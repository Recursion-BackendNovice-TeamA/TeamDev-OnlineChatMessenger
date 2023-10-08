import socket
import json
import struct
import threading

from user import User


# ChatClientクラスを定義
class Client:
    def __init__(self):
        self.__tcp_address = ("127.0.0.1", 9002)
        self.__tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # クライアントが入力したアクション番号
        self.__CREATE_ROOM_NUM = 1
        self.__JOIN_ROOM_NUM = 2
        self.__QUIT_NUM = 3

        self.__SERVER_INIT = 0
        self.__RESPONSE_OF_REQUEST = 1
        self.__REQUEST_COMPLETION = 2
        self.__ERROR_RESPONSE = 3

    def start(self):
        """クライアントを起動する関数"""
        # ユーザー名入力
        user_name = self.__input_user_name()
        user = User(user_name)
        # ユーザーがアクション(1:部屋作成, 2:部屋参加, 3:終了)を選択
        operation = user.input_action_number()
        # TCP接続するかどうか
        tcp_connected = self.__check_tcp_connection(int(operation))
        if not tcp_connected:
            print("Closing connection...")
            self.__tcp_socket.close()
            print("Connection closed.")
            exit()

        # 部屋名を入力
        room_name = user.input_room_name()
        # 入室リクエストを送信
        self.__request_to_join_room(operation, user, room_name)
        # 入室リクエストのレスポンスを受け取る
        token = self.__receive_response_to_join_room()
        # ユーザーにトークンを付与
        user.token = token
        # 参加した部屋名をセット
        user.room_name = room_name
        # TCP接続を閉じる
        self.__tcp_socket.close()

        # 他クライアントからのメッセージを別スレッドで受信
        threading.Thread(target=user.receive_message).start()
        # メッセージを送信
        threading.Thread(target=user.send_message).start()

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

    def __check_tcp_connection(self, operation):
        """TCP接続の確認

        Args:
            operation (int): クライアントが入力したアクション番号(1:部屋作成, 2:参加, 3:終了)

        Returns:
            (bool): TCP接続できたかどうか
        """
        tcp_connected = False
        if operation == self.__CREATE_ROOM_NUM or operation == self.__JOIN_ROOM_NUM:
            self.__tcp_socket.connect(self.__tcp_address)
            tcp_connected = True

        return tcp_connected

    def __request_to_join_room(self, operation, user, room_name):
        """部屋入室リクエストの関数（部屋作成・部屋参加共通）

        Args:
            operation (str): クライアントが入力したアクション番号(1:部屋作成, 2:参加)
            user (user.User): ユーザー
            room_name (str): 部屋名
        """

        encoded_room_name = room_name.encode("utf-8")
        payload = {
            "user_name": user.name,
            "user_address": user.address,
        }
        payload_data = json.dumps(payload).encode("utf-8")
        # ヘッダーを作成
        header = struct.pack(
            "!B B B 29s",
            len(encoded_room_name),
            int(operation),
            self.__SERVER_INIT,
            len(payload_data).to_bytes(29, byteorder="big"),
        )
        # ボディを作成
        # Todo OperationPayloadSizeの最大バイト数を超えた場合の例外処理
        body = encoded_room_name + payload_data

        # ヘッダーとボディをサーバーに送信
        req = header + body
        self.__tcp_socket.sendall(req)

    def __receive_response_to_join_room(self):
        """部屋入室リクエストのレスポンスを受け取る

        Returns:
            (str): トークン
        """
        header = self.__tcp_socket.recv(32)
        _, _, state, payload_size = struct.unpack_from("!B B B 29s", header)
        operation_payload_size = int.from_bytes(payload_size, byteorder="big")
        payload = self.__tcp_socket.recv(operation_payload_size)

        if state == self.__SERVER_INIT:
            print(json.loads(payload.decode("utf-8"))["message"])
            self.__tcp_socket.close()
            self.start()
        elif state == self.__RESPONSE_OF_REQUEST:
            # リクエストの受理をするため
            print(json.loads(payload.decode("utf-8"))["message"])
            return self.__receive_response_to_join_room
        elif state == self.__REQUEST_COMPLETION:
            # トークンを取得
            token = json.loads(payload.decode("utf-8"))["token"]
            message = json.loads(payload.decode("utf-8"))["message"]
            print(message)
            return token

    def recvall_TCRP(self, header):
        """TCRPのデータを受取をする関数

        Args:
            header (32Bytes): クライアントから送信されたヘッダー
        """
        room_name_size, operation, state, payload_size = struct.unpack_from(
            "!B B B 29s", header
        )
        MSGLEN = {
            int.from_bytes(room_name_size)
            + len(operation)
            + len(state)
            + int.from_bytes(payload_size)
        }
        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            chunk = self.__tcp_socket.recv(min(MSGLEN - bytes_recd, 4096))
            if chunk == b"":
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b"".join(chunks)


if __name__ == "__main__":
    print("---WELCOME TO THE CHAT MESSENGER PROGRAM!---")
    client = Client()
    client.start()
