import socket
import secrets


class ChatClient:
    def __init__(self, name, address):
        self.name = name
        self.address = address
        # トークンをrandomで生成する関数
        self.token = secrets.token_bytes(255)
        self.is_host = False
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # メッセージを送信する関数
    def send_message(self, message):
        # メッセージを送信
        self.udp_socket.sendto(message.encode("utf-8"), self.client_address)
