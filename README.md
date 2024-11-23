# Socket Programming Project 2024


## Trường Đại học Khoa học Tự nhiên - Đại học Quốc gia TPHCM (HCMUS - VNU)

## Bộ môn Mạng máy tính (Computer Networking)
### Members :
* Nguyễn Trần Phú Quý - 23127113
* Nguyễn Hải Đăng - 
* Lê Nhật Khôi -
### Content : 
## Problem 1 : Using TCP to download files

Set up : 
* Tải các thư viện cần thiết
    ```bash
   pip install -r requirements.txt
   ```
* Tạo thư mục ```server/server_files/``` và add file mà client muốn tải vào đó
* Chạy file python sau để tạo ```server/file_list.txt``` chứa các tên file và dung lượng 
   ```bash
   python server/create_file_list.py
   ```

* Edit file ```input.txt``` của client
* Trên máy server
   ```bash
   python server/server.py
   ```
   Trên máy client 
   ```bash
   python client/client.py
   ```
