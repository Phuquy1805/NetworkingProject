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
   cd server
   python server.py
   ```
* Trên máy client 
   ```bash
   cd client
   python client.py
   ```
Ghi các tên file client cần tải vào ```client/input.txt```
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
  cd server
  python server.py
  ```
* Trên máy client 
  ```bash
  cd client
  python client.py
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
        Server->>Client: Chunk with Sequence Number & Checksum
        Note over Client: Verify Checksum
        alt Chunk Valid
            Client->>Server: ACK: Sequence Number
        else Chunk Corrupted
            Client->>Server: No ACK (Timeout)
        end
    end
    
    Client->>Server: DONE filename
    Server-->>Client: END transfer
```
### Demo video
 ***coming soon***
