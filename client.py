import socket
import json
import struct
import threading


# ChatClientクラスを定義
class Client:
    def __init__(self, name):
        self.name = name
        self.server_address = ("0.0.0.0", 9002)
        self.token = ""
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = self.udp_socket.getsockname()[0]

    # クライアントを起動する関数
    def start(self):
        # ユーザー入力後にアクションを選ばせる(部屋作成・参加・終了)
        op = input(
            "0, Send a message(test)\n1. Create a new room\n2. Join an existing room\n3. Quit\nChoose an option: "
        )
        if op == "3":
            print("Closing connection...")
            self.udp_socket.close()
            print("Connection closed.")
            exit()

        self.tcp_connect(int(op))

    def tcp_connect(self, operation):
        # サーバーにTCP接続
        # TCPサーバーのポート：9002
        self.tcp_socket.connect(self.server_address)

        # 入室リクエストを送信・レスポンス待機
        self.tcp_request(operation)

    # 部屋入室リクエストの関数（作成・参加共通）
    def tcp_request(self, operation):
        # 部屋名を入力させる
        room_name = input("Enter room name: ")

        payload = {
            "user_name": self.name,
            "address": self.address,
        }

        payload_data = json.dumps(payload).encode("utf-8")

        # ヘッダーを作成(state = 0)
        header = struct.pack(
            "!B B B 29s",
            len(room_name),
            operation,
            0,
            len(payload_data).to_bytes(29, byteorder="big"),
        )

        # ボディを作成
        body = room_name.encode("utf-8") + payload_data

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

        # メッセージを送信
        threading.Thread(target=self.send_message).start()

        # 他クライアントからのメッセージを別スレッドで受信
        threading.Thread(target=self.receive_message).start()

    # メッセージを送信する関数
    def send_message(self):
        # メッセージを入力させる
        while True:
            message = input("Enter your message: ")

            if message == "exit":
                print("Closing connection...")
                self.udp_socket.close()
                print("Connection closed.")
                exit()

            # メッセージを送信
            self.udp_socket.sendto(
                f"{self.name}: {message}".encode("utf-8"), self.server_address
            )

    # メッセージを受信する関数
    def receive_message(self):
        while True:
            # メッセージを受信
            data, _ = self.udp_socket.recvfrom(4096)
            print(data.decode("utf-8"))


if __name__ == "__main__":
    print("---WELCOME TO THE CHAT MESSENGER PROGRAM!---")
    client = Client(input("Enter your username: "))
    client.start()
