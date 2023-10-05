import socket
import secrets


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
<<<<<<< HEAD
        # トークンをrandomで生成する関数
        self.token = secrets.token_bytes(255)
        self.is_host = False
||||||| 97f049f
        self.token = ""
        self.is_host = False
        self.address = ("", 0)
=======
        self.token = token
        self.is_host = is_host
>>>>>>> c7d32c65ed5014789473d49ddb0ee8468ef39c4c
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.room_name = ""

    # メッセージを送信する関数
    def send_message(self, message):
        # メッセージを送信
        self.udp_socket.sendto(message.encode("utf-8"), self.client_address)
