import socket
import os
import time
import hashlib

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
DOWNLOAD_DIR = "downloads"
INPUT_FILE = "input.txt"

downloaded_files = set()

def calculate_checksum(data):
    return hashlib.md5(data).hexdigest()

def fetch_file_list():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(b"LIST", (SERVER_HOST, SERVER_PORT))

    file_list_data, _ = client_socket.recvfrom(4096)
    with open("file_list.txt", "wb") as f:
        f.write(file_list_data)

    files = {}
    with open("file_list.txt", "r") as f:
        for line in f:
            filename, size = line.strip().split()
            files[filename] = int(size)
    return files

def download_file(filename, file_size):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(f"DOWNLOAD {filename}".encode(), (SERVER_HOST, SERVER_PORT))

    received_data = {}
    while True:
        packet, _ = client_socket.recvfrom(2048)
        if packet == b"END":
            break

        seq, checksum, data = packet.split(b"|", 2)
        seq = int(seq.decode())
        checksum = checksum.decode()

        if calculate_checksum(data) == checksum:
            received_data[seq] = data
            client_socket.sendto(f"ACK:{seq}".encode(), (SERVER_HOST, SERVER_PORT))
        else:
            print(f"Corrupted chunk {seq}, requesting retransmission...")

    # Write the complete file
    with open(os.path.join(DOWNLOAD_DIR, filename), "wb") as f:
        for seq in sorted(received_data.keys()):
            f.write(received_data[seq])

    print(f"Downloaded {filename} successfully!")

def client_main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    server_files = fetch_file_list()

    while True:
        input_files = []
        if os.path.exists(INPUT_FILE):
            with open(INPUT_FILE, "r") as f:
                input_files = [line.strip() for line in f if line.strip()]

        for filename in input_files:
            if filename in server_files and filename not in downloaded_files:
                print(f"Starting download for: {filename}")
                download_file(filename, server_files[filename])
                downloaded_files.add(filename)
        time.sleep(5)

if __name__ == "__main__":
    try:
        client_main()
    except KeyboardInterrupt:
        print("\nClient exited.")
