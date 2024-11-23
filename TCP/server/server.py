import socket
import threading
import os
import tqdm
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
FILE_DIR = "server_files"
FILE_LIST = "file_list.txt"

def handle_client(client_socket):
    try:
        request = client_socket.recv(1024).decode()
        command, *args = request.split()

        if command == "LIST":
            # Gửi file_list.txt về client
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
    # Cập nhật file_list.txt với các file và kích thước
    with open(FILE_LIST, "w") as f:
        for filename in os.listdir(FILE_DIR):
            filepath = os.path.join(FILE_DIR, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                f.write(f"{filename} {size}\n")

def server_main():
    update_file_list()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen(5)
    print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}...")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr}")
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    try:
        os.makedirs(FILE_DIR, exist_ok=True)
        server_main()
    except KeyboardInterrupt:
        print("Server exited.")
