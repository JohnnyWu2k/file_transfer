# Simple File Transfer

A simple, portable, and powerful file transfer tool with a graphical user interface, built with Python. It allows you to share files and folders easily in two modes: across the internet using a public URL, or within your local network (LAN).

![Server Mode Demo](assets\demo-server.gif)

---

## Features

- **Easy-to-use GUI:** No command-line knowledge required.
- **Two Transfer Modes:**
    1.  **Public (Internet) Mode:** Generates a temporary, public URL for sharing files with anyone, anywhere.
    2.  **Local (LAN) Mode:** Works out-of-the-box for transferring files between computers on the same Wi-Fi network.
- **Folder Support:** Automatically compresses folders into a `.zip` file for easy transfer.
- **Cross-Platform:** Works on Windows, macOS, and Linux.
- **One-Click Setup:** Includes a `setup.bat` script for Windows to install all dependencies automatically.

---

## Requirements

- Python 3.7+
- The `ngrok` service is required for public (internet) sharing. The application handles its integration.
- For Windows users, the `setup.bat` script will handle the installation of Python libraries.
- For other systems, install the dependencies manually:
  ```bash
  pip install -r requirements.txt
  ```

---

## Quick Setup (For Windows)

1.  Download or clone this repository.
2.  Double-click on **`setup.bat`**. This will install the required Python libraries.
3.  Once the setup is complete, you can run the application by double-clicking **`start.bat`**.

---

## How to Use

The logic is simple: The person **RECEIVING** files runs the app in **Server Mode**. The person **SENDING** files runs it in **Client Mode**.

### Scenario 1: Sharing with Anyone over the Internet

This mode creates a public URL. It requires a one-time setup of a free ngrok API Key (authtoken).

**On the Receiver's Computer:**
1.  **First-Time Use:**
    *   Click **"Get API Key (Help)"** to open the ngrok website.
    *   Sign up for a free account and copy your Authtoken.
    *   Back in the app, click **"Configure API Key"**, paste your key, and click OK.
2.  Click **"Start Server"**.
3.  The app will generate a public URL (e.g., `https://random-name.ngrok-free.app`).
4.  Click the **"Copy"** button and send this URL to the sender.

**On the Sender's Computer:**
1.  Switch to **Client Mode**.
2.  Paste the full URL into the **"Address or URL"** box. The "Port" box can be left empty.
3.  Select a file or folder and click **"Upload"**.

![Client Mode Demo](assets\demo-client.gif)

### Scenario 2: Sharing on a Local Network (LAN/Wi-Fi)

This mode requires **no API Key** and is perfect for quick transfers at home or in the office.

**On the Receiver's Computer:**
1.  Ensure you have not configured an API Key, or if you have, choose "No" when the app asks about public sharing.
2.  Click **"Start Server"**.
3.  The app will display a local IP address (e.g., `192.168.1.10:8000`).
4.  Click **"Copy"** and send this address to the sender on the same network.

**On the Sender's Computer:**
1.  Switch to **Client Mode**.
2.  In the **"Address or URL"** box, enter the IP part (e.g., `192.168.1.10`).
3.  In the **"Port"** box, enter the port part (e.g., `8000`).
4.  Select a file or folder and click **"Upload"**.

---

## Project Files

- `gui2.py`: The main application script.
- `requirements.txt`: A list of Python libraries required for the project.
- `setup.bat`: A simple batch script for Windows users to set up the environment automatically.