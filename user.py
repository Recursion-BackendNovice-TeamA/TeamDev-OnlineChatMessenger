import socket
import struct


class User:
    def __init__(self, name):
        """Userクラスインスタンス化

        Args:
            name (str): ユーザー名

         Note:
             UDPソケットをアドレスとポート番号にバインドする際に、ポート番号に0を渡すことで
             OSが利用可能なランダムなポートを選び、それ利用することができる。
        """
        self.__RANDOM_PORT_NUM = 0
        self.__udp_server_address = ("127.0.0.1", 9003)
        self.__udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__udp_socket.bind(("127.0.0.1", self.__RANDOM_PORT_NUM))
        self.name = name
        self.token = ""
        self.room_name = ""
        self.is_host = False
        self.address = self.__udp_socket.getsockname()

    def input_action_number(self):
        """アクション番号の入力

        Note:
            1: 新しく部屋を作成
            2: 既存の部屋に入室
            3: 入力操作をやめる

        Returns:
            (str): 入力番号(1、2、3のいずれか)
        """
        print("Please enter 1, 2 or 3")
        operation = input(
            "1. Create a new room\n2. Join an existing room\n3. Quit\nChoose an option: "
        )
        return operation

    def input_room_name(self):
        """部屋名の入力

        Returns:
            (str): 部屋名
        """
        while True:
            ROOM_NAME_MAX_BYTE_SIZE = 255
            self.room_name = input("Enter room name: ")
            if self.room_name == "":
                continue
            room_name_size = len(self.room_name.encode("utf-8"))
            if room_name_size > ROOM_NAME_MAX_BYTE_SIZE:
                print(f"Room name bytes: {room_name_size} is too large.")
                print(
                    f"Please retype the room name with less than {ROOM_NAME_MAX_BYTE_SIZE} bytes"
                )
                continue
            return self.room_name

    def send_message(self):
        """メッセージを送信する関数

        Note:
            メッセージを送信する際にクライアントが入室している部屋名も一緒に渡して
            どの部屋の他のクライアントにメッセージを送信するか判断する
        """

        # メッセージを入力させる
        while True:
            header = struct.pack(
                "!B B",
                len(self.room_name.encode("utf-8")),
                len(self.token.encode("utf-8")),
            )

            input_message = input("")

            if input_message == "exit":
                print("Closing connection...")
                self.__udp_socket.close()
                print("Connection closed.")
                exit()

            body = self.room_name + self.token + input_message
            encoded_body = body.encode("utf-8")

            message = header + encoded_body

            # メッセージを送信
            # Todo メッセージのバイトサイズを超えた際の例外処理
            self.__udp_socket.sendto(message, self.__udp_server_address)

    def receive_message(self):
        """メッセージの受信"""
        while True:
            # メッセージを受信
            data, _ = self.__udp_socket.recvfrom(4096)
            decoded_data = data.decode("utf-8")
            print(f"{decoded_data}")
