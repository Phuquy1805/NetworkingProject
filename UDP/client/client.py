import argparse
import socket
import os
import hashlib
import threading
import time

# Server configuration
DOWNLOAD_DIR = "downloads"
INPUT_FILE = "input.txt"
FILE_LIST = "file_list.txt"
socket_art = """
    ██╗   ██╗██████╗ ██████╗     
    ██║   ██║██╔══██╗██╔══██╗    
    ██║   ██║██║  ██║██████╔╝    
    ██║   ██║██║  ██║██╔═══╝     
    ╚██████╔╝██████╔╝██║         
     ╚═════╝ ╚═════╝ ╚═╝         

    ███████╗ ██████╗  ██████╗██╗  ██╗███████╗████████╗
    ██╔════╝██╔═══██╗██╔════╝██║ ██╔╝██╔════╝╚══██╔══╝
    ███████╗██║   ██║██║     █████╔╝ █████╗     ██║   
    ╚════██║██║   ██║██║     ██╔═██╗ ██╔══╝     ██║   
    ███████║╚██████╔╝╚██████╗██║  ██╗███████╗   ██║   
    ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝   ╚═╝ 
     """
# A set to avoid re-downloading files
downloaded_files = set()

def calculate_checksum(data):
    """Calculate and return the MD5 checksum of the given data."""
    return hashlib.md5(data).hexdigest()

def fetch_chunk_size(server_host, server_port):
    """Send a request to the server for the chunk size for a given filename."""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(f"GET_CHUNK_SIZE".encode(), (server_host, server_port))

    # Receive the chunk size from the server
    chunk_size_data, _ = client_socket.recvfrom(1024)
    return int(chunk_size_data.decode())

def fetch_file_list(server_host, server_port):
    """Request and receive the list of available files from the server."""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(b"LIST", (server_host, server_port))

    # Receive the file list from the server
    file_list_data, _ = client_socket.recvfrom(4096)

    # Parse the file list data
    files = {}
    for line in file_list_data.decode().splitlines():
        filename, size = line.strip().split()
        files[filename] = int(size)

    # Save the file list to a local file
    with open(FILE_LIST, "w") as f:
        for file in files:
            f.write(f"{file} {files[file]}\n")
    return files

def read_input_file():
    """Read INPUT_FILE and get the list of wanted filenames for download."""
    input_files = []
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "r") as f:
            for line in f:
                filename = line.strip()
                if filename:  # Skip blank lines
                    input_files.append(filename)
    return input_files

def display_available_files(files):
    """Display available files and their sizes with clean, minimal formatting."""
    
    def format_size(size_in_bytes):
        """Convert bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_in_bytes < 1024:
                return f"{size_in_bytes:.1f} {unit}"
            size_in_bytes /= 1024
        return f"{size_in_bytes:.1f} TB"
    
    # Colors (can be easily removed if not needed)
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # Header
    print(f"\n{BOLD}Available Files{RESET}")
    print("-" * 45)
    print(f"{BOLD}{'Filename':<30} {'Size':>12}{RESET}")
    print("-" * 45)
    
    # File listings
    for filename, size in sorted(files.items()):
        # Truncate filename if too long
        display_filename = filename if len(filename) <= 27 else filename[:27] + "..."
        human_size = format_size(size)
        print(f"{display_filename:<30} {human_size:>12}")
    
    # Footer
    print("-" * 45)
    print(f"{BOLD}Total Files: {len(files)}{RESET}")
    print(f"\nTo download: Add filenames to input.txt, one per line.\n")


def download_file(filename, file_size, server_host, server_port):
    """Download the specified file from the server."""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(f"DOWNLOAD {filename}".encode(), (server_host, server_port))

    # Calculate total chunks based on file size and chunk size
    total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
    received_chunks = {}
    
    
    def receive_chunks():
        """Receive file chunks from the server and send ACKs."""
        while True:
            packet, _ = client_socket.recvfrom(65535)
            if packet == b"END":
                print(f"[+] Downloaded {filename} successfully!")
                break

            try:
                seq, checksum, data = packet.split(b"|", 2)
                seq = int(seq.decode())
                checksum = checksum.decode()

                # Verify checksum before storing the chunk
                if calculate_checksum(data) == checksum:
                    received_chunks[seq] = data
                    client_socket.sendto(f"ACK:{seq}".encode(), (server_host, server_port))

                else:
                    print(f"[-] Corrupted chunk {seq}, requesting retransmission...")
            except Exception as e:
                print(f"Error processing packet: {e}")

    # Start a thread to receive chunks while main thread handles flow control
    threading.Thread(target=receive_chunks, daemon=True).start()

    # Wait until all chunks are received
    while len(received_chunks) < total_chunks:
        time.sleep(0.1)
    
    # Notify the server that the download is complete
    client_socket.sendto(f"DONE {filename}".encode(), (server_host, server_port))

    # Write the received chunks to a file
    with open(os.path.join(DOWNLOAD_DIR, filename), "wb") as f:
        for seq in range(total_chunks):
            f.write(received_chunks[seq])
    

def client_main(server_host, server_port):
    """Main function to control the client download process."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    server_files = fetch_file_list(server_host, server_port)
    
    # Fetch chunk size from server's end
    global CHUNK_SIZE
    CHUNK_SIZE = fetch_chunk_size(server_host, server_port)
    print(f"[!] Using chunk size: {CHUNK_SIZE} bytes")
    
    files_displayed = False
    while True:
        input_files = read_input_file()
        
        if not input_files and not files_displayed:
            display_available_files(server_files)
            files_displayed = True
            
        for filename in input_files:
            if filename in server_files and filename not in downloaded_files and not os.path.exists(os.path.join(DOWNLOAD_DIR, filename)):
                print(f"Starting download for: {filename}")
                download_file(filename, server_files[filename], server_host, server_port)
                downloaded_files.add(filename)
        # Wait 5 seconds after checking INPUT_FILE for additional files
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
        os.remove(FILE_LIST)
        print("\nClient exited.")