from src.utils.logger import Logger

import socket

Log = Logger(__name__)

class SimpleOSCClient:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.addr = (self.ip, self.port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def to_osc_str(self, s: str) -> bytes:
        b = s.encode("utf-8") + b'\x00'
        padding_size = (4 - (len(b) % 4)) % 4
        return b + (b'\x00' * padding_size)
    
    def build_osc_msg(self, address: str, args: list) -> bytes:
        packet = self.to_osc_str(address)
        
        tags = ","
        arg_bytes = b""
        
        for arg in args:
            arg_type_str = type(arg).__name__
            
            match arg_type_str:
                case "str":
                    tags += "s"
                    arg_bytes += self.to_osc_str(arg)
                case "bool":
                    tags += "T" if arg else "F"
        
        packet += self.to_osc_str(tags)
        packet += arg_bytes
        
        return packet
    
    def send(self, address: str, args: list):
        self.sock.sendto(self.build_osc_msg(address, args), self.addr)

class OSC:
    def __init__(self, ip: str = "127.0.0.1", port: int = 9000):
        self.client = SimpleOSCClient(ip, port)
    
    def send_chatbox(self, message: str):
        self.client.send("/chatbox/input", [message, True])
        Log.debug(f"Send message: {message}")
    
    def send_typing(self, typing: bool):
        self.client.send("/chatbox/typing", [typing])
        Log.debug(f"Send typing: {typing}")