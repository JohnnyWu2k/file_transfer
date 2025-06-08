# --- START OF FILE gui2.py (Corrected) ---

import os
import shutil
import requests
import socket
import threading
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
import cgi
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

# ### NEW: Import pyngrok ###
from pyngrok import ngrok, conf

# --- CONFIGURATION & SETUP ---
RECEIVE_DIRECTORY = 'receive'
if not os.path.exists(RECEIVE_DIRECTORY):
    os.makedirs(RECEIVE_DIRECTORY)

# --- SERVER & CLIENT LOGIC ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.app = kwargs.pop('app', None)
        super().__init__(*args, **kwargs)
    def do_POST(self):
        try:
            ctype, pdict = cgi.parse_header(self.headers['Content-Type'])
            if ctype == 'multipart/form-data':
                pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
                pdict['CONTENT-LENGTH'] = int(self.headers['Content-Length'])
                fields = cgi.parse_multipart(self.rfile, pdict)
                file_data = fields.get('file')[0]
                file_name = self.headers.get('file-name', 'uploaded_file')
                file_path = os.path.join(RECEIVE_DIRECTORY, os.path.basename(file_name))
                with open(file_path, 'wb') as f: f.write(file_data)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'File received successfully')
                status_message = f"Received file: {file_name}"
                if self.app: self.app.root.after(0, self.app.update_status, status_message)
            else:
                self.send_response(400); self.end_headers(); self.wfile.write(b'Bad request')
        except Exception as e:
            self.send_response(500); self.end_headers(); self.wfile.write(f'Server error: {e}'.encode('utf-8'))
def compress_folder_to_temp(folder_path):
    temp_dir = tempfile.gettempdir(); base_name = os.path.join(temp_dir, os.path.basename(folder_path)); zip_path = shutil.make_archive(base_name, 'zip', folder_path); return zip_path
def upload_file(file_path, url):
    with open(file_path, 'rb') as f: files = {'file': (os.path.basename(file_path), f)}; headers = {'file-name': os.path.basename(file_path)}; response = requests.post(url, files=files, headers=headers, timeout=300); return response


# --- TKINTER GUI APPLICATION ---
class FileTransferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple File Transfer (with ngrok)")
        self.root.geometry("450x400")

        self.selected_path = None
        self.httpd = None
        self.server_thread = None
        self.public_url = None

        # --- Mode Selection ---
        self.mode_var = tk.StringVar(value="server")
        mode_frame = tk.Frame(self.root)
        tk.Radiobutton(mode_frame, text="Server (Receive)", variable=self.mode_var, value="server", command=self.update_mode).pack(side="left", padx=10)
        tk.Radiobutton(mode_frame, text="Client (Send)", variable=self.mode_var, value="client", command=self.update_mode).pack(side="left", padx=10)
        mode_frame.pack(pady=10)
        
        # --- Server Frame (Simplified) ---
        self.server_frame = tk.LabelFrame(self.root, text="Server Controls", padx=10, pady=10)
        
        tk.Label(self.server_frame, text="Local Port:").pack()
        self.port_entry = tk.Entry(self.server_frame)
        self.port_entry.insert(0, "8000")
        self.port_entry.pack(pady=(0, 10))

        self.ngrok_config_button = tk.Button(self.server_frame, text="Configure ngrok Authtoken (Recommended)", command=self.configure_ngrok)
        self.ngrok_config_button.pack(pady=5)

        self.server_button = tk.Button(self.server_frame, text="Start Server", command=self.toggle_server)
        self.server_button.pack(pady=10)

        # --- Client Frame (Simplified) ---
        self.client_frame = tk.LabelFrame(self.root, text="Client Controls", padx=10, pady=10)
        
        tk.Label(self.client_frame, text="URL (provided by receiver):").pack()
        self.url_entry = tk.Entry(self.client_frame, width=45)
        self.url_entry.pack(pady=5)
        
        select_buttons_frame = tk.Frame(self.client_frame)
        tk.Button(select_buttons_frame, text="Select File", command=self.select_file).pack(side="left", padx=5)
        tk.Button(select_buttons_frame, text="Select Folder", command=self.select_folder).pack(side="left", padx=5)
        select_buttons_frame.pack(pady=10)

        self.selected_path_label = tk.Label(self.client_frame, text="No file/folder selected.", wraplength=350)
        self.selected_path_label.pack(pady=5)
        
        self.upload_button = tk.Button(self.client_frame, text="Upload", command=self.upload, state=tk.DISABLED)
        self.upload_button.pack(pady=10)

        # --- Status Bar ---
        self.status_bar = tk.Label(self.root, text="Welcome!", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # ### FIX: Moved self.update_mode() to be called AFTER all widgets are created ###
        self.update_mode()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_status(self, message):
        self.status_bar.config(text=message)

    def update_mode(self):
        if self.mode_var.get() == "server":
            self.server_frame.pack(fill="x", padx=10, pady=5)
            self.client_frame.pack_forget()
            self.update_status("Server mode. Click Start Server to receive files.")
        else:
            self.server_frame.pack_forget()
            self.client_frame.pack(fill="x", padx=10, pady=5)
            self.update_status("Client mode. Paste the URL and select a file to send.")

    def configure_ngrok(self):
        authtoken = simpledialog.askstring("ngrok Authtoken", "Please enter your ngrok authtoken:", parent=self.root)
        if authtoken:
            try:
                ngrok.set_auth_token(authtoken)
                messagebox.showinfo("Success", "ngrok authtoken saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to set ngrok authtoken: {e}")

    def toggle_server(self):
        if self.httpd:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        try:
            port = int(self.port_entry.get())
            self.update_status("Starting ngrok tunnel... This may take a moment.")
            
            def start_ngrok_tunnel():
                try:
                    conf.get_default().log_event_callback = self.log_ngrok_event
                    # Start a TCP tunnel instead of HTTP for better reliability
                    self.public_url = ngrok.connect(port, "http").public_url
                    self.root.after(0, self.update_status, f"Server running! Share this URL: {self.public_url}")
                except Exception as e:
                    self.root.after(0, messagebox.showerror, "ngrok Error", f"Failed to start ngrok tunnel:\n{e}\n\nMake sure ngrok is not already running on this port.")
                    self.root.after(0, self.stop_server)

            ngrok_thread = threading.Thread(target=start_ngrok_tunnel, daemon=True)
            ngrok_thread.start()

            handler_factory = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, app=self, **kwargs)
            self.httpd = HTTPServer(('', port), handler_factory)
            self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.server_thread.start()
            
            self.server_button.config(text="Stop Server")

        except Exception as e:
            messagebox.showerror("Error", f"Could not start server:\n{e}")
            self.update_status("Error starting server.")

    def log_ngrok_event(self, log):
        if "starting web service" in log.msg:
            self.root.after(0, self.update_status, "ngrok: Starting web service...")
        elif "tunnel established" in log.msg:
             self.root.after(0, self.update_status, "ngrok: Tunnel established!")

    def stop_server(self):
        if self.public_url:
            try:
                ngrok.disconnect(self.public_url)
                print("ngrok tunnel disconnected.")
            except Exception as e:
                print(f"Error disconnecting ngrok: {e}")
            self.public_url = None
        
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
            print("HTTP server stopped.")

        self.server_button.config(text="Start Server")
        self.update_status("Server stopped.")
        
    def upload(self):
        if not self.selected_path:
            messagebox.showerror("Error", "Please select a file or folder first.")
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "URL cannot be empty.")
            return
        
        # ### FIX: Add http:// if user forgets it ###
        if not url.startswith("http://") and not url.startswith("https://"):
            messagebox.showinfo("Info", "Assuming HTTPS for the provided URL.")
            url = "https://" + url # ngrok free tier uses https

        self.upload_button.config(state=tk.DISABLED)
        self.update_status("Starting upload...")

        upload_thread = threading.Thread(target=self.perform_upload, args=(url,), daemon=True)
        upload_thread.start()

    def perform_upload(self, url):
        temp_zip_path = None
        try:
            path_to_upload = self.selected_path
            if os.path.isdir(self.selected_path):
                self.root.after(0, self.update_status, f"Compressing folder...")
                temp_zip_path = compress_folder_to_temp(self.selected_path)
                path_to_upload = temp_zip_path
            self.root.after(0, self.update_status, f"Uploading {os.path.basename(path_to_upload)}...")
            response = upload_file(path_to_upload, url)
            if 200 <= response.status_code < 300:
                self.root.after(0, messagebox.showinfo, "Success", f"Upload successful!")
                self.root.after(0, self.update_status, "Upload complete.")
            else:
                self.root.after(0, messagebox.showerror, "Error", f"Upload failed: {response.status_code}\n{response.text}")
                self.root.after(0, self.update_status, "Upload failed.")
        except requests.exceptions.RequestException as e:
            self.root.after(0, messagebox.showerror, "Connection Error", f"Could not connect:\n{e}")
            self.root.after(0, self.update_status, "Connection failed.")
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"An unexpected error occurred:\n{e}")
            self.root.after(0, self.update_status, "An error occurred.")
        finally:
            if temp_zip_path and os.path.exists(temp_zip_path): os.remove(temp_zip_path)
            self.root.after(0, lambda: self.upload_button.config(state=tk.NORMAL))

    def on_closing(self):
        if self.httpd:
            self.stop_server()
        ngrok.kill()
        self.root.destroy()
        
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