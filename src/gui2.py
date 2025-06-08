# --- START OF FILE gui2.py (FINAL - Path Aware Version) ---

import os
import shutil
import requests
import socket
import threading
import tempfile
import webbrowser
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import cgi
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

from pyngrok import ngrok, conf

# --- PATH CONFIGURATION (This is the main change) ---
# Get the directory where this script is located (e.g., .../project/src)
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project's root directory (one level up from 'src')
ROOT_DIR = os.path.dirname(SRC_DIR)

# ### CHANGE: Base all paths on the project's ROOT_DIR ###
RECEIVE_DIRECTORY = os.path.join(ROOT_DIR, 'receive')
CONFIG_FILE = os.path.join(ROOT_DIR, 'config.json')

# --- SETUP ---
if not os.path.exists(RECEIVE_DIRECTORY):
    os.makedirs(RECEIVE_DIRECTORY)

# --- SERVER LOGIC (No changes needed here, it now gets the path correctly) ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # This handler will be correctly configured by the factory
        self.receive_directory = kwargs.pop('receive_directory', RECEIVE_DIRECTORY)
        self.app = kwargs.pop('app', None)
        super().__init__(*args, **kwargs)
    def do_POST(self):
        try:
            ctype, pdict = cgi.parse_header(self.headers['Content-Type'])
            if ctype == 'multipart/form-data':
                pdict['boundary'] = bytes(pdict['boundary'], "utf-8"); pdict['CONTENT-LENGTH'] = int(self.headers['Content-Length']); fields = cgi.parse_multipart(self.rfile, pdict)
                file_data = fields.get('file')[0]; file_name = self.headers.get('file-name', 'uploaded_file'); file_path = os.path.join(self.receive_directory, os.path.basename(file_name))
                with open(file_path, 'wb') as f: f.write(file_data)
                self.send_response(200); self.end_headers(); self.wfile.write(b'File received successfully')
                if self.app: self.app.root.after(0, self.app.update_status, f"Received file: {file_name}")
            else:
                self.send_response(400); self.end_headers(); self.wfile.write(b'Bad request')
        except Exception as e:
            self.send_response(500); self.end_headers(); self.wfile.write(f'Server error: {e}'.encode('utf-8'))

# (The rest of the code is exactly the same, only the handler_factory needs the fix)
def get_local_ip():
    try: s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(0); s.connect(('10.254.254.254', 1)); ip = s.getsockname()[0]; s.close(); return ip
    except Exception: return "127.0.0.1"
def compress_folder_to_temp(folder_path):
    temp_dir = tempfile.gettempdir(); base_name = os.path.join(temp_dir, os.path.basename(folder_path)); return shutil.make_archive(base_name, 'zip', folder_path)
def upload_file(file_path, url):
    with open(file_path, 'rb') as f: files = {'file': (os.path.basename(file_path), f)}; headers = {'file-name': os.path.basename(file_path)}; return requests.post(url, files=files, headers=headers, timeout=300)

class FileTransferApp:
    def __init__(self, root):
        self.root = root; self.root.title("Simple File Transfer"); self.root.geometry("450x450")
        self.selected_path = None; self.httpd = None; self.server_thread = None; self.public_url = None
        self.user_authtoken = ""; self.load_config()
        self.mode_var = tk.StringVar(value="server"); mode_frame = tk.Frame(self.root)
        tk.Radiobutton(mode_frame, text="Server (Receive)", variable=self.mode_var, value="server", command=self.update_mode).pack(side="left", padx=10)
        tk.Radiobutton(mode_frame, text="Client (Send)", variable=self.mode_var, value="client", command=self.update_mode).pack(side="left", padx=10)
        mode_frame.pack(pady=10)
        self.server_frame = tk.LabelFrame(self.root, text="Server Controls", padx=10, pady=10)
        tk.Label(self.server_frame, text="Local Port:").pack(); self.port_entry = tk.Entry(self.server_frame); self.port_entry.insert(0, "8000"); self.port_entry.pack(pady=(0, 10))
        ngrok_frame = tk.Frame(self.server_frame)
        tk.Button(ngrok_frame, text="Configure API Key", command=self.configure_ngrok).pack(side="left", padx=5)
        tk.Button(ngrok_frame, text="Get API Key (Help)", command=lambda: webbrowser.open("https://dashboard.ngrok.com/get-started/your-authtoken")).pack(side="left", padx=5)
        ngrok_frame.pack(pady=5)
        self.server_button = tk.Button(self.server_frame, text="Start Server", command=self.toggle_server); self.server_button.pack(pady=10)
        self.share_frame = tk.Frame(self.server_frame)
        self.share_url_label = tk.Label(self.share_frame, text="", fg="blue", wraplength=350); self.share_url_label.pack(side="left", padx=(0, 5))
        self.copy_url_button = tk.Button(self.share_frame, text="Copy", command=self.copy_url, state=tk.DISABLED); self.copy_url_button.pack(side="left")
        self.client_frame = tk.LabelFrame(self.root, text="Client Controls", padx=10, pady=10)
        tk.Label(self.client_frame, text="Address or URL (from receiver):").pack(); self.url_entry = tk.Entry(self.client_frame, width=45); self.url_entry.pack(pady=5)
        tk.Label(self.client_frame, text="Port (only if using an IP address):").pack(); self.client_port_entry = tk.Entry(self.client_frame); self.client_port_entry.insert(0, "8000"); self.client_port_entry.pack(pady=5)
        select_buttons_frame = tk.Frame(self.client_frame)
        tk.Button(select_buttons_frame, text="Select File", command=self.select_file).pack(side="left", padx=5)
        tk.Button(select_buttons_frame, text="Select Folder", command=self.select_folder).pack(side="left", padx=5)
        select_buttons_frame.pack(pady=10)
        self.selected_path_label = tk.Label(self.client_frame, text="No file/folder selected.", wraplength=350); self.selected_path_label.pack(pady=5)
        self.upload_button = tk.Button(self.client_frame, text="Upload", command=self.upload, state=tk.DISABLED); self.upload_button.pack(pady=10)
        self.status_bar = tk.Label(self.root, text="Welcome!", bd=1, relief=tk.SUNKEN, anchor=tk.W); self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_mode(); self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f: self.user_authtoken = json.load(f).get('authtoken', '')
            except (json.JSONDecodeError, IOError): self.user_authtoken = ''
    def save_config(self):
        with open(CONFIG_FILE, 'w') as f: json.dump({'authtoken': self.user_authtoken}, f, indent=4)
    def update_status(self, message): self.status_bar.config(text=message)
    def update_mode(self):
        if self.mode_var.get() == "server": self.server_frame.pack(fill="x", padx=10, pady=5); self.client_frame.pack_forget(); self.share_frame.pack_forget(); self.update_status("Server mode. Configure API Key for public sharing.")
        else: self.server_frame.pack_forget(); self.client_frame.pack(fill="x", padx=10, pady=5); self.update_status("Client mode. Enter address and select a file to send.")
    def copy_url(self):
        text_to_copy = self.share_url_label.cget("text");
        if text_to_copy: self.root.clipboard_clear(); self.root.clipboard_append(text_to_copy); self.update_status("Address copied to clipboard!")
    def configure_ngrok(self):
        new_token = simpledialog.askstring("Configure ngrok API Key", "Please enter your ngrok API Key (authtoken):", initialvalue=self.user_authtoken, parent=self.root)
        if new_token is not None:
            new_token = new_token.strip()
            if new_token != self.user_authtoken:
                try: ngrok.set_auth_token(new_token); self.user_authtoken = new_token; self.save_config(); messagebox.showinfo("Success", "ngrok API Key saved successfully!")
                except Exception as e: messagebox.showerror("Error", f"Failed to save ngrok API Key: {e}")
    def toggle_server(self):
        if self.httpd: self.stop_server()
        else: self.start_server()

    def start_server(self):
        if self.user_authtoken:
            try:
                port = int(self.port_entry.get())
                # ### FIX: This now uses the global RECEIVE_DIRECTORY which is correctly calculated ###
                handler_factory = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, receive_directory=RECEIVE_DIRECTORY, app=self, **kwargs)
                self.httpd = HTTPServer(('', port), handler_factory)
                self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
                self.server_thread.start()
                self.server_button.config(text="Stop Server")
                self.update_status("Starting public tunnel via ngrok...")
                def start_ngrok_tunnel():
                    try: self.public_url = ngrok.connect(port, "http").public_url; self.root.after(0, self.on_address_ready, self.public_url, False)
                    except Exception as e:
                        self.root.after(0, lambda e=e: messagebox.showerror("ngrok Error", f"Failed to start ngrok tunnel:\n\n{e}\n\nYour API Key might be invalid."))
                        self.root.after(0, self.stop_server)
                threading.Thread(target=start_ngrok_tunnel, daemon=True).start()
            except Exception as e: messagebox.showerror("Error", f"Could not start local server:\n{e}")
        else:
            messagebox.showinfo("Local Network Mode", "No API Key found. Server will start in Local Network (LAN) mode.", parent=self.root)
            try:
                port = int(self.port_entry.get())
                handler_factory = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, receive_directory=RECEIVE_DIRECTORY, app=self, **kwargs)
                self.httpd = HTTPServer(('', port), handler_factory)
                self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
                self.server_thread.start()
                self.server_button.config(text="Stop Server")
                self.root.after(0, lambda: self.on_address_ready(f"{get_local_ip()}:{port}", True))
            except Exception as e: messagebox.showerror("Error", f"Could not start local server:\n{e}")

    def on_address_ready(self, address, is_lan):
        if is_lan: self.update_status("Server running in Local Network (LAN) mode.")
        else: self.update_status("Server running with Public URL.")
        self.share_url_label.config(text=address); self.copy_url_button.config(state=tk.NORMAL); self.share_frame.pack(pady=10)

    def stop_server(self):
        if self.public_url:
            try: ngrok.disconnect(self.public_url)
            except Exception: pass
            self.public_url = None
        if self.httpd:
            try: self.httpd.shutdown(); self.httpd.server_close()
            except Exception: pass
            self.httpd = None
        self.server_button.config(text="Start Server"); self.update_status("Server stopped.")
        self.share_frame.pack_forget(); self.copy_url_button.config(state=tk.DISABLED)

    # (The rest of the functions are unchanged)
    def upload(self):
        if not self.selected_path: messagebox.showerror("Error", "Please select a file or folder first."); return
        address = self.url_entry.get().strip(); port = self.client_port_entry.get().strip()
        if not address: messagebox.showerror("Error", "Address or URL cannot be empty."); return
        if address.startswith("http"): url = address
        else:
            if not port: messagebox.showerror("Error", "Port is required when using an IP address."); return
            url = f"http://{address}:{port}"
        self.upload_button.config(state=tk.DISABLED); self.update_status("Starting upload...")
        threading.Thread(target=self.perform_upload, args=(url,), daemon=True).start()
    def perform_upload(self, url):
        temp_zip_path = None
        try:
            path_to_upload = self.selected_path
            if os.path.isdir(self.selected_path): self.root.after(0, self.update_status, "Compressing folder..."); temp_zip_path = compress_folder_to_temp(self.selected_path); path_to_upload = temp_zip_path
            self.root.after(0, self.update_status, f"Uploading {os.path.basename(path_to_upload)}..."); response = upload_file(path_to_upload, url)
            if 200 <= response.status_code < 300: self.root.after(0, messagebox.showinfo, "Success", "Upload successful!"); self.root.after(0, self.update_status, "Upload complete.")
            else: self.root.after(0, messagebox.showerror, "Error", f"Upload failed: {response.status_code}\n{response.text}"); self.root.after(0, self.update_status, "Upload failed.")
        except requests.exceptions.RequestException as e: self.root.after(0, messagebox.showerror, "Connection Error", f"Could not connect:\n{e}"); self.root.after(0, self.update_status, "Connection failed.")
        except Exception as e: self.root.after(0, messagebox.showerror, "Error", f"An unexpected error occurred:\n{e}"); self.root.after(0, self.update_status, "An error occurred.")
        finally:
            if temp_zip_path and os.path.exists(temp_zip_path): os.remove(temp_zip_path)
            self.root.after(0, lambda: self.upload_button.config(state=tk.NORMAL))
    def on_closing(self):
        if self.httpd: self.stop_server()
        ngrok.kill(); self.root.destroy()
    def select_file(self):
        self.selected_path = filedialog.askopenfilename()
        if self.selected_path: self.selected_path_label.config(text=os.path.basename(self.selected_path)); self.upload_button.config(state=tk.NORMAL)
    def select_folder(self):
        self.selected_path = filedialog.askdirectory()
        if self.selected_path: self.selected_path_label.config(text=os.path.basename(self.selected_path)); self.upload_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = FileTransferApp(root)
    root.mainloop()