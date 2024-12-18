# Socket Programming Project 2024


## Trường Đại học Khoa học Tự nhiên - Đại học Quốc gia TPHCM (HCMUS - VNU)

## Bộ môn Mạng máy tính (Computer Networking)
### Members :
* Nguyễn Trần Phú Quý - 23127113
* Nguyễn Hải Đăng - 23127165
* Lê Nhật Khôi - 23127004

### Content : 
Project : https://docs.google.com/document/d/1ART-HEw2Z0uDu-jkQ1kyZth6CaY6gXQgrOHWDCACGcE/edit?tab=t.0

 Tải các thư viện cần thiết
```bash
pip install -r requirements.txt
```
## Problem 1 : Using TCP to download files


### Set up 
```bash
cd TCP
```

* Tạo thư mục ```server/server_files/``` và add file mà client muốn tải vào đó
* Di chuyển vào đường dẫn ```/server```



* Trên máy server
  ```bash
  python server.py [-h] [--host HOST] [--port PORT]
  ```

* Trên máy client 
  ```bash
  python client.py [-h] [--host HOST] [--port PORT]
  ```
Ghi các tên file client cần tải vào ```client/input.txt```
### Comunication Diagram 
```mermaid
sequenceDiagram
    participant Client
    participant Server

    Client->>Server: LIST (Request file_list.txt)
    Server-->>Client: Send file_list.txt

    loop For each file in input.txt
        Client->>Server: DOWNLOAD <filename> Chunk 1 (offset: 0)
        Server-->>Client: Send Chunk 1

        Client->>Server: DOWNLOAD <filename> Chunk 2 (offset: size/4)
        Server-->>Client: Send Chunk 2

        Client->>Server: DOWNLOAD <filename> Chunk 3 (offset: size/2)
        Server-->>Client: Send Chunk 3

        Client->>Server: DOWNLOAD <filename> Chunk 4 (offset: remaining bytes)
        Server-->>Client: Send Chunk 4
    end

    Client->>Client: Merge all chunks
    Client->>Client: Save complete file to downloads/

```
### Demo video
***coming soon***
## Problem 2 : Using UDP to download files


### Set up
```bash
cd UDP
```
* Tạo thư mục ```server/server_files/``` và add file mà client muốn tải vào đó
* Di chuyển vào đường dẫn ```/server```



* Trên máy server
  ```bash
  python server.py [-h] [--host HOST] [--port PORT]
  ```

* Trên máy client 
  ```bash
  python client.py [-h] [--host HOST] [--port PORT]
  ```
Ghi các tên file client cần tải vào ```client/input.txt```
### Comunication Diagram 
```mermaid
sequenceDiagram
    participant Client
    participant Server
    
    # File List Request
    Client->>Server: LIST command
    Server-->>Client: file_list.txt content
    
    # Download Preparation
    Client->>Server: GET_CHUNK_SIZE
    Server-->>Client: Chunk Size (e.g., 10 kB)
    
    # File Download
    Client->>Server: DOWNLOAD filename
    loop Chunk Transfer
        Server->>Client: <sequence_number>|<checksum>|<chunk_data>
        Note over Client: Verify Checksum
        alt Chunk Valid
            Client->>Server: ACK: Sequence Number
        else Chunk Corrupted
            Client->>Server: No ACK (Timeout)
        end
    end
    
    Server-->>Client: END 
    Client->>Server: DONE 
```
### Demo video
 ***coming soon***
