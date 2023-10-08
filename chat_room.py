import secrets


class ChatRoom:
    TIMEOUT = 300

    def __init__(self, room_name):
        self.name = room_name
        self.max_users = 1000
        self.host_token = ""
        self.users = {}  # クライアント名:クライアントオブジェクトの辞書
        self.tokens_to_addrs = {}  # トークンの辞書:ユーザーIPアドレスの辞書
        self.token_to_user_name = {}  # トークン:ユーザー名
        self.messages = []  # チャットメッセージの履歴

    # トークンをrandomで生成する関数
    def generate_token(self):
        token = secrets.token_hex(16)
        return token

    def add_client(self, token, user_address, user_name):
        if len(self.tokens_to_addrs) < self.max_users:
            self.tokens_to_addrs[token] = user_address
            self.token_to_user_name[token] = user_name
            # self.clients[client.name] = client
            return True
        else:
            print("部屋 {} は満員です。".format(self.name))
            return False

    def remove_client(self, token):
        if token in self.tokens_to_addrs:
            del self.tokens_to_addrs[token]
            del self.token_to_user_name[token]
            return True

    def remove_all_users(self):
        # tokens_to_addrsのコピーを作成
        # tokens_to_addrsをforループ中に変更すると、forループが正常に動作しないため
        tokens_to_remove = self.tokens_to_addrs.copy()
        for token in tokens_to_remove:
            if self.remove_client(token):
                self.users = {}
                self.tokens_to_addrs = {}
                self.messages = []

    def add_message(self, client, message):
        if client in self.users:
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
