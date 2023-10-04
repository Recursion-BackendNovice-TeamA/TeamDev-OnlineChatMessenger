import socket

server_address = ("0.0.0.0", 9002)
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clients = {}


# stage1 の送信プロトコル
# header: usernamelen(1bytes)
# body: name(1~255bytes) | message()
#  Test用 半角全角による表記ブレの対策済み
def protocol_test_stg1():
    name = "testMr.なまえ"
    message = "testこれはメッセージ123test"
    header = len(name.encode()).to_bytes(1, "big")
    print(header)
    body = name.encode() + message.encode()
    print(body)
    full_message = header + body
    print(full_message)

    print("decoded...")
    print("UserNameLen: " + str(full_message[0]))
    print("UserName: " + full_message[1 : full_message[0] + 1].decode())
    print("message: " + full_message[full_message[0] + 1 :].decode())


def client_sendto_stg1():
    name = "testMr.なまえ"
    message = "testこれはメッセージ123test"
    header = len(name.encode()).to_bytes(1, "big")
    body = name.encode() + message.encode()
    full_message = header + body
    udp_socket.sendto(full_message, server_address)


def server_handle_stg1():
    data, address = udp_socket.recvfrom(4096)

    for key in clients.keys():
        if key != address:
            udp_socket.sendto(data, key)


def client_recv():
    data, _ = udp_socket.recvfrom(4096)
    namelen = data[0]
    name = data[1 : 1 + namelen].decode()
    message = data[1 + namelen :].decode()
    print(f"[{name}] : {message}")


# stage2 TCRP(チャットルームプロトコル)
# header(32byte): RoomNameSize(1byte) | Operation(1byte) | State(1byte) | OperationPayloadSize(29byte)
# body: RoomName(Max 2^8byte) | OperationPayloadSize(Max 2^29byte)
def tcrp_test_host():
    user_name = "testMr.なまえ"
    room_name = "chatRoomチャットルーム123"
    # Operation: 1.ルーム作成 | 2.ルーム参加
    # State: 0:リクエスト | 1.準拠or応答 | 2.完了
    # Operation 1の場合 host
    # Operation == 1 and State == 0 and OperationPayload == user_name
    # client が server　にリクエスト
    room_name_size = len(room_name.encode()).to_bytes(1, "big")
    Operation = (1).to_bytes(1, "big")
    State = (0).to_bytes(1, "big")
    payload = len(user_name.encode()).to_bytes(29, "big")
    header = room_name_size + Operation + State + payload
    body = room_name.encode() + user_name.encode()
    full_message = header + body
    # tcp_socket.sendto(full_message, server_address)
    # State == 1が来るまで送り続ける
    # n秒毎が良い　一定時間後受信しないならタイムアウトを出す

    # server の処理
    # Operation が１ならルーム作成の処理　２ならルーム内でClientのインスタンス生成
    # full_message, address = tcp_socket.recvfrom(4096)
    header = full_message[0:32]
    body = full_message[32:]
    print(header)
    print(body)

    roomlen = header[0]
    Ope = header[1]
    sta = header[2]
    pay = header[3:]
    romname = body[:roomlen]
    username = body[roomlen:]
    print(f"header =={roomlen}:{Ope}:{sta}:{pay}")
    print(f"body =={romname.decode()}:{username.decode()}")
    # state を　1に変えてクライアントに返信する
    changed_state0to1 = header[:2] + (1).to_bytes(1, "big") + pay + body
    # tcp_socket.sendto(changed_state0to1, address)
    print(len(changed_state0to1))
    # client の処理
    # state == 1　を受け取ったので受信待ちに移行する
    # bodyの情報も見れるのでロスがないかわかる
    # ある場合の処理は、state == 0　で再送

    # server の処理
    # state == 1 で　返信が来て内容が同じなら以下の処理をする
    # state == 0ならはじめからになる
    # Server が ChatRoom を作り、 ChatRoom を server.chatrooms{roomname: ChatRoom}　で管理する
    # ChatRoom が ClientInfo とtokenを作る　ChatRoom.clients{} で管理
    # state == 2 で payload が　token　で送信する
    # token　は　random.randint(0,256).to_bytes(1,'big')で作り byteで保管する


tcrp_test_host()


# stage2 client ---> server Max4096byte
# header(2byte): RoomNameSize(1byte) | TokenSize(1byte)
# body: RoomName | token | message
def client_sendto():
    # roomname とtokenはある
    # header = (len(roomname.encode())).to_bytes(1,'big') + (len(token)).to_bytes(1,'big')
    # body = roomname.encode() + token + message.encode()
    # if len(header + body) <= 4096:
    #    udp_socket.sendto(header+body, server_address)
    print("")


def server_recvfrom():
    print("")


# stage2 client <--- server  recv Max 4094(byte), Only message, not include header
def client_recv():
    print("")


def server_sendto():
    print("")
