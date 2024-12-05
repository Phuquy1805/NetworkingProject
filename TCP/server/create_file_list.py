import os

"""
Run this file when adding new file into the directory /server_files/ to automatically change file_list.txt
"""

def list_files_with_sizes(folder_path, output_file):
    try:
        with open(output_file, "w") as f:  # Open the output file in write mode
            files = os.listdir(folder_path)
            for file in files:
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    f.write(f"{file} {file_size}\n")  # Write each file name and size to the file
        print(f"File list saved to {output_file}")
    except Exception as e:
        print(f"Error: {e}")

# Replace 'your_folder_path_here' and 'output.txt' with the actual folder path and desired output file
folder_path = "server_files/"
output_file = "file_list.txt"
list_files_with_sizes(folder_path, output_file)
