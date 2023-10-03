import socket
import asyncio


class Server:
    def __init__(self):
        self.address = "127.0.0.1"
        self.port = 12345
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.address, self.port))
        self.buffsize = 4096
        print(f"serverが起動しました: {self.address}:{self.port}")


async def handle_client(server):
    try:
        data, address = await recv_data(server)
        message = data.decode()
        print(f"print: {message}:{address}")
        await send_to_all(server, data, address)
    except KeyboardInterrupt as e:
        print(e)
        server.sock.close()


async def recv_data(server):
    return server.sock.recvfrom(server.buffsize)


async def send_to_all(server, data, address):
    server.sock.sendto(data, address)
    print(f"send {address}")


def main():
    server = Server()
    while True:
        try:
            asyncio.run(handle_client(server))
        except KeyboardInterrupt as e:
            print(e)
            server.sock.close()


if __name__ == "__main__":
    main()
