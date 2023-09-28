#TCP
import socket
import threading

class TCPServer:
    def __init__(self, ip='0.0.0.0', port=9002):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((ip, port))
        self.server_socket.listen(5)
        self.rooms = {}

    # クライアントからの接続を処理する関数
    def handle_client(self, client_socket, client_address):
        try:
            # クライアントからのデータを受信
            # ヘッダー... 部屋名（1バイト） + operation_code（1バイト） + payload（29バイト）(要件定義)
            # 合計32バイト
            header = client_socket.recv(32)
            room_name_size = header[0]
            operation = header[1]

            # ボディ... 部屋名（最大2^8バイト） + payload（最大2^29バイト）(要件定義)
            # ペイロードには希望するユーザー名を入れる（要件定義）
            # 部屋名 ... [:room_name_size]で前から部屋名の長さ分を切り取った分
            # ユーザー名 ... [room_name_size:]で部屋名の長さ分を切り取った後の文字列を扱う
            body = client_socket.recv(4096)
            room_name = body[:room_name_size].decode('utf-8')
            # ペイロード（ユーザー名）は操作と状態によってデコード方法が異なる（要件）（保留）
            user_name = body[room_name_size:].decode('utf-8')


            # operation = 1 ... 部屋作成
            if operation == 1:

                # 部屋が存在しない場合、部屋を作成
                if room_name not in self.rooms:
            
                # 部屋が存在する場合、部屋に参加
                
                
                # クライアントに渡すトークンを生成
                # 部屋名の長さとユーザー名の長さを足したものをオフセットとして使う

                # 部屋リストにトークンを追加

                # クライアントに新しいヘッダーを送信
                # 部屋名の長さ1バイト(b'0'), operation = 1, state = 1をステータスコードとして、payload b'0' * 29と一緒に送信
                # b'011' + b'0' * 29
                
                # operation = 2 ... 部屋参加
                elif operation == 2:


        except KeyboardInterrupt:
            print("Keyboard Interrupted")
            self.server_socket.close()
            print("\nServer Closed")    

    # サーバー起動の関数
    def start(self):
        print("TCP Server Started on port", 9002)
        while True:
            # クライアントからの接続を待つ
            client_socket, _ = self.server_socket.accept()
            # threadingでhandle_clientを実行
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_thread.start()

if __name__ == "__main__":
    # サーバー起動
    tcp_server = TCPServer()
    tcp_server.start()
   