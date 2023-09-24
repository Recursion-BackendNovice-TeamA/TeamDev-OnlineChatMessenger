import socket

def start_udp_server():
    host = '0.0.0.0'
    port = 9001
    buffer_size = 4096

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))

    clients = set()

    print("UDP Server Started on port", port)
    try:
        while True:
            message, client_address = server_socket.recvfrom(buffer_size)
            clients.add(client_address)

            print(f"[{client_address}] {message.decode('utf-8')}")

            for client in clients:
                if client != client_address:
                    print(client)
                    server_socket.sendto(message, client)
    except KeyboardInterrupt:
        server_socket.close()
        print("\nUDP Server Closed")

if __name__ == "__main__":
    start_udp_server()
