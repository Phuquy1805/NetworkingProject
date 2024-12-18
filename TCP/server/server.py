import argparse
import socket
import threading
import os

FILE_DIR = "server_files"
FILE_LIST = "file_list.txt"

def handle_client(client_socket):
    try:
        request = client_socket.recv(1024).decode()
        command, *args = request.split()

        if command == "LIST":
            # Send file_list.txt to client
            with open(FILE_LIST, "rb") as f:
                client_socket.sendall(f.read())

        elif command == "DOWNLOAD":
            filename, offset, chunk_size = args
            offset = int(offset)
            chunk_size = int(chunk_size)
            filepath = os.path.join(FILE_DIR, filename)

            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    f.seek(offset)
                    data = f.read(chunk_size)
                    client_socket.sendall(data)
            else:
                client_socket.sendall(b"ERROR: File not found")
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()
        

def update_file_list():
    # Update file_list.txt with file and file's size
    with open(FILE_LIST, "w") as f:
        for filename in os.listdir(FILE_DIR):
            filepath = os.path.join(FILE_DIR, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                f.write(f"{filename} {size}\n")

def server_main(server_host, server_port):
    update_file_list()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_host, server_port))
    server.listen(5)
    print(f"Server listening on {server_host}:{server_port}...")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr}")
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server IP address")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    args = parser.parse_args()
    try:
        os.makedirs(FILE_DIR, exist_ok=True)
        server_main(args.host, args.port)
    except KeyboardInterrupt:
        print("Server exited.")
