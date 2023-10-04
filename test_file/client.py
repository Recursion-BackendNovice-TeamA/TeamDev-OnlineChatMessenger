import socket
import asyncio

server_address = "127.0.0.1"
server_port = 12345
buffsize = 4096
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


async def recv_message():
    print(udp_sock.recv(buffsize).decode())


async def send_message():
    message = input("write a message: ")
    full_message = message.encode()
    udp_sock.sendto(full_message, (server_address, server_port))


async def handler():
    while True:
        asyncio.gather(send_message(), recv_message())


def main():
    asyncio.run(handler())


if __name__ == "__main__":
    main()
