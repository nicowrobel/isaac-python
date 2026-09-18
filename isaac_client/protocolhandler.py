#from .websockethandler import WebSocketHandler, websocket
from .websockethandler_asyncio import WebSocketHandler
import threading
from base64 import standard_b64decode
import asyncio

class ProtocolHandler(WebSocketHandler):
    """Handles Send and Receive Events in the ISAAC Protocol

    This is done via the kernel, so expect the most indirect way to get your
    image (but also the most reliable in case you are tunneling your notebook).
    """
    def __init__(self, enable_trace=False):
        """..."""
        # this should be made implementation agnostic, in case I switch to
        # websockets
        # TODO: set ip and port and forward it to WebSocketHandler
        #websocket.enableTrace(enable_trace)
        self.observe_id = -1
        # TODO: use default image from webclient
        self.latest_image = b''
        
    def run_async(self):
        self.wsh = WebSocketHandler(self.message_handler, "10.1.24.7", 2459)
        self.wsh_thread = threading.Thread(target=self.wsh.run_forever)
        self.wsh_thread.start()

    async def run_asyncio(self):
        self.wsh = WebSocketHandler(self.message_handler, "10.1.24.7", 2459)
        await self.wsh.connect()
        loop = asyncio.get_running_loop()
        self._listen_task = loop.create_task(self.wsh.run_forever())

    def message_handler(self, args):
        #print("ISAAC Message Handler")

        if args["type"] == "hello":
            self.hello_handler(args)
        if args["type"] == "register":
            self.register_handler(args)
        if args["type"] == "period":
            self.period_handler(args)
        if args["type"] == "exit":
            self.exit_handler(args)

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

    def period_handler(self, payload):
        """A new iteration from the visualization arrived!"""
        #print(f"Period received: {payload["meta nr"]}")
        if "payload" in payload:
            image_base64 = payload["payload"]
            #image_jpg = self.image_decoder(image_base64)
            self.latest_image = image_base64

    def exit_handler(self, payload):
        """A visualization exited!"""
        print(f"\nExit received from visualization {payload["id"]}!")

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
        print("Sending observe!")
        # TODO: What happens, when I send multiple observes?!
        self.observe_id = observe_id
        d = {
            'type': 'observe',
            'observe id': self.observe_id,
            'stream': stream,
            'dropable': dropable
        }
        await self.wsh.send_message(d)

    def send_feedback(self, args):
        """adjust variables of the visualization"""
        #print("Send feedback to visualization!")
        d = {
            'type': 'feedback'
        }
        # changes and adds keys to dictionary
        d.update(args)
        self.wsh.send_message(d)

    def send_stop(self):
        """disconnect from a visualization: stop getting 'period' messages from it"""
        # return, if no visualization is observered
        if self.observe_id < 0:
            print("Currently not observing any visualization")
            return
        print(f"Stop receiving updates from visualization {self.observe_id}")
        d = {
            'type': 'stop',
            'observe id': self.observe_id
        }
        self.wsh.send_message(d)
        # reset observation id
        self.observe_id = -1

    def send_closed(self):
        """disconnect from the isaac server"""
        #print("Disconnecting from server!")
        d = {
            'type': 'closed'
        }
        self.wsh.send_message(d)

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
