import socket
import random
import string


# randomを使って、クライアントに渡すためのトークンを生成(最大255バイト)
# このトークンにユーザー名を割り当てる
# このトークンはクライアントをルームホストとして識別するために使用される
def generate_token(chars=string.ascii_uppercase + string.digits):
    return "".join(random.choice(chars) for _ in range(255))


# チャットルーム作成・参加時にTCP接続するための関数
# TCP接続を初期化するために、ユーザー名とオペレーションコードをサーバーに送信する
def tcp_connect(user_name, operation):
    # 部屋名を入力させる
    room_name = input("Enter a room name: ")

    # ヘッダー... 部屋名の長さ(1バイト) + オペレーションコード(1バイト) + 通信状態state(1バイト) + payload(29バイト)（要件）
    header = bytes([len(room_name), operation, 0]) + b"0" * 29
    # ボディ... 部屋名（最大2^8バイト） + payload（最大2^29バイト）(要件)
    # ペイロードには希望するユーザー名を入れる（要件）
    body = room_name.encode("utf-8") + user_name.encode("utf-8")

    # サーバーにTCP接続
    # TCPサーバーのポート：9002
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect(("0.0.0.0", 9002))
    # ヘッダーとボディをサーバーに送信
    req = header + body
    tcp_socket.sendall(req)

    # サーバーからヘッダーとボディを受信
    res = tcp_socket.recv(4096)

    # stateを取得
    state = res[2]
    # state = 1 ... 成功
    if state == 1:
        # トークンを受信(生成)
        # トークンにはIPアドレスを含める
        token = generate_token()
        # トークンをエンコードしてpayloadとする
        payload = token.encode("utf-8")
        # ヘッダーのstateを2(リクエスト完了)に更新
        header = header[:2] + bytes(2) + header[3:]
        # ヘッダーとボディとpayloadをクライアントに送信
        tcp_socket.sendall(header + body + payload)
        # TCP接続を閉じる
        tcp_socket.close()
        # 部屋名とトークンを返す
        return room_name, token
    else:
        print("サーバーとの接続に失敗しました。")
        exit()


# メッセージ送信用の関数
def send_message(client_socket, room_name, token):
    # # メッセージを入力させる
    # message = input("Enter your message:")
    # # ヘッダー... 部屋名の長さ(1バイト) + 取得したトークンの長さ(1バイト)
    # header = bytes(len(room_name), len(token))
    # # ヘッダー + 部屋名 + トークン + メッセージをサーバーに送信
    # full_message = header + room_name.encode('utf-8') + token.encode('utf-8') + message.encode('utf-8')
    # if(len(full_message) > 255):
    #     print("Message too long.")

    # client_socket.sendto(full_message, ('0.0.0.0', 9001))

    # メッセージ送信テスト用
    message = input("Enter your message:")
    full_message = message.encode("utf-8")
    client_socket.sendto(full_message, ("0.0.0.0", 9001))

    try:
        data, _ = client_socket.recvfrom(4096)
        print(data.decode("utf-8"))
    except:
        print("No response.")
        exit()


if __name__ == "__main__":
    print("---WELCOME TO THE CHAT MESSENGER PROGRAM!---")
    while True:
        username = input("Enter your username: ")
        if len(username) < 0:
            print("Username must be at least 1 character long.")
        # ユーザーがすでに存在してたら、ユーザー名を再入力させる条件分岐を追加
        else:
            break
    # ユーザー入力後にアクションを選ばせる(部屋作成・参加・終了)
    option = input(
        "0, Send a message(test)\n1. Create a new room\n2. Join an existing room\n3. Quit\nChoose an option: "
    )

    if option == "1":
        room_name, token = tcp_connect(username, 1)
    elif option == "2":
        room_name, token = tcp_connect(username, 2)
    elif option == "0":
        # send_message動作確認用
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.settimeout(60)
        while True:
            send_message(udp_socket, "dummy_room", "dummy token")

    else:
        exit()

    # メッセージ送信用ソケットは、部屋作成・参加後に作成
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # ６０秒間他クライアントからの送信がなかった場合、タイムアウト
    udp_socket.settimeout(60)
    # メッセージ送信
    while True:
        send_message(udp_socket, room_name, token)
