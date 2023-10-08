import socket
import json
import secrets
import struct
import threading
from concurrent.futures import ThreadPoolExecutor

from chat_room import ChatRoom


class Server:
    def __init__(self):
        self.tcp_address = ("127.0.0.1", 9002)
        self.udp_address = ("127.0.0.1", 9003)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_socket.bind(self.tcp_address)
        self.udp_socket.bind(self.udp_address)
        # room_name: ChatRoom インスタンスの辞書
        self.rooms = {}
        self.HEADER_BYTE_SIZE = 32

        # クライアントが入力したアクション番号
        self.CREATE_ROOM_NUM = 1
        self.JOIN_ROOM_NUM = 2
        self.QUIT_NUM = 3

        self.SERVER_INIT = 0
        self.RESPONSE_OF_REQUEST = 1
        self.REQUEST_COMPLETION = 2
        self.ERROR_RESPONSE = 3

    # サーバー起動の関数
    def start(self):
        print("Server Started on port", 9002)

        while True:
            try:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    executor.submit(self.wait_for_tcp_conn)
                    executor.submit(self.receive_message)

            except KeyboardInterrupt:
                print("Keyboard Interrupted")
                self.tcp_socket.close()
                self.udp_socket.close()
                print("\nServer Closed")
                break

    def wait_for_tcp_conn(self):
        """クライアントからのTCP接続を待機する関数"""
        while True:
            self.tcp_socket.listen(5)
            conn, _ = self.tcp_socket.accept()
            # クライアントからのTCP接続を処理(並列処理)
            threading.Thread(target=self.__handle_tcp_conn, args=(conn,)).start()

    def __handle_tcp_conn(self, conn):
        """クライアントからのTCP接続を処理する関数

        Args:
            conn (socket.socket): 接続されたクライアントのソケットオブジェクト
        """
        try:
            # クライアントからのデータを受信
            header = conn.recv(self.HEADER_BYTE_SIZE)
            room_name_size, operation, _, _ = struct.unpack_from("!B B B 29s", header)
            body = conn.recv(4096)

            room_name = body[:room_name_size].decode("utf-8")
            payload_data = body[room_name_size:].decode("utf-8")

            # payloadはjson形式の文字列とする
            # payloadをloadsして辞書に変換
            payload = json.loads(payload_data)
            user_name = payload["user_name"]
            user_address = payload["user_address"]
        except Exception as e:
            print(e)
            server.tcp_socket.close()
            server.udp_socket.close()
            exit()

        # operation = 1 ... 部屋作成
        if operation == self.CREATE_ROOM_NUM:
            self.create_room(room_name, conn, user_address, user_name)

        # operation = 2 ... 部屋参加
        if operation == self.JOIN_ROOM_NUM:
            self.assign_room(room_name, conn, user_address, user_name)

    def create_room(self, room_name, conn, user_address, user_name):
        """部屋を作成する関数

        Args:
            room_name (str): チャットルーム名
            conn (socket.socket): 接続されたクライアントのソケットオブジェクト
            user_address (tuple): クライアントのアドレス（IPアドレスとポート番号)
            user_name (str): ユーザー名
        """
        # クライアントに新しいヘッダーを送信(state = 1)
        # self.send_state_res(conn, room_name, self.CREATE_ROOM_NUM, self.RESPONSE_OF_REQUEST, "")
        # キーとして部屋名が部屋リストに存在しない場合
        if room_name not in self.rooms:
            # 部屋を作成
            new_room = ChatRoom(room_name)
            self.rooms[room_name] = new_room
            print(f"{user_name}が{room_name}を作成しました。")

            # クライアントにトークンを発行
            token = self.__generate_token()
            # ホストトークン設定
            new_room.host_token = token
            # client.token = token

            # 部屋にユーザーを追加
            new_room.add_client(token, user_address, user_name)

            # クライアントをホストに設定
            # client.is_host = True
            # 作成して参加した部屋名
            # client.room_name = room_name

            # クライアントに新しいヘッダーを送信(state = 2)
            self.send_state_res(conn, room_name, 1, 2, token)
        else:
            self.send_state_res(conn, room_name, 1, 0, "")

    def assign_room(self, room_name, conn, user_address, user_name):
        """クライアントを部屋に参加させる関数

        Args:
            room_name (str): チャットルーム名
            conn (socket.socket): 接続されたクライアントのソケットオブジェクト
            user_address (tuple): クライアントのアドレス（IPアドレスとポート番号)
            user_name (str): ユーザー名

        Todo:
            同姓同名の人物がいる場合の処理
        """
        # クライアントに新しいヘッダーを送信(state = 1)
        # self.send_state_res(conn, room_name, 2, 1, "")
        # 部屋が存在する場合
        if room_name in self.rooms:
            room = self.rooms[room_name]

            # クライアントにトークンを発行
            token = self.__generate_token()
            # client.token = token
            # 部屋にユーザーを追加
            room.add_client(token, user_address, user_name)
            print(f"{user_name}が{room_name}に参加しました。")

            # クライアントに新しいヘッダーを送信(state = 2)
            self.send_state_res(conn, room_name, 2, 2, token)
        else:
            self.send_state_res(conn, room_name, 2, 0, "")

    # トークンをrandomで生成する関数
    def __generate_token(self):
        token = secrets.token_hex(32)
        # token = secrets.token_hex(16)
        return token

    # リクエストの状態に応じてヘッダーとペイロードを送信する関数
    def send_state_res(self, conn, room_name, operation, state, token):
        """_summary_

        Args:
            conn (_type_): _description_
            room_name (_type_): _description_
            operation (_type_): _description_
            state (_type_): _description_
            token (_type_): _description_
        """
        if state == self.SERVER_INIT:
            payload_data = (
                {"status": 400, "message": "部屋 {} はすでに存在します".format(room_name)}
                if operation == 1
                else {"status": 404, "message": "部屋 {} は存在しません".format(room_name)}
            )
        elif state == self.RESPONSE_OF_REQUEST:
            payload_data = {"status": 200, "message": "リクエストを受理しました。"}
        else:
            payload_data = {"status": 202, "message": "リクエストを完了しました。", "token": token}

        res_payload = json.dumps(payload_data).encode("utf-8")

        header = struct.pack(
            "!B B B 29s",
            len(room_name),
            operation,
            state,
            len(res_payload).to_bytes(29, byteorder="big"),
        )

        conn.sendall(header + res_payload)

    def receive_message(self):
        """クライアントからのUDP接続経由でメッセージを受信する関数"""
        HEADER_SIZE = 2

        while True:
            data, _ = self.udp_socket.recvfrom(4096)

            room_name_size, token_size = struct.unpack_from("!B B", data[:2])
            room_name = data[HEADER_SIZE : HEADER_SIZE + room_name_size].decode("utf-8")
            token = data[
                HEADER_SIZE + room_name_size : HEADER_SIZE + room_name_size + token_size
            ].decode("utf-8")
            message = data[HEADER_SIZE + room_name_size + token_size :]

            # クライアントからのメッセージを処理(並列処理)
            threading.Thread(
                target=self.handle_message, args=(message, room_name, token)
            ).start()

    def handle_message(self, message, room_name, token):
        """クライアントからのメッセージを処理する関数

        Args:
            message (bytes): クライアントから送信されたメッセージ
            room_name (str): 部屋名
            token (str): トークン
        """
        room = self.rooms[room_name]
        # exitと送信したユーザーは部屋から退出
        if message == b"exit":
            deleted_user_name = room.token_to_user_name[token]
            if token == room.host_token:
                message = f"{deleted_user_name}が{room_name}から退出しました。\nホストが退出したため、チャットルームを終了します。"
                self.send_others_in_same_room(room, token, message.encode("utf-8"))
                room.remove_all_users()
            else:
                message = f"{deleted_user_name}が{room_name}から退出しました。"
                self.send_others_in_same_room(room, token, message.encode("utf-8"))
                room.remove_client(token)
        else:
            self.send_others_in_same_room(room, token, message)

    def send_others_in_same_room(self, room, token, message):
        # 受け取ったメッセージを部屋内の全クライアントに中継
        for token_key, user_address in room.tokens_to_addrs.items():
            if token != token_key:
                self.udp_socket.sendto(message, tuple(user_address))

    # def recvall_TCRP(self, header , conn):
    #     """TCRPのデータを受取をする関数

    #     Args:
    #         header (32Bytes): クライアントから送信されたヘッダー
    #         conn (socket.socket): 接続されたクライアントのソケットオブジェクト
    #     """
    #     room_name_size, operation, state, payload_size = struct.unpack_from(
    #         "!B B B 29s", header
    #     )
    #     MSGLEN = {
    #         int.from_bytes(room_name_size)
    #         + len(operation)
    #         + len(state)
    #         + int.from_bytes(payload_size)
    #     }
    #     chunks = []
    #     bytes_recd = 0
    #     while bytes_recd < MSGLEN:
    #         chunk = conn.recv(min(MSGLEN - bytes_recd, 4096))
    #         if chunk == b"":
    #             raise RuntimeError("socket connection broken")
    #         chunks.append(chunk)
    #         bytes_recd = bytes_recd + len(chunk)
    #     return b"".join(chunks)


if __name__ == "__main__":
    try:
        server = Server()
        server.start()
    except KeyboardInterrupt:
        print("Keyboard Interrupted")
        server.tcp_socket.close()
        server.udp_socket.close()
        print("\nServer Closed")
