import socket
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

    # クライアントからのTCP接続を待機する関数
    def wait_for_tcp_conn(self):
        while True:
            self.tcp_socket.listen(5)
            conn, client_address = self.tcp_socket.accept()
            # クライアントからのTCP接続を処理(並列処理)
            threading.Thread(
                target=self.handle_tcp_conn, args=(conn, client_address)
            ).start()

    # クライアントからのTCP接続を処理する関数
    def handle_tcp_conn(self, conn, client_address):
        # クライアントからのデータを受信
        header = conn.recv(32)
        room_name_size, operation, state, operation_payload_size = struct.unpack('!B B B 29s', header)

        body = conn.recv(4096)
        decoded_body = body.decode("utf-8")

        room_name = decoded_body[:room_name_size]
        user_name = decoded_body[room_name_size:]

        # operation = 1 ... 部屋作成
        if operation == 1:
            self.create_room(room_name, conn, client_address, user_name)

        # operation = 2 ... 部屋参加
        if operation == 2:
            self.assign_room(room_name, conn, client_address, user_name)

    # 部屋を作成する関数
    def create_room(self, room_name, conn, client_address, user_name):
        # キーとして部屋名が部屋リストに存在しない場合
        if room_name not in self.rooms:
            # 部屋を作成
            new_room = ChatRoom(room_name)
            self.rooms[room_name] = new_room
            print(room_name, "を作成しました。")

            # クライアントにトークンを発行
            client = ChatClient(user_name, client_address)
            token = new_room.generate_token()
            client.token = token

            # 部屋にユーザーを追加
            new_room.add_client(token, client)

            # クライアントをホストに設定
            client.is_host = True

            # クライアントに新しいヘッダーを送信(state = 2)
            res = bytes([len(room_name), 1, 2]) + b"0" * 29
            conn.sendall(res)

        else:
            print("部屋 {} は既に存在します。".format(room_name))
            # クライアントに新しいヘッダーを送信(state = 0)
            res = b"\x00\x01\x00" + b"0" * 29
            conn.sendall(res)

    # クライアントを部屋に参加させる関数
    def assign_room(self, room_name, conn, client_address, user_name):
        # 部屋が存在する場合
        if room_name in self.rooms:
            # クライアントに新しいヘッダーを送信(state = 1)
            res = bytes([len(room_name), 1, 1]) + b"0" * 29
            conn.sendall(res)
            room = self.rooms[room_name]

            # クライアントにトークンを発行
            token = room.generate_token()
            client = ChatClient(client_address, user_name)
            client.token = token
            # 部屋にユーザーを追加
            room.add_client(token, client)
            print("{} が部屋 {} に参加しました。".format(user_name, room_name))

            # クライアントに新しいヘッダーを送信(state = 2)
            res = b"\x00\x01\x02" + b"0" * 29
            conn.sendall(res)
        else:
            print("部屋 {} は存在しません。".format(room_name))
            # クライアントに新しいヘッダーを送信(state = 0)
            res = b"\x00\x02\x00" + b"0" * 29
            conn.sendall(res)

    # クライアントからのUDP接続経由でメッセージを受信する関数
    def receive_message(self):
        while True:
            data, client_address = self.udp_socket.recvfrom(4096)
            # クライアントからのメッセージを処理(並列処理)
            threading.Thread(
                target=self.handle_message, args=(data, client_address)
            ).start()

    # クライアントからのメッセージを処理する関数
    def handle_message(self, data, client_address):
        # 受け取ったメッセージを部屋内の全クライアントに中継
        for room_name in self.rooms:
            room = self.rooms[room_name]
            if client_address in room.clients:
                client = room.clients[client_address]
                room.add_message(client.token, client.name, data)
                for client in room.clients:
                    room.clients[client].send_message(data)


if __name__ == "__main__":
    try:
        server = Server()
        server.start()
    except KeyboardInterrupt:
        print("Keyboard Interrupted")
        print("\nServer Closed")
