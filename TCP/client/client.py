import argparse
import socket
import threading
import os
import time
from tqdm import tqdm  

DOWNLOAD_DIR = "downloads"
INPUT_FILE = "input.txt"  # wanted files
socket_art = """
     .d8888b.                    888               888    
    d88P  Y88b                   888               888    
    Y88b.                        888               888    
     "Y888b.    .d88b.   .d8888b 888  888  .d88b 888888 
        "Y88b. d88""88b d88P"    888 .88P d8P  Y8b 888    
          "888 888  888 888      888888K  88888888 888    
    Y88b  d88P Y88..88P Y88b.    888 "88b Y8b.     Y88b.  
     "Y8888P"   "Y88P"   "Y8888P 888  888  "Y8888  "Y888 
     """
# A set to avoid redownload file
downloaded_files = set()

def fetch_file_list(server_host, server_port):
    """
    Send a LIST command for server, server then gives the client the file_list.txt which will be parsed for filenames and their sizes
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_host, server_port))
    client.sendall(b"LIST")  # LIST command
    
    # Client recieves file_list.txt
    with open("file_list.txt", "wb") as f:
        while True:
            data = client.recv(1024)
            if not data:
                break
            f.write(data)
    client.close()

    # Parse file_list.txt to obtain filenames and their sizes
    
    files = {} # A dictionary {filename:size}
    with open("file_list.txt", "r") as f:
        for line in f:
            filename, size = line.strip().split()
            files[filename] = int(size)  # Update dictionary
    return files

def read_input_file():
    """
    Read INPUT_FILE and get wanted filenames
    """
    input_files = []
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "r") as f:
            for line in f:
                filename = line.strip()
                if filename:  # skip blank lines
                    input_files.append(filename)
    return input_files
 
def display_available_files(files):
    """Display available files and their sizes."""
    print("\n===== Available Files =====")
    print(f"{'Filename':<20} Size (bytes)")
    print("-" * 35)
    
    for filename, size in files.items():
        # Format size with comma separators for readability
        formatted_size = f"{size:,}"
        print(f"{filename:<20} {formatted_size}")
    
    print("\n=== Total Files: {} ===".format(len(files)))
    print("To download, add filenames to input.txt, one per line.")

def download_chunk(filename, offset, chunk_size, part, total_parts, server_host, server_port):
    """
    Client sends a DOWNLOAD command with arguments : filename, chunksize, partNumber, totalPart
    Server will begins downloading the requested chunk(s)
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_host, server_port))
    client.sendall(f"DOWNLOAD {filename} {offset} {chunk_size}".encode())
    
    # Create temporary part files
    with open(f"{DOWNLOAD_DIR}/{filename}.part{part}", "wb") as f:
        with tqdm(total=chunk_size, unit="B", unit_scale=True, desc=f"{filename} part {part}/{total_parts}", leave=True) as pbar:
            while True:
                data = client.recv(1024)
                if not data:
                    break
                f.write(data)
                pbar.update(len(data))  # Progressbar handling
    client.close()


def merge_file(filename, total_parts):
    """
    Merge file from the temporary part files
    """
    with open(f"{DOWNLOAD_DIR}/{filename}", "wb") as f:
        for part in range(1, total_parts + 1):
            part_path = f"{DOWNLOAD_DIR}/{filename}.part{part}"
            with open(part_path, "rb") as part_file:
                f.write(part_file.read())
            os.remove(part_path)  # deleted merged chunks
    print(f"File {filename} has been merged successfully.")

def download_file(filename, file_size, server_host, server_port):
    """
    Split file into 4 chunks, with the last chunk holds the remaining bytes
    For example : 
    test.zip has 102 bytes
    test.zip.part 1: 25 bytes
    test.zip.part 2: 25 bytes
    test.zip.part 3: 25 bytes
    test.zip.part 4: 27 bytes
    """
    chunk_size = file_size // 4
    threads = []

    for i in range(4):
        offset = i * chunk_size
        if i == 3:  # Last chunk takes the remaining bytes
            chunk_size = file_size - offset
        part = i + 1
        # create thread to download chunk
        t = threading.Thread(target=download_chunk, args=(filename, offset, chunk_size, part, 4, server_host, server_port))
        threads.append(t)
        t.start()

    # Wait for all threads to finish downloading
    for t in threads:
        t.join()
    
    # Merge chunks into completed file
    merge_file(filename, 4)
    print(f"[+] Downloaded {filename} successfully!")

def client_main(server_host, server_port):
    """
    Main client loop: only download wanted files in INPUT_FILE.
    """
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # get file list from the server (file_list.txt)
    server_files = fetch_file_list(server_host, server_port)
    files_displayed = False
    
    while True:
        # get filenames from INPUT_FILE (input.txt)
        input_files = read_input_file()
        
        if not input_files and not files_displayed:
            display_available_files(server_files)
            files_displayed = True
        
        for filename in input_files:
            # Only download available and not yet downloaded file
            if filename in server_files and filename not in downloaded_files:
                print(f"[!] Starting download for: {filename} ({server_files[filename]} bytes)")
                download_file(filename, server_files[filename], server_host, server_port)
                downloaded_files.add(filename)

        # Wait 5s after checking INPUT_FILE for additional file(s)
        time.sleep(5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP Client")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server IP address")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    args = parser.parse_args()
    print(socket_art)
    try:
        client_main(args.host, args.port)
    except KeyboardInterrupt:
        os.remove("file_list.txt") # delete file_list.txt of client
        print("\nClient exited.")
