import os
import shutil
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
import cgi
import tkinter as tk
from tkinter import filedialog, messagebox

RECEIVE_DIRECTORY = 'receive'

if not os.path.exists(RECEIVE_DIRECTORY):
    os.makedirs(RECEIVE_DIRECTORY)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers['Content-Type'])
        if ctype == 'multipart/form-data':
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            pdict['CONTENT-LENGTH'] = int(self.headers['Content-Length'])
            fields = cgi.parse_multipart(self.rfile, pdict)
            file_data = fields.get('file')[0]
            file_name = self.headers['file-name']
            file_path = os.path.join(RECEIVE_DIRECTORY, file_name)
            with open(file_path, 'wb') as f:
                f.write(file_data)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'File received')
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Bad request')

    def do_GET(self):
        file_name = self.path.strip("/")
        file_path = os.path.join(RECEIVE_DIRECTORY, file_name)
        if os.path.exists(file_path):
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename={file_name}')
            self.end_headers()
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'File not found')

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f'Starting httpd server on port {port}...')
    httpd.serve_forever()

def compress_folder(folder_path, output_path):
    shutil.make_archive(output_path, 'zip', folder_path)

def upload_file(file_path, url):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files, headers={'file-name': os.path.basename(file_path)})
    os.remove(file_path)  # Remove the file after uploading
    return response

class FileTransferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Transfer App")
        
        self.mode_var = tk.StringVar(value="server")
        self.mode_frame = tk.Frame(self.root)
        self.server_radio = tk.Radiobutton(self.mode_frame, text="Server", variable=self.mode_var, value="server", command=self.update_mode)
        self.client_radio = tk.Radiobutton(self.mode_frame, text="Client", variable=self.mode_var, value="client", command=self.update_mode)
        self.server_radio.pack(side="left", padx=5)
        self.client_radio.pack(side="left", padx=5)
        self.mode_frame.pack(pady=10)
        
        self.server_frame = tk.Frame(self.root)
        self.port_label = tk.Label(self.server_frame, text="Port:")
        self.port_label.pack(pady=5)
        self.port_entry = tk.Entry(self.server_frame)
        self.port_entry.insert(0, "8000")
        self.port_entry.pack(pady=5)
        self.server_button = tk.Button(self.server_frame, text="Start Server", command=self.start_server)
        self.server_button.pack(pady=10)
        
        self.client_frame = tk.Frame(self.root)
        self.folder_button = tk.Button(self.client_frame, text="Select Folder to Upload", command=self.select_folder)
        self.folder_button.pack(pady=5)
        self.host_entry = tk.Entry(self.client_frame)
        self.host_entry.insert(0, "localhost")
        tk.Label(self.client_frame, text="Host:").pack(pady=5)
        self.host_entry.pack(pady=5)
        self.client_port_entry = tk.Entry(self.client_frame)
        self.client_port_entry.insert(0, "8000")
        tk.Label(self.client_frame, text="Port:").pack(pady=5)
        self.client_port_entry.pack(pady=5)
        self.upload_button = tk.Button(self.client_frame, text="Upload Folder", command=self.upload_folder)
        self.upload_button.pack(pady=5)
        
        self.update_mode()

    def update_mode(self):
        if self.mode_var.get() == "server":
            self.server_frame.pack(pady=10)
            self.client_frame.pack_forget()
        else:
            self.server_frame.pack_forget()
            self.client_frame.pack(pady=10)

    def start_server(self):
        port = int(self.port_entry.get())
        run_server(port=port)

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.selected_folder = folder_path

    def upload_folder(self):
        if hasattr(self, 'selected_folder'):
            output_zip = os.path.join(os.getcwd(), 'output_zip_file')
            compress_folder(self.selected_folder, output_zip)
            file_path = output_zip + '.zip'
            host = self.host_entry.get().strip()
            port = self.client_port_entry.get().strip()
            url = f"http://{host}:{port}"
            upload_file(file_path, url)
        else:
            messagebox.showerror("Error", "Please select a folder first.")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileTransferApp(root)
    root.mainloop()
