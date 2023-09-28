
#UDP
import socket
import threading

class UDPServer:
    def __init__(self, ip='0.0.0.0', port=9001):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((ip, port))
        self.clients = set()

    def start(self):
        print("UDP Server Started on port", 9001)
        try: 
            while True:                
                # クライアントからのデータを受信
                message, client_address = self.server_socket.recvfrom(4096)
                # クライアントアドレスを保存
                if client_address not in self.clients:
                    self.clients.add(client_address)

                # 部屋名の長さとトークンの長さを取得


                # 部屋名とトークンを取得
                # 部屋名の長さとトークンの長さを足したものをオフセットとして使う

                # dataの前からオフセット分を切り取り、残りを部屋名として扱う
                # オフセットに部屋名の長さを足して更新

                # トークンを取得
                # dataの前からオフセット分を切り取り、残りをトークンとして扱う

                # オフセットにトークンの長さを足して更新

                # メッセージを取得
                # dataの前からオフセット分を切り取り、残りをメッセージとして扱う


                # 保存してるクライアントアドレスにメッセージを送信　for文で回す
                for client in self.clients:
                    if client != client_address:
                        print(client)
                        self.server_socket.sendto(message, client)
                        
        except KeyboardInterrupt:
            print("Keyboard Interrupted")
            self.server_socket.close()
            print("\nServer Closed")


if __name__ == "__main__":
    server = UDPServer()
    server.start()