#from .websockethandler import WebSocketHandler, websocket
from .websockethandler_asyncio import WebSocketHandler
import threading
from base64 import standard_b64decode
import asyncio

class ProtocolHandler(WebSocketHandler):
    """Handles Send and Receive Events in the ISAAC Protocol

    Comment Axel: This is done via the kernel, so expect the most indirect way to get your
    image (but also the most reliable in case you are tunneling your notebook).
    """
    def __init__(self, ip: str ="127.0.0.1", port: int=2459, verbose: bool=False):
        """..."""
        self.verbose = verbose
        self.ip = ip
        self.port = port
        self.observe_id = -1
        # TODO: use default image from webclient
        self.latest_image = b''
        self.last_step = -1
        # TODO: make setter
        self.response_handler = None

    # old thread based version, currently unused
    def run_async(self):
        self.wsh = WebSocketHandler(self.message_handler, self.ip, self.port)
        self.wsh_thread = threading.Thread(target=self.wsh.run_forever)
        self.wsh_thread.start()

    # newer asyncio version
    async def run_async_io(self):
        """Create WebSocketHandler object, connect and put receiver into
        background task.
        """
        self.wsh = WebSocketHandler(self.message_handler, self.ip, self.port)
        await self.wsh.connect()
        loop = asyncio.get_running_loop()
        self._listen_task = loop.create_task(self.wsh.run_forever())

    async def message_handler(self, payload):
        """Handles incomming messages"""
        if payload["type"] == "hello":
            self.hello_handler(payload)
        if payload["type"] == "register":
            self.register_handler(payload)
        if payload["type"] == "period":
            await self.period_handler(payload)
        if payload["type"] == "exit":
            self.exit_handler(payload)

    def hello_handler(self, payload):
        """Response on connect to server: lists connected visualizations"""
        print("\nHello received:")
        print(f"  Server name: {payload["name"]}")
        print("  Available streams:")
        for stream in payload["streams"]:
            print(f"    {stream["name"]} (ID: {stream["id"]})")

    def register_handler(self, payload):
        """A new visualization registered at the server"""
        print("\nRegister received:")
        print(f"  Visualization ID: {payload["id"]}")
        # TODO check protocol match
        protocol = payload["protocol"]
        print(f"  Protocol version: {protocol[0]}.{protocol[1]}")
        print("  Sources:")
        for source in payload["sources"]:
            print(f"    {source["name"]} ({source["feature dimension"]}D)")

    async def period_handler(self, payload):
        """Handle new iterations from visualization"""
        if self.verbose:
            print(f"Period received:\n{payload}\n")
        # Store last received time step of sim
        if "time step" in payload["metadata"]:
            self.last_step = payload["metadata"]["time step"]
            # respond handler can be used to send feedback upon receiving messages
            # which uses the last received time step
            if self.response_handler != None:
                response = self.response_handler(self.last_step)
                #print("send response")
                await self.send_feedback(response)

        # process incoming images
        if "payload" in payload:
            #image_base64 = payload["payload"]
            #image_jpg = self.image_decoder(image_base64)
            #self.latest_image = image_base64
            ...

    def exit_handler(self, payload):
        """A visualization exited!"""
        print(f"\nExit received from visualization {payload["id"]}!")
        if payload["id"] == self.observe_id:
            self.observe_id = -1

    async def send_observe(self, observe_id: int, stream: int=0, dropable: bool=False):
        """Register to receive 'period' messages from a visualization

        Parameters
        ----------
        observe_id: unsigned integer
            The id of the visualization to observe.
        stream: unsigned integer
            Number of the stream to get (JPEG, RDP,...).
        dropable: bool
            If True: it is okay to drop 'period' updates on slow connections.
        """
        # Currently, only one visualisation can be observed at a time
        # TODO: check, if the id is actually registered
        # TODO: Should I support multiple observes?!
        if self.observe_id > -1:
            print("Already observing a visualization. Please call `send_stop()` fist!")
        else:
            print("Sending observe!")
            self.observe_id = observe_id
            d = {
                'type': 'observe',
                'observe id': self.observe_id,
                'stream': stream,
                'dropable': dropable
            }
            await self.wsh.send_message(d)

    async def send_feedback(self, args: dict[str]):
        """adjust variables of the visualization"""
        # TODO: maybe make 'observe id' overwritable
        d = {
            'type': 'feedback',
            'observe id': self.observe_id
        }
        # changes and adds keys to dictionary
        d.update(args)
        await self.wsh.send_message(d)
        if self.verbose:
            print(f"Feedback sent:\n{d}\n")


    async def send_stop(self):
        """disconnect from a visualization: stop getting 'period' messages from it"""
        # return, if no visualization is observered
        if self.observe_id < 0:
            print("Currently not observing any visualization")
        else:
            d = {
                'type': 'stop',
                'observe id': self.observe_id
            }
            await self.wsh.send_message(d)
            print(f"Stop receiving updates from visualization {self.observe_id}")
            # reset observation id
            self.observe_id = -1

    async def send_closed(self):
        """disconnect from the isaac server"""
        print("Disconnecting from server!")
        d = {
            'type': 'closed'
        }
        await self.wsh.send_message(d)
        # do i need to call self.wsh.ws.close() or would that be redundant?

    # currently unused
    @staticmethod
    def image_decoder(payload):
        """
        Decode image from base64 back to binary jpeg
        """
        image_base64 = payload
        # throw away base64 prefix
        prefix = "data:image/jpeg;base64,"
        image_base64 = image_base64[len(prefix):]
        # fix missing padding
        missing_padding = len(image_base64) % 4
        if missing_padding != 0:
            image_base64 += '='* (4 - missing_padding)
        
        image_binary = standard_b64decode(image_base64)
        return image_binary
