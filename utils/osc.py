from pythonosc.udp_client import SimpleUDPClient
from utils.logger import Logger

Log = Logger(__name__)

class OSC:
    def __init__(self, ip: str = "127.0.0.1", port: int = 9000):
        self.client = SimpleUDPClient(ip, port)
    
    def send_chatbox(self, message: str):
        self.client.send_message("/chatbox/input", [message, True])
        Log.debug(f"Send message: {message}")
    
    def send_typing(self, typing: bool):
        self.client.send_message("/chatbox/typing", typing)
        Log.debug(f"Send typing: {typing}")