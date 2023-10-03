import socket

server_address = ("0.0.0.0", 9002)
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clients = {}
name = "testMr.なまえ"
message = "testこれはメッセージ123test"


# stage1 の送信プロトコル
# header: usernamelen(1bytes)
# body: name(1~255bytes) | message()
#  Test用 半角全角による表記ブレの対策済み
def protocol_test_stg1():
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


# stage2 client ---> server Max4096byte
# header(2byte): RoomNameSize(1byte) | TokenSize(1byte)
# body: RoomName | token | message
def client_sendto():
    print("")


def server_recvfrom():
    print("")


# stage2 client <--- server  recv Max 4094(byte), Only message, not include header
def client_recv():
    print("")


def server_sendto():
    print("")
