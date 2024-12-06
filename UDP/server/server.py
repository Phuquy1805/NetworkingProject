import socket
import os
import threading
import hashlib
from tqdm import tqdm

# Server configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
FILE_DIR = "server_files"
FILE_LIST = "file_list.txt"
CHUNK_SIZE = 50 * 1024  # Chunk size of 50 KB
WINDOW_SIZE = 5          # Number of chunks that can be in flight simultaneously
ACK_TIMEOUT = 5          # Timeout in seconds for waiting for ACKs before retransmission

def calculate_checksum(data):
    """Calculate the MD5 checksum of the given data."""
    return hashlib.md5(data).hexdigest()

def update_file_list():
    """Update the list of files in FILE_DIR and save to FILE_LIST."""
    with open(FILE_LIST, "w") as f:
        for filename in os.listdir(FILE_DIR):
            filepath = os.path.join(FILE_DIR, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                f.write(f"{filename} {size}\n")  # Write filename and size to file

def handle_get_chunk_size(server_socket, client_addr, filename):
    """Send the current CHUNK_SIZE to the client."""
    server_socket.sendto(str(CHUNK_SIZE).encode(), client_addr)

def handle_list(server_socket, client_addr):
    """Send the list of available files to the client."""
    with open(FILE_LIST, "rb") as f:
        server_socket.sendto(f.read(), client_addr)

def handle_download(server_socket, client_addr, filename):
    """Handle file download request from the client."""
    filepath = os.path.join(FILE_DIR, filename)
    if not os.path.exists(filepath):
        server_socket.sendto(b"ERROR: File not found", client_addr)
        return

    file_size = os.path.getsize(filepath)
    total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
    print(f"Starting download of {filename}, Size: {file_size} bytes, Chunks: {total_chunks}")

    sent_chunks = {}
    acked_chunks = set()
    window_start = 0

    # Initialize a loading bar for tracking download progress
    loading_bar = tqdm(total=total_chunks, desc=f"Downloading {filename}", unit="chunk")

    def resend_chunk(seq_num):
        """Resend a specific chunk if it hasn't been acknowledged."""
        if seq_num in sent_chunks and seq_num not in acked_chunks:
            server_socket.sendto(sent_chunks[seq_num], client_addr)
            print(f"Resending chunk {seq_num}")

    def wait_for_ack():
        """Wait for ACKs from the client and update the loading bar."""
        while len(acked_chunks) < total_chunks:
            try:
                server_socket.settimeout(ACK_TIMEOUT)
                ack, _ = server_socket.recvfrom(1024)
                
                if ack.startswith(b"ACK:"):    
                    seq_num = int(ack.split(b":")[1])
                    acked_chunks.add(seq_num)
                    loading_bar.update(1)  # Update the loading bar on receiving an ACK
                    
                elif ack.startswith(b"DONE:"):
                    print(f"Client finished receiving {filename}.")
                    break  # Stop waiting for more ACKs
            except socket.timeout:
                # Resend unacknowledged chunks
                for seq in range(window_start, min(window_start + WINDOW_SIZE, total_chunks)):
                    resend_chunk(seq)

    # Start a thread to listen for ACKs
    ack_thread = threading.Thread(target=wait_for_ack, daemon=True)
    ack_thread.start()

    # Main loop for sending chunks
    while window_start < total_chunks:
        for seq in range(window_start, min(window_start + WINDOW_SIZE, total_chunks)):
            if seq in acked_chunks:
                continue  # Skip already acknowledged chunks

            # Read and send the chunk
            with open(filepath, "rb") as file:
                file.seek(seq * CHUNK_SIZE)  # Move to the correct chunk
                chunk_data = file.read(CHUNK_SIZE)
                checksum = calculate_checksum(chunk_data)
                packet = f"{seq}|{checksum}|".encode() + chunk_data  # Create the packet
                sent_chunks[seq] = packet
                server_socket.sendto(packet, client_addr)  # Send the packet

        # Update the window_start to the next unacknowledged chunk
        while window_start in acked_chunks:
            window_start += 1

    ack_thread.join()  # Wait for the ACK thread to finish
    loading_bar.close()  # Close the loading bar after completion
    server_socket.sendto(b"END", client_addr)  # Signal the end of the transfer

def handle_client(server_socket, data, client_addr):
    """Handle incoming client requests."""
    command, *args = data.decode().split()
    if command == "LIST":
        handle_list(server_socket, client_addr)  # Handle LIST command
    elif command == "DOWNLOAD":
        filename = args[0]
        handle_download(server_socket, client_addr, filename)  # Handle DOWNLOAD command
    elif command == "GET_CHUNK_SIZE":
        filename = args[0]
        handle_get_chunk_size(server_socket, client_addr, filename)  # Handle GET_CHUNK_SIZE command

def server_main():
    """Main server loop to handle incoming connections."""
    update_file_list()  # Update the file list at startup
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a UDP socket
    server_socket.bind((SERVER_HOST, SERVER_PORT))  # Bind the socket to the host and port
    print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}...")

    while True:
        try:
            data, client_addr = server_socket.recvfrom(2048)  # Receive data from clients
            # Start a new thread to handle the client request
            threading.Thread(target=handle_client, args=(server_socket, data, client_addr), daemon=True).start()
        except socket.timeout:
            print("Waiting for client...")

if __name__ == "__main__":
    os.makedirs(FILE_DIR, exist_ok=True)  # Create the file directory if it doesn't exist
    try:
        server_main()  # Start the server
    except KeyboardInterrupt:
        print("\nServer exited.")  # Handle server exit on Ctrl+C
