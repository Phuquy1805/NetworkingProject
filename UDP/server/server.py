import argparse
import socket
import os
import threading
import hashlib
import random

# Server configuration
FILE_DIR = "server_files"
FILE_LIST = "file_list.txt"
CHUNK_SIZE = 10 * 1024  
WINDOW_SIZE = 5          # Number of chunks that can be in flight simultaneously
ACK_TIMEOUT = 5          # Timeout in seconds for waiting for ACKs before retransmission
CORRUPTION_RATE = 0   # % of packets will be corrupted (for debug purposes)

def calculate_checksum(data):
    """Calculate the MD5 checksum of the given data."""
    return hashlib.md5(data).hexdigest()

def corrupt_packet(packet):
    """Simulate packet corruption by randomly modifying a byte."""
    if random.random() < CORRUPTION_RATE:
        packet_list = bytearray(packet)
        # Randomly choose a byte to modify
        corrupt_index = random.randint(0, len(packet_list) - 1)
        # Modify the byte
        packet_list[corrupt_index] = (packet_list[corrupt_index] + 1) % 256
        return bytes(packet_list)
    return packet

def update_file_list():
    """Update the list of files in FILE_DIR and save to FILE_LIST."""
    with open(FILE_LIST, "w") as f:
        for filename in os.listdir(FILE_DIR):
            filepath = os.path.join(FILE_DIR, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                f.write(f"{filename} {size}\n")  

def handle_get_chunk_size(server_socket, client_addr):
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

    def resend_chunk(seq_num):
        """Resend a specific chunk if it hasn't been acknowledged."""
        if seq_num in sent_chunks and seq_num not in acked_chunks:
            # Potentially corrupt the packet when resending
            packet = sent_chunks[seq_num]
            corrupted_packet = corrupt_packet(packet)
            server_socket.sendto(corrupted_packet, client_addr)
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
                    
                elif ack.startswith(b"DONE"):
                    print(f"Client finished receiving {filename}.")
                    break  
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
                continue  

            # Read and send the chunk
            with open(filepath, "rb") as file:
                file.seek(seq * CHUNK_SIZE)  
                chunk_data = file.read(CHUNK_SIZE)
                checksum = calculate_checksum(chunk_data)
                packet = f"{seq}|{checksum}|".encode() + chunk_data 
                
                # Potentially corrupt the packet
                corrupted_packet = corrupt_packet(packet)
                
                sent_chunks[seq] = packet
                server_socket.sendto(corrupted_packet, client_addr)  

        # Update the window_start to the next unacknowledged chunk
        while window_start in acked_chunks:
            window_start += 1
            
    # Wait for the ACK thread to finish
    ack_thread.join()  
    
    # Signal the end of the transfer
    server_socket.sendto(b"END", client_addr)  

def handle_client(server_socket, data, client_addr):
    """Handle incoming client requests."""
    command, *args = data.decode().split()
    if command == "LIST":
        handle_list(server_socket, client_addr)  
    elif command == "DOWNLOAD":
        filename = args[0]
        handle_download(server_socket, client_addr, filename)  
    elif command == "GET_CHUNK_SIZE":
        handle_get_chunk_size(server_socket, client_addr)  

def server_main(server_host, server_port):
    """Main server loop to handle incoming connections."""
    update_file_list()  
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
    server_socket.bind((server_host, server_port))  
    print(f"Server listening on {server_host}:{server_port}...")
    
    if CORRUPTION_RATE > 0:
        print(f"🚨 Packet Corruption Simulation Enabled ({CORRUPTION_RATE * 100}% corruption rate)")

    while True:
        try:
            data, client_addr = server_socket.recvfrom(2048) 
            # Start a new thread to handle the client request
            threading.Thread(target=handle_client, args=(server_socket, data, client_addr), daemon=True).start()
        except socket.timeout:
            print("Waiting for client...")

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="UDP Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server IP address")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    args = parser.parse_args()

    os.makedirs(FILE_DIR, exist_ok=True)  
    try:
        server_main(args.host, args.port)  
    except KeyboardInterrupt:
        print("\nServer exited.") 