import socket


class ChatClient:
    def __init__(
        self, 
        name="",
        address=None,
        token="",
        is_host=False,
    ):
        self.name = name
        self.address = address
        self.token = token
        self.is_host = is_host
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # メッセージを送信する関数
    def send_message(self, message):
        # メッセージを送信
        self.udp_socket.sendto(message.encode("utf-8"), self.client_address)
