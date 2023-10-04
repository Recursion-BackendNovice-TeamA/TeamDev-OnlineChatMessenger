import socket
import threading
import secrets


class ChatRoom:
    TIMEOUT = 300

    def __init__(self, room_name):
        self.name = room_name
        self.max_clients = 1000
        self.host_token = ""
        self.clients = {}  # クライアント名:クライアントオブジェクトの辞書
        self.tokens_to_addrs = {}  # トークンの辞書:IPアドレスの辞書
        self.messages = []  # チャットメッセージの履歴

    # トークンをrandomで生成する関数
    def generate_token(self):
        token = secrets.token_hex(16)
        self.host_token = token
        return token

    def add_client(self, token, client):
        if len(self.tokens_to_addrs) < self.max_clients:
            self.tokens_to_addrs[token] = client.address
            self.clients[client.name] = client
            return True
        else:
            print("部屋 {} は満員です。".format(self.name))
            return False

    def remove_client(self, client):
        if client.token in self.tokens_to_addrs:
            del self.tokens_to_addrs[client.token]
            del self.clients[client.name]
            client.send_message("exit")
        # ホストが退出した場合、全員退出させる
        if client.is_host:
            self.remove_all_users()
        else:
            print("ユーザー {} は存在しません。".format(self.tokens[client.name]))

    def remove_all_users(self):
        for client in self.clients.values():
            client.send_message("ホストが退出したため、チャットルームを終了します。")
            client.send_message("exit")
        self.clients = {}
        self.tokens_to_addrs = {}
        self.messages = []

    def add_message(self, client, message):
        if client in self.clients:
            self.messages.append(f"{client.name}: {message}")
        else:
            print("トークンを所持していないため、メッセージを送信できません。")

    def send_message(self, client, message):
        if client.token in self.tokens_to_addrs:
            client.send_message(message)
        else:
            print("トークンを所持していないため、メッセージを送信できません。")

    # 部屋内のクライアント全員に送信メッセージを中継する関数
    def relay_message(self, client, message):
        if client.token in self.tokens_to_addrs:
            for token in self.tokens_to_addrs:
                if token != client.token:
                    client.send_message(client.name + ": " + message)
        else:
            print("ユーザー {} は存在しません。".format(client.name))
