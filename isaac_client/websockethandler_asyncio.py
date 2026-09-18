#import websocket
import websockets.asyncio.client as websocket
import json

class WebSocketHandler:
    """Handles the low level websocket protocol to ISAAC server"""

    def __init__(self, msg_handler=None, ip="127.0.0.1", port: int=2459):
        """connect to an ISAAC server service"""
        self.uri = f'ws://{ip}:{port}'
        self.msg_handler = msg_handler
        self.ws = None

    async def connect(self):
        self.ws = await websocket.connect(
            self.uri,
            subprotocols=['isaac-json-protocol'],
            compression=None,
        )
        
    async def run_forever(self):
        print("WebSocketHandler: Start run!")
        async for message in self.ws:
            await self.on_message(message)

    async def on_message(self, message):
        #print("WebSocketHandler: Message Handler")

        # this is potentially dangerous
        d = json.loads(message)

        if self.msg_handler is not None:
            self.msg_handler(d)
        else:
            print("WebSocketHandler: No message handler registered!")

    @staticmethod
    def on_error(ws, error):
        print(f"Error:\n{error}")

    @staticmethod
    def on_close(ws, status_code, msg):
        print("WebSocketHandler: closed")
        if msg != None:
            print(msg)

    @staticmethod
    def on_open(ws):
        pass

    async def send_message(self, args):
        json_args = json.dumps(args)
        #print("WebSocketHandler: Send")
        #print(json_args)
        await self.ws.send(json_args)

