import socket
import secrets


class ChatClient:
    def __init__(
        self,
        name="",
        address=None,
        token=secrets.token_bytes(16),
        is_host=False,
    ):
        self.name = name
        self.address = address
        self.is_host = is_host
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.room_name = ""

    # メッセージを送信する関数
    def send_message(self, message):
        # メッセージを送信
        self.udp_socket.sendto(message.encode("utf-8"), self.client_address)
