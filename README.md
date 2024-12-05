# Socket Programming Project 2024


## Trường Đại học Khoa học Tự nhiên - Đại học Quốc gia TPHCM (HCMUS - VNU)

## Bộ môn Mạng máy tính (Computer Networking)
### Members :
* Nguyễn Trần Phú Quý - 23127113
* Nguyễn Hải Đăng - 23127165
* Lê Nhật Khôi - 23127004
### Content : 
## Problem 1 : Using TCP to download files

 Tải các thư viện cần thiết
```bash
   pip install -r requirements.txt
```
Set up folder ```TCP```: 
```bash
cd TCP
```

* Tạo thư mục ```server/server_files/``` và add file mà client muốn tải vào đó
* Di chuyển vào đuongwf dẫn ```/server```
* Chạy file python sau để tạo ```file_list.txt``` chứa các tên file và dung lượng 
   ```bash
   python create_file_list.py
   ```

* Edit file ```client/input.txt``` của client
* Trên máy server
   ```bash
   cd server
   python server.py
   ```
   Trên máy client 
   ```bash
   cd client
   python client/client.py
   ```
