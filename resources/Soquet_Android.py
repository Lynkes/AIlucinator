import socket

server_ip = '0.0.0.0'  # Ou o IP da sua máquina na LAN
server_port = 9596

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((server_ip, server_port))
server_socket.listen(1)

print(f"Servidor ouvindo em {server_ip}:{server_port}")

conn, addr = server_socket.accept()
print(f"Conexão de {addr}")

with open('audio_received.wav', 'wb') as audio_file:
    data = conn.recv(1024)
    while data:
        audio_file.write(data)
        data = conn.recv(1024)

conn.close()
server_socket.close()