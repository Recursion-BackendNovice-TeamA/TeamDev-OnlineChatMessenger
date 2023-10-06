import socket
import struct


class User:
    def __init__(
        self, 
        name="",
        address=None,
        token= "",
        is_host=False,
    ):
        self.name = name
        self.address = address
        self.token = token
        self.is_host = is_host
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_address = ("0.0.0.0", 9003)
        self.udp_socket.bind(('0.0.0.0', 0))
        self.address = self.udp_socket.getsockname()
        self.room_name = ""

    # メッセージを送信する関数
    def send_message(self, message):
        # メッセージを送信
        self.udp_socket.sendto(message.encode("utf-8"), self.client_address)


    def input_action_number(self):
        """ユーザー入力後にアクションを選ばせる(部屋作成・参加・終了)

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
        """クライアントが部屋名を入力
        
        Returns:
            (str): 部屋名
        """
        while True:
            ROOM_NAME_MAX_BYTE_SIZE = 255
            self.room_name = input("Enter room name: ")
            self.room_name_size = len(self.room_name.encode('utf-8'))
            if self.room_name_size > ROOM_NAME_MAX_BYTE_SIZE:
                print(f"Room name bytes: {self.room_name_size} is too large.")
                print(f"Please retype the room name with less than {ROOM_NAME_MAX_BYTE_SIZE} bytes")
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
            # Todo ヘッダーにRoomNameSizeとTokenSizeを持たせる
            # header = struct.pack("!B B", self.room_name_size, self.token_size)
            header = struct.pack("!B", self.room_name_size)

            input_message = input("")

            if input_message == "exit":
                print("Closing connection...")
                self.udp_socket.close()
                print("Connection closed.")
                exit()

            # Todo bodyにトークンを持たせる
            # body = self.room_name + self.token + input_message
            body = self.room_name + input_message
            encoded_body = body.encode('utf-8')

            message = header + encoded_body

            # メッセージを送信
            # Todo メッセージのバイトサイズを超えた際の例外処理
            self.udp_socket.sendto(message, self.udp_address)

    # メッセージを受信する関数
    def receive_message(self):
        while True:
            # メッセージを受信
            data, _ = self.udp_socket.recvfrom(4096)
            decoded_data = data.decode("utf-8")
            print(f"{decoded_data}")