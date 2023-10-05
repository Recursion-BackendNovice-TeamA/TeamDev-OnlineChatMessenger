import socket
import json
import struct
import threading


# ChatClientクラスを定義
class Client:
    def __init__(self, name):
        self.name = name
        self.tcp_address = ("0.0.0.0", 9002)
        self.udp_address = ("0.0.0.0", 9003)
        self.token = ""
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(('0.0.0.0', 0))
        self.address = self.udp_socket.getsockname()

        #クライアントが入力したアクション番号
        self.CREATE_ROOM_NUM = 1
        self.JOIN_ROOM_NUM = 2
        self.QUIT_NUM = 3
        
        # クライアントがサーバーに送信するヘッダー(UDP)
        self.room_name_size = 0
        self.token_size = 0
        

    def start(self):
        """クライアントを起動する関数"""

        # ユーザーがアクション(1:部屋作成, 2:参加, 3:終了)を選択
        operation = self.__input_action_number()
        self.tcp_connect(int(operation))

    def tcp_connect(self, operation):
        """サーバーにTCP接続

        Args:
            operation (int): クライアントが入力したアクション番号(1:部屋作成, 2:参加, 3:終了)
        """

        if operation == self.CREATE_ROOM_NUM or operation == self.JOIN_ROOM_NUM:
            self.tcp_socket.connect(self.tcp_address)
            # 入室リクエストを送信・レスポンス待機
            self.tcp_request(operation)
        elif operation == self.QUIT_NUM:
            print("Closing connection...")
            self.tcp_socket.close()
            print("Connection closed.")
            exit()

    def tcp_request(self, operation):
        """部屋入室リクエストの関数（部屋作成・部屋参加共通）

        Args:
            operation (int): クライアントが入力したアクション番号(1:部屋作成, 2:参加)
        """
        # 部屋名を入力
        room_name = self.__input_room_name()
        encoded_room_name = room_name.encode("utf-8")

        payload = {
            "user_name": self.name,
            "address": self.address,
        }

        payload_data = json.dumps(payload).encode("utf-8")

        # ヘッダーを作成(state = 0)
        header = struct.pack(
            "!B B B 29s",
            len(encoded_room_name),
            operation,
            0,
            len(payload_data).to_bytes(29, byteorder="big"),
        )

        # ボディを作成
        # Todo OperationPayloadSizeの最大バイト数を超えた場合の例外処理
        body = encoded_room_name + payload_data

        # ヘッダーとボディをサーバーに送信
        req = header + body
        self.tcp_socket.sendall(req)
        print(f"request: {req}")

        # サーバーから新しいレスポンスを受信(state = 1: リクエスト受理)
        header = self.tcp_socket.recv(32)
        payload_size = int.from_bytes(header[3:], byteorder="big")
        payload = self.tcp_socket.recv(payload_size)

        # サーバーから新しいレスポンスを受信(state = 2: リクエストの完了)
        header = self.tcp_socket.recv(32)
        payload_size = int.from_bytes(header[3:], byteorder="big")
        payload = self.tcp_socket.recv(payload_size)

        # 新しいヘッダーからstateを取得
        state = header[2]
        if state == 0:
            print(json.loads(payload.decode("utf-8"))["message"])
            self.tcp_socket.close()
            self.start()
        else:
            # トークンを取得
            if self.token == "":
                token = json.loads(payload.decode("utf-8"))["token"]
                self.token = token
                print("トークン: {}".format(token))

            self.tcp_socket.close()
            # UDPソケットをバインド
            # self.udp_socket.bind(("", 0))

        # 他クライアントからのメッセージを別スレッドで受信
        threading.Thread(target=self.receive_message).start()

        # メッセージを送信
        threading.Thread(target=self.send_message).start()

    def __input_action_number(self):
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


    def __input_room_name(self):
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


if __name__ == "__main__":
    print("---WELCOME TO THE CHAT MESSENGER PROGRAM!---")
    client = Client(input("Enter your username: "))
    client.start()
