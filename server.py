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
        # state
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
                    executor.submit(self.__handle_tcp_conn)
                    executor.submit(self.__handle_udp_conn)

            except KeyboardInterrupt:
                print("Keyboard Interrupted")
                self.tcp_socket.close()
                self.udp_socket.close()
                print("\nServer Closed")
                break

    def __handle_tcp_conn(self):
        """TCO接続を処理する関数"""
        while True:
            self.tcp_socket.listen(5)
            conn, _ = self.tcp_socket.accept()
            # クライアントからのTCP接続を処理(並列処理)
            try:
                # クライアントからのデータを受信
                header = conn.recv(self.HEADER_BYTE_SIZE)
                room_name_size, operation, _, _ = struct.unpack_from(
                    "!B B B 29s", header
                )
                body = conn.recv(4096)

                room_name = body[:room_name_size].decode("utf-8")
                payload_data = body[room_name_size:].decode("utf-8")

                # payloadはjson形式の文字列とする
                # payloadをloadsして辞書に変換
                payload = json.loads(payload_data)
                user_name = payload["user_name"]
                user_address = payload["user_address"]
            except Exception as e:
                print(f"Server Error:{e}")
                self.__send_state_res(
                    conn, room_name, operation, self.ERROR_RESPONSE, ""
                )
                break

            try:
                token = self.__create_or_join_room(
                    room_name, user_address, user_name, operation
                )

                self.__send_state_res(
                    conn, room_name, operation, self.REQUEST_COMPLETION, token
                )
            except Exception as e:
                print(f"Server Error:{e}")
                self.__send_state_res(conn, room_name, operation, self.SERVER_INIT, "")

    def __generate_token(self):
        """トークンをrandomで生成する関数

        Returns:
            token: トークン
        """
        token = secrets.token_hex(32)
        return token

    def __create_or_join_room(self, room_name, user_address, user_name, operation):
        """部屋を作成もしくは参加する関数

        Args:
            room_name (str): チャットルーム名
            user_address (tuple): クライアントのアドレス（IPアドレスとポート番号)
            user_name (str): ユーザー名
            operation (int): クライアントが入力したアクション番号(1:部屋作成, 2:参加)
        """
        # クライアントにトークンを発行
        token = self.__generate_token()

        if operation == self.CREATE_ROOM_NUM:
            # 作成する部屋が存在する場合
            if room_name in self.rooms:
                raise KeyError(f"Key {room_name} found in {self.rooms}.")
            # キーとして部屋名が部屋リストに存在しない場合
            elif room_name not in self.rooms:
                # 部屋を作成
                room = ChatRoom(room_name)
                self.rooms[room_name] = room
                print(f"{user_name}が{room_name}を作成しました。")
                # ホストトークン設定
                room.host_token = token
        elif operation == self.JOIN_ROOM_NUM:
            # 参加する部屋が存在しない場合
            if room_name not in self.rooms:
                raise KeyError(f"Key {room_name} not found in {self.rooms}.")
            # 部屋が存在する場合
            elif room_name in self.rooms:
                room = self.rooms[room_name]

        # 部屋にユーザーを追加
        if room.add_client(token, user_address, user_name):
            print(f"{user_name}が{room_name}に参加しました。")
            return token

    # リクエストの状態に応じてヘッダーとペイロードを送信する関数
    def __send_state_res(self, conn, room_name, operation, state, token):
        """_summary_

        Args:
            conn (socket.socket): 接続されたクライアントのソケットオブジェクト
            room_name (str): 部屋名
            operation (str): クライアントが入力したアクション番号(1:部屋作成, 2:参加)
            state (int): 操作コード: サーバの初期化(0)、リクエストの応答(1)、リクエストの完了(2)
            token (str): トークン
        """
        if state == self.SERVER_INIT:
            payload_data = (
                {"status": 400, "message": "部屋 {} はすでに存在します".format(room_name)}
                if operation == 1
                else {"status": 400, "message": "部屋 {} は存在しません".format(room_name)}
            )
        elif state == self.RESPONSE_OF_REQUEST:
            payload_data = {"status": 200, "message": "リクエストを受理しました。"}
        elif state == self.ERROR_RESPONSE:
            payload_data = {
                "status": 500,
                "message": "リクエストを完了できませんでした。\n入力し直してください。",
            }
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

    def __handle_udp_conn(self):
        """クライアントからのUDP接続経由でメッセージを受信する関数"""
        HEADER_SIZE = 2

        while True:
            data, _ = self.udp_socket.recvfrom(4096)

            room_name_size, token_size = struct.unpack_from("!B B", data[:HEADER_SIZE])
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
        sender_name = room.token_to_user_name[token]
        # exitと送信したユーザーは部屋から退出
        if message == b"exit":
            if token == room.host_token:
                message = f"{sender_name}が{room_name}から退出しました。\nホストが退出したため、チャットルーム:{room_name}を終了します。"
                self.__send_others_in_same_room(room, token, message)
                room.remove_all_users()
                del self.rooms[room.name]
            else:
                message = f"{sender_name}が{room_name}から退出しました。"
                self.__send_others_in_same_room(room, token, message)
                room.remove_client(token)
            print(message)
        else:
            print(f"{room_name}: {sender_name}が'{message.decode('utf-8')}'を送信しました。")
            decoded_message = message.decode("utf-8")
            message = f"{sender_name}: {decoded_message}"
            self.__send_others_in_same_room(room, token, message)

    def __send_others_in_same_room(self, room, token, message):
        """同じ部屋の他のユーザーにメッセージを送信

        Args:
            room (chat_room.ChatRoom): ChatRoomインスタンス
            token (str): トークン
            message (str): 送信メッセージ
        """
        # 受け取ったメッセージを部屋内の全クライアントに中継
        for token_key, user_address in room.tokens_to_addrs.items():
            if token != token_key:
                self.udp_socket.sendto(message.encode("utf-8"), tuple(user_address))

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
