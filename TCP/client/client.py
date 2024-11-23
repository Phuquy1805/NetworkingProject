import socket
import threading
import os
import time
import tqdm
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
DOWNLOAD_DIR = "downloads"
INPUT_FILE = "input.txt"  # File chứa danh sách các tệp cần tải

# Lưu các file đã tải để tránh tải lại
downloaded_files = set()

def fetch_file_list():
    """
    Kết nối tới server để tải file_list.txt, sau đó phân tích và trả về danh sách file.
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER_HOST, SERVER_PORT))
    client.sendall(b"LIST")  # Yêu cầu danh sách file
    
    # Nhận file_list.txt từ server
    with open("file_list.txt", "wb") as f:
        while True:
            data = client.recv(1024)
            if not data:
                break
            f.write(data)
    client.close()

    # Phân tích file_list.txt để lấy danh sách file và kích thước
    files = {}
    with open("file_list.txt", "r") as f:
        for line in f:
            filename, size = line.strip().split()
            files[filename] = int(size)  # Tạo dictionary {tên_file: kích_thước}
    return files

def read_input_file():
    """
    Đọc danh sách các tệp cần tải từ INPUT_FILE.
    """
    input_files = []
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "r") as f:
            for line in f:
                filename = line.strip()
                if filename:  # Bỏ qua dòng trống
                    input_files.append(filename)
    return input_files

from tqdm import tqdm  # Import tqdm for the progress bar

def download_chunk(filename, offset, chunk_size, part, total_parts):
    """
    Tải một phần (chunk) của file từ server với thanh tiến trình.
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER_HOST, SERVER_PORT))
    client.sendall(f"DOWNLOAD {filename} {offset} {chunk_size}".encode())
    
    # Ghi dữ liệu chunk vào file tạm thời
    with open(f"{DOWNLOAD_DIR}/{filename}.part{part}", "wb") as f:
        with tqdm(total=chunk_size, unit="B", unit_scale=True, desc=f"{filename} part {part}/{total_parts}", leave=True) as pbar:
            while True:
                data = client.recv(1024)
                if not data:
                    break
                f.write(data)
                pbar.update(len(data))  # Cập nhật tiến trình
    client.close()
    # print(f"Completed downloading {filename} part {part}/{total_parts}")


def merge_file(filename, total_parts):
    """
    Ghép các chunk thành file hoàn chỉnh.
    """
    with open(f"{DOWNLOAD_DIR}/{filename}", "wb") as f:
        for part in range(1, total_parts + 1):
            part_path = f"{DOWNLOAD_DIR}/{filename}.part{part}"
            with open(part_path, "rb") as part_file:
                f.write(part_file.read())
            os.remove(part_path)  # Xóa file chunk sau khi ghép xong
    print(f"File {filename} đã được ghép thành công.")

def download_file(filename, file_size):
    """
    Chia file thành 4 chunk, tải xuống song song và ghép lại.
    """
    chunk_size = file_size // 4
    threads = []

    for i in range(4):
        offset = i * chunk_size
        part = i + 1
        # Tạo thread để tải chunk
        t = threading.Thread(target=download_chunk, args=(filename, offset, chunk_size, part, 4))
        threads.append(t)
        t.start()

    # Chờ tất cả các thread tải xong
    for t in threads:
        t.join()
    
    # Ghép các chunk thành file hoàn chỉnh
    merge_file(filename, 4)
    print(f"Downloaded {filename} successfully!")

def client_main():
    """
    Vòng lặp chính của client: chỉ tải các file có trong INPUT_FILE.
    """
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    while True:
        # Lấy danh sách file từ server
        server_files = fetch_file_list()

        # Lấy danh sách file cần tải từ INPUT_FILE
        input_files = read_input_file()

        for filename in input_files:
            # Chỉ tải nếu file nằm trong danh sách server và chưa tải
            if filename in server_files and filename not in downloaded_files:
                print(f"Starting download for: {filename} ({server_files[filename]} bytes)")
                download_file(filename, server_files[filename])
                downloaded_files.add(filename)

        # Chờ 5 giây trước khi kiểm tra lại danh sách file
        time.sleep(5)

if __name__ == "__main__":
    try:
        client_main()
    except KeyboardInterrupt:
        print("\nClient exited.")
