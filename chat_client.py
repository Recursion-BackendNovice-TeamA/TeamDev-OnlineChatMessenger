import socket


class ChatClient:
    def __init__(
        self, 
        name="",
        udp_addr=None,
        tcp_addr=None,
        token="",
        is_host=False,
    ):
        self.name = name
        self.tcp_addr = tcp_addr
        self.udp_addr = udp_addr
        self.token = token
        self.is_host = is_host
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # メッセージを送信する関数
    def send_message(self, message):
        # メッセージを送信
        self.udp_socket.sendto(message.encode("utf-8"), self.client_address)
