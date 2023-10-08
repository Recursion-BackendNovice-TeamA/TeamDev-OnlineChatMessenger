import socket
import struct
import threading


class User:
    TIMEOUT = 300

    def __init__(self, name):
        """Userクラスインスタンス化

        Args:
            name (str): ユーザー名

         Note:
             UDPソケットをアドレスとポート番号にバインドする際に、ポート番号に0を渡すことで
             OSが利用可能なランダムなポートを選び、それ利用することができる。
        """
        self.__RANDOM_PORT_NUM = 0
        self.__udp_server_address = ("127.0.0.1", 9003)
        self.__udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__udp_socket.bind(("127.0.0.1", self.__RANDOM_PORT_NUM))
        self.name = name
        self.token = ""
        self.room_name = ""
        self.is_host = False
        self.address = self.__udp_socket.getsockname()
        self.__timer = None

        # クライアントが入力したアクション番号
        self.__CREATE_ROOM_NUM = 1
        self.__JOIN_ROOM_NUM = 2
        self.__QUIT = 3

    def __input_text(self, input_description):
        """テキスト入力

        Note:
            テキストの入力と同時にタイムアウトタイマーをリセットする

        Returns:
            (str): 入力テキスト
        """
        while True:
            text = input(input_description)
            # Enterなどの入力文字がない場合は再度入力させる
            if text == "":
                continue
            return text

    def input_action_number(self):
        """アクション番号の入力

        Note:
            1: 新しく部屋を作成
            2: 既存の部屋に入室
            3: 入力操作をやめる

        Returns:
            (str): 入力番号(1、2、3のいずれか)
        """
        while True:
            try:
                print("Please enter 1, 2 or 3")
                input_description = "1. Create a new room\n2. Join an existing room\n3. Quit\nChoose an option: "
                operation = self.__input_text(input_description)
                if int(operation) in [
                    self.__CREATE_ROOM_NUM,
                    self.__JOIN_ROOM_NUM,
                    self.__QUIT,
                ]:
                    return operation
            except Exception:
                continue

    def input_room_name(self):
        """部屋名の入力

        Returns:
            (str): 部屋名
        """
        while True:
            ROOM_NAME_MAX_BYTE_SIZE = 255
            input_description = "Enter room name: "
            self.room_name = self.__input_text(input_description)
            room_name_size = len(self.room_name.encode("utf-8"))
            if room_name_size > ROOM_NAME_MAX_BYTE_SIZE:
                print(f"Room name bytes: {room_name_size} is too large.")
                print(
                    f"Please retype the room name with less than {ROOM_NAME_MAX_BYTE_SIZE} bytes"
                )
                continue
            return self.room_name

    def __generate_request(self, message):
        """リクエスト情報の生成

        Args:
            message (str): メッセージ

        Returns:
            bytes: リクエスト情報
        """
        header = struct.pack(
            "!B B",
            len(self.room_name.encode("utf-8")),
            len(self.token.encode("utf-8")),
        )
        body = self.room_name + self.token + message
        encoded_body = body.encode("utf-8")
        request_info = header + encoded_body
        return request_info

    def send_message(self):
        """メッセージの送信"""

        while True:
            # メッセージの入力
            input_message = self.__input_text("")
            self.__reset_timer()
            request_info = self.__generate_request(input_message)
            # メッセージを送信
            # Todo メッセージのバイトサイズを超えた際の例外処理
            self.__udp_socket.sendto(request_info, self.__udp_server_address)
            if "exit" == input_message:
                self.__udp_socket.close()
                exit()

    def receive_message(self):
        """メッセージの受信"""
        while True:
            # メッセージを受信
            data, _ = self.__udp_socket.recvfrom(4096)
            decoded_data = data.decode("utf-8")
            print(decoded_data)
            if (
                f"ホストが退出したため、チャットルーム:{self.room_name}を終了します。" in decoded_data
                or decoded_data == f"{self.name}が{self.room_name}から退出しました。"
            ):
                print("UDPソケットを閉じる。")
                self.__cancel_timer()
                self.__udp_socket.close()
                exit()

    def __reset_timer(self):
        """タイムアウトのカウントをリセットする"""
        self.start_timer()

    def start_timer(self):
        """タイマーを開始または再開する"""
        if self.__timer:
            # 既存のタイマーがあればキャンセル
            self.__timer.cancel()
        self.__timer = threading.Timer(User.TIMEOUT, self.__timeout)
        self.__timer.start()

    def __timeout(self):
        """指定した時間が経過したときに実行されるメソッド"""
        print("Timed out!")
        request_info = self.__generate_request("exit")

        # メッセージを送信
        # Todo メッセージのバイトサイズを超えた際の例外処理
        self.__udp_socket.sendto(request_info, self.__udp_server_address)
        self.__udp_socket.close()
        exit()

    def __cancel_timer(self):
        """タイマーを止める"""
        self.__timer.cancel()
