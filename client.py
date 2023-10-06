import socket
import json
import struct
import threading

from user import User


# ChatClientクラスを定義
class Client:
    def __init__(self):
        # self.name = ""
        self.tcp_address = ("0.0.0.0", 9002)
        self.udp_address = ("0.0.0.0", 9003)
        self.token = ""
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(("0.0.0.0", 0))
        self.address = self.udp_socket.getsockname()

        # クライアントが入力したアクション番号
        self.CREATE_ROOM_NUM = 1
        self.JOIN_ROOM_NUM = 2
        self.QUIT_NUM = 3

        # クライアントがサーバーに送信するヘッダー(UDP)
        self.room_name_size = 0
        self.token_size = 0

        self.SERVER_INIT = 0
        self.RESPONSE_OF_REQUEST = 1
        self.REQUEST_COMPLETION = 2
        self.ERROR_RESPONSE = 3

    def start(self):
        """クライアントを起動する関数"""

        # ユーザー名入力
        user_name = self.__input_user_name()
        user = User(user_name)

        # ユーザーがアクション(1:部屋作成, 2:部屋参加, 3:終了)を選択
        operation = user.input_action_number()
        # TCP接続できたかどうか
        tcp_connected = self.__is_tcp_connected(int(operation))
        if not tcp_connected:
            print("Closing connection...")
            self.tcp_socket.close()
            print("Connection closed.")
            exit()

        # 入室リクエストを送信・レスポンス待機
        self.__request_to_join_room(operation, user)

    def __input_user_name(self):
        """ユーザー名入力

        Returns:
            (str): ユーザー名
        """
        while True:
            USER_NAME_MAX_BYTE_SIZE = 255
            user_name = input("Enter your username: ")
            if user_name == "":
                continue
            user_name_size = len(user_name.encode("utf-8"))
            if user_name_size > USER_NAME_MAX_BYTE_SIZE:
                print(f"User name bytes: {user_name_size} is too large.")
                print(
                    f"Please retype the room name with less than {USER_NAME_MAX_BYTE_SIZE} bytes"
                )
                continue
            return user_name

    def __is_tcp_connected(self, operation):
        """TCP接続できたかどうかの判定

        Args:
            operation (int): クライアントが入力したアクション番号(1:部屋作成, 2:参加, 3:終了)

        Returns:
            (bool): TCP接続できたかどうか
        """
        tcp_connected = False
        if operation == self.CREATE_ROOM_NUM or operation == self.JOIN_ROOM_NUM:
            self.tcp_socket.connect(self.tcp_address)
            tcp_connected = True

        return tcp_connected

    def __request_to_join_room(self, operation, user):
        """部屋入室リクエストの関数（部屋作成・部屋参加共通）

        Args:
            operation (str): クライアントが入力したアクション番号(1:部屋作成, 2:参加)
        """
        # 部屋名を入力
        room_name = user.input_room_name()
        encoded_room_name = room_name.encode("utf-8")

        payload = {
            "user_name": user.name,
            "user_address": user.address,
        }

        payload_data = json.dumps(payload).encode("utf-8")

        # ヘッダーを作成(state = 0)
        header = struct.pack(
            "!B B B 29s",
            len(encoded_room_name),
            int(operation),
            self.SERVER_INIT,
            len(payload_data).to_bytes(29, byteorder="big"),
        )

        # ボディを作成
        # Todo OperationPayloadSizeの最大バイト数を超えた場合の例外処理
        body = encoded_room_name + payload_data

        # ヘッダーとボディをサーバーに送信
        req = header + body
        self.tcp_socket.sendall(req)

        # サーバーから新しいレスポンスを受信(state = 1: リクエスト受理)
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
            if user.token == "":
                token = json.loads(payload.decode("utf-8"))["token"]
                user.token = token
                print("トークン: {}".format(token))

            self.tcp_socket.close()

        # 他クライアントからのメッセージを別スレッドで受信
        threading.Thread(target=user.receive_message).start()

        # メッセージを送信
        threading.Thread(target=user.send_message).start()


if __name__ == "__main__":
    print("---WELCOME TO THE CHAT MESSENGER PROGRAM!---")
    client = Client()
    client.start()
