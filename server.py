import socket
import json
import struct
import threading
from concurrent.futures import ThreadPoolExecutor

from chat_room import ChatRoom
from chat_client import ChatClient


class Server:
    def __init__(self):
        self.tcp_address = ("0.0.0.0", 9002)
        self.udp_address = ("0.0.0.0", 9003)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_socket.bind(self.tcp_address)
        self.udp_socket.bind(self.udp_address)
        # room_name: ChatRoom インスタンスの辞書
        self.rooms = {}
        self.HEADER_BYTE_SIZE = 32

    # サーバー起動の関数
    def start(self):
        print("Server Started on port", 9002)

        while True:
            try:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    executor.submit(self.wait_for_tcp_conn)
                    executor.submit(self.receive_message)

                # クライアントからのTCP接続を待機(並列処理)
                # threading.Thread(target=self.wait_for_tcp_conn).start()
                # クライアントからのUDP接続経由でメッセージを受信(並列処理)
                # threading.Thread(target=self.receive_message).start()

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
            conn, client_address = self.tcp_socket.accept()
            # クライアントからのTCP接続を処理(並列処理)
            threading.Thread(
                target=self.handle_tcp_conn, args=(conn, client_address)
            ).start()

    def handle_tcp_conn(self, conn, client_address):
        """クライアントからのTCP接続を処理する関数

        Args:
            conn (socket.socket): 接続されたクライアントのソケットオブジェクト
            client_address (tuple): クライアントのアドレス（IPアドレスとポート番号)
        """
        try:
            # クライアントからのデータを受信
            header = conn.recv(self.HEADER_BYTE_SIZE)
            room_name_size, operation, state, operation_payload_size = struct.unpack(
                "!B B B 29s", header
            )
            body = conn.recv(4096)

            room_name = body[:room_name_size].decode("utf-8")
            payload_data = body[room_name_size:].decode("utf-8")

            # payloadはjson形式の文字列とする
            # payloadをloadsして辞書に変換
            payload = json.loads(payload_data)
            user_name = payload["user_name"]
            client_address = payload["address"]
        except Exception as e:
            print(e)
            server.tcp_socket.close()
            server.udp_socket.close()
            exit()

        # operation = 1 ... 部屋作成
        if operation == 1:
            self.create_room(room_name, conn, client_address, user_name)

        # operation = 2 ... 部屋参加
        if operation == 2:
            self.assign_room(room_name, conn, client_address, user_name)

    def create_room(self, room_name, conn, client_address, user_name):
        """部屋を作成する関数

        Args:
            room_name (str): チャットルーム名
            conn (socket.socket): 接続されたクライアントのソケットオブジェクト
            client_address (tuple): クライアントのアドレス（IPアドレスとポート番号)
            user_name (str): ユーザー名
        """
        # クライアントに新しいヘッダーを送信(state = 1)
        self.send_state_res(conn, room_name, 1, 1, "")
        # キーとして部屋名が部屋リストに存在しない場合
        if room_name not in self.rooms:
            # 部屋を作成
            new_room = ChatRoom(room_name)
            self.rooms[room_name] = new_room
            print(f"{user_name}が{room_name}を作成しました。")

            # クライアントにトークンを発行
            client = ChatClient(name=user_name, address=client_address)
            token = client.token

            # 部屋にユーザーを追加
            new_room.add_client(token, client)

            # クライアントをホストに設定
            client.is_host = True
            # 作成して参加した部屋名
            client.room_name = room_name

            # クライアントに新しいヘッダーを送信(state = 2)
            self.send_state_res(conn, room_name, 1, 2, token)
        else:
            self.send_state_res(conn, room_name, 1, 0, "")

    def assign_room(self, room_name, conn, client_address, user_name):
        """クライアントを部屋に参加させる関数

        Args:
            room_name (str): チャットルーム名
            conn (socket.socket): 接続されたクライアントのソケットオブジェクト
            client_address (tuple): クライアントのアドレス（IPアドレスとポート番号)
            user_name (str): ユーザー名

        Todo:
            同姓同名の人物がいる場合の処理
        """
        # クライアントに新しいヘッダーを送信(state = 1)
        self.send_state_res(conn, room_name, 2, 1, "")
        # 部屋が存在する場合
        if room_name in self.rooms:
            room = self.rooms[room_name]

            # クライアントにトークンを発行
            client = ChatClient(name=user_name, address=client_address)
            token = client.token
            # 部屋にユーザーを追加
            room.add_client(token, client)
            print(f"{user_name}が{room_name}に参加しました。")

            # クライアントに新しいヘッダーを送信(state = 2)
            self.send_state_res(conn, room_name, 2, 2, token)
        else:
            self.send_state_res(conn, room_name, 2, 3, "")

    # リクエストの状態に応じてヘッダーとペイロードを送信する関数
    def send_state_res(self, conn, room_name, operation, state, token):
        if state == 3:
            payload_data = (
                {"status": 400, "message": "部屋 {} はすでに存在します".format(room_name)}
                if operation == 1
                else {"status": 404, "message": "部屋 {} は存在しません".format(room_name)}
            )
        # elif state == 1:
        #     payload_data = {"status": 200, "message": "リクエストを受理しました。"}
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

    # クライアントからのUDP接続経由でメッセージを受信する関数

    def receive_message(self):
        """クライアントからのUDP接続経由でメッセージを受信する関数"""
        HEADER_SIZE = 1

        while True:
            data, sender_address = self.udp_socket.recvfrom(4096)

            # Todo トークンも変換
            room_name_size = struct.unpack("!B", data[:1])[0]
            room_name = data[HEADER_SIZE : HEADER_SIZE + room_name_size].decode("utf-8")
            message = data[HEADER_SIZE + room_name_size :]

            # クライアントからのメッセージを処理(並列処理)
            threading.Thread(
                target=self.handle_message, args=(message, room_name, sender_address)
            ).start()

    def handle_message(self, message, room_name, sender_address):
        """クライアントからのメッセージを処理する関数

        Args:
            message (bytes): クライアントから送信されたメッセージ
            room_name (str): 部屋名
            sender_address (tuple): メッセージ送信者のアドレス（IPアドレスとポート番号)
        """

        _, sender_port = sender_address
        # 受け取ったメッセージを部屋内の全クライアントに中継
        for client in self.rooms[room_name].clients.values():
            _, client_port = client.address
            if sender_port != client_port:
                self.udp_socket.sendto(message, tuple(client.address))

        # if sender_address in room.clients:
        # client = room.clients[sender_address]
        # room.add_message(client.token, client.name, message)
        # host, port = client.address
        # room.clients[client].send_message(message)


if __name__ == "__main__":
    try:
        server = Server()
        server.start()
    except KeyboardInterrupt:
        print("Keyboard Interrupted")
        server.tcp_socket.close()
        server.udp_socket.close()
        print("\nServer Closed")
