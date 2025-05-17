import socket
import threading
import ssl
from datetime import datetime  # Import datetime for timestamps

HOST = "0.0.0.0"
PORT = 65432
clients = {}

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="server.crt", keyfile="server.key")

def broadcast(message):
    """Send message to all connected clients with a timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Add timestamp
    full_message = f"[{timestamp}] {message}"  # Format message with timestamp
    for client_socket in clients.values():
        try:
            client_socket.send(full_message.encode())
        except:
            pass

def send_user_list():
    """Send the updated list of online users to all clients"""
    user_list = "USER_LIST " + ",".join(clients.keys())
    broadcast(user_list)

def handle_client(client_socket, address):
    """Handle client connections and messages"""
    secure_client = context.wrap_socket(client_socket, server_side=True)
    username = secure_client.recv(1024).decode().strip()
    
    if not username or username in clients:
        secure_client.close()
        return

    clients[username] = secure_client
    print(f"{username} connected")
    send_user_list()

    try:
        while True:
            message = secure_client.recv(4096).decode().strip()
            if not message:
                break

            if message.startswith("FILE_REQUEST "):
                _, recipient = message.split(" ", 1)
                if recipient in clients:
                    clients[recipient].send(f"FILE_ALERT {username}".encode())

            elif message.startswith("FILE_PORT "):
                _, recipient, port = message.split(" ")
                if recipient in clients:
                    clients[recipient].send(f"FILE_CONNECT {username} {port}".encode())

            elif message.startswith("PRIVATE "):
                _, recipient, private_msg = message.split(" ", 2)
                if recipient in clients:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Add timestamp
                    clients[recipient].send(f"PRIVATE {username}: [{timestamp}] {private_msg}".encode())

            else:
                broadcast(f"{username}: {message}")

    except ConnectionResetError:
        pass
    finally:
        del clients[username]
        secure_client.close()
        send_user_list()
        print(f"{username} disconnected")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(10)
print(f"Server running on {PORT}...")

while True:
    client_socket, address = server_socket.accept()
    threading.Thread(target=handle_client, args=(client_socket, address)).start()