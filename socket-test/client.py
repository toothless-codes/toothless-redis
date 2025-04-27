import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 12345))  # connect to server

message = client_socket.recv(1024)  # receive up to 1024 bytes
print(message.decode())

client_socket.close()