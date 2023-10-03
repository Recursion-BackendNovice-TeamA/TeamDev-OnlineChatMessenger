import secrets


class ChatRoom:
    TIMEOUT = 300

    def __init__(self, room_name):
        self.name = room_name
        self.max_clients = 1000
        self.host_token = ""
        self.clients = {}  # クライアント名:クライアントオブジェクトの辞書
        self.tokens = {}  # IPアドレス:トークンの辞書
        self.messages = []  # チャットメッセージの履歴

    # トークンをrandomで生成する関数
    def generate_token(self):
        token = secrets.token_hex(16)
        self.host_token = token
        return token

    def add_client(self, token, client):
        if len(self.tokens) < self.max_clients:
            self.tokens[client.name] = token
            self.clients[client.name] = client
            return True
        else:
            print("部屋 {} は満員です。".format(self.name))
            return False

    def remove_client(self, token, client):
        if token in self.tokens:
            del self.tokens[client.name]
            del self.clients[client.name]
        # ホストが退出した場合、全員退出させる
        if client.is_host:
            for client in self.clients:
                self.clients[client].send_message("ホストが退出しました。")
                self.clients[client].close()
            self.clients = {}
            self.tokens = {}
            self.messages = []
        else:
            print("ユーザー {} は存在しません。".format(self.tokens[client.name]))

    def remove_all_users(self):
        self.tokens = {}

    def add_message(self, token, client_name, message):
        if token in self.tokens:
            user_name = self.tokens[token]
            self.messages.append((user_name, message))
        else:
            print("ユーザー {} は存在しません。".format(self.tokens[client_name]))

    def send_message(self, token, client_name, message):
        if token in self.tokens:
            user_name = self.tokens[token]
            self.clients[user_name].send_message(message)
        else:
            print("ユーザー {} は存在しません。".format(self.tokens[client_name]))

    # 部屋内のクライアント全員に送信メッセージを中継する関数
    def relay_message(self, token, client_name, message):
        if token in self.tokens:
            user_name = self.tokens[token]
            for client in self.clients:
                if client != user_name:
                    self.clients[client].send_message(user_name + ": " + message)
        else:
            print("ユーザー {} は存在しません。".format(self.tokens[client_name]))
