import socket
import os
import threading
import time
import hashlib

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
FILE_DIR = "server_files"
FILE_LIST = "file_list.txt"
CHUNK_SIZE = 1024
ACK_TIMEOUT = 2  # Timeout in seconds for retransmission

def calculate_checksum(data):
    return hashlib.md5(data).hexdigest()

def handle_list(server_socket, client_addr):
    with open(FILE_LIST, "rb") as f:
        server_socket.sendto(f.read(), client_addr)

def handle_download(server_socket, client_addr, filename):
    filepath = os.path.join(FILE_DIR, filename)
    if not os.path.exists(filepath):
        server_socket.sendto(b"ERROR: File not found", client_addr)
        return

    with open(filepath, "rb") as file:
        seq_num = 0
        while True:
            data = file.read(CHUNK_SIZE)
            if not data:
                break

            checksum = calculate_checksum(data)
            packet = f"{seq_num}|{checksum}|".encode() + data
            server_socket.sendto(packet, client_addr)

            # Wait for acknowledgment
            while True:
                try:
                    server_socket.settimeout(ACK_TIMEOUT)
                    ack, addr = server_socket.recvfrom(1024)
                    if ack.decode() == f"ACK:{seq_num}":
                        break  # Successfully received ACK
                    else:
                        print(f"Received wrong ACK for chunk {seq_num}, expected {seq_num}.")
                except socket.timeout:
                    print(f"Timeout on chunk {seq_num}, resending...")
                    server_socket.sendto(packet, client_addr)  # Resend the packet

            seq_num += 1

    server_socket.sendto(b"END", client_addr)  # Indicate end of transmission

def handle_client(server_socket, data, client_addr):
    command, *args = data.decode().split()
    if command == "LIST":
        handle_list(server_socket, client_addr)
    elif command == "DOWNLOAD":
        filename = args[0]
        handle_download(server_socket, client_addr, filename)

def update_file_list():
    with open(FILE_LIST, "w") as f:
        for filename in os.listdir(FILE_DIR):
            filepath = os.path.join(FILE_DIR, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                f.write(f"{filename} {size}\n")

def server_main():
    update_file_list()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}...")

    while True:
        try:
            data, client_addr = server_socket.recvfrom(2048)
            client_thread = threading.Thread(target=handle_client, args=(server_socket, data, client_addr))
            client_thread.start()
        except socket.timeout:
            print("Waiting for clients...")  # Handle timeout gracefully
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    os.makedirs(FILE_DIR, exist_ok=True)
    try:
        server_main()
    except KeyboardInterrupt:
        print("Server exited.")
