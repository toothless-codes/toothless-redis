import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 12345))  # bind to IP address and port
server_socket.listen(5)  # max 5 connections

print("Waiting for a connection...")
client_socket, addr = server_socket.accept()
print(f"Connection from {addr}")

client_socket.sendall(b'Hello from server!')
client_socket.close()
