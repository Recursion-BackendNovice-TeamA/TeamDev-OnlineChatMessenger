import socket
import threading

def start_udp_client():
    host = '0.0.0.0'
    port = 9001
    buffer_size = 4096

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    nickname = input("Enter your nickname: ")
    formatted_message = f"{nickname}が参加しました。".encode('utf-8')
    client_socket.sendto(formatted_message, (host, port))


    def send_message():
        while True:
            message = input()
            formatted_message = f"{nickname}: {message}".encode('utf-8')
            if len(formatted_message) > 255:
                raise ValueError("文字数が255バイトを超えています。")
            # ソケットにデータを送信
            client_socket.sendto(formatted_message, (host, port))

    def receive_message():
        print('receive_start')
        while True:
            message, _ = client_socket.recvfrom(buffer_size)
            print(message.decode('utf-8'))

    threading.Thread(target=send_message).start()
    threading.Thread(target=receive_message).start()

if __name__ == "__main__":
    start_udp_client()
