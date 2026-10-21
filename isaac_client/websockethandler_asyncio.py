#import websocket
import websockets.asyncio.client as websocket
import json

class WebSocketHandler:
    """Handles the low level websocket protocol to ISAAC server"""

    def __init__(self, msg_handler=None, ip="127.0.0.1", port: int=2459):
        self.uri = f'ws://{ip}:{port}'
        self.msg_handler = msg_handler
        self.ws = None

    async def connect(self):
        """connect to an ISAAC server service"""
        self.ws = await websocket.connect(
            self.uri,
            subprotocols=['isaac-json-protocol'],
            compression=None,
        )
        
    async def run_forever(self):
        """Listen to messages"""
        print("WebSocketHandler: Start run!")
        async for message in self.ws:
            await self.on_message(message)

    async def on_message(self, message):
        """Handle incoming messages by giving them to message handler"""
        #print("WebSocketHandler: Message Handler")

        # convert json to dict
        # this is potentially dangerous
        d = json.loads(message)

        if self.msg_handler is not None:
            await self.msg_handler(d)
        else:
            print("WebSocketHandler: No message handler registered!")

    # unused
    @staticmethod
    def on_error(ws, error):
        print(f"Error:\n{error}")

    # unused
    @staticmethod
    def on_close(ws, status_code, msg):
        print("WebSocketHandler: closed")
        if msg != None:
            print(msg)

    async def send_message(self, args):
        """Send messages to server"""
        # convert dict to json
        json_args = json.dumps(args)
        await self.ws.send(json_args)

