import socket
import tkinter as tk
import tkinter.simpledialog as simpledialog
import tkinter.filedialog as filedialog
import ssl
import threading
import zipfile
import os
from datetime import datetime  # Import datetime for timestamps

SERVER_IP = "10.147.18.240"
PORT = 65432

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

client_socket = socket.create_connection((SERVER_IP, PORT))
secure_socket = context.wrap_socket(client_socket)

root = tk.Tk()
root.withdraw()
username = simpledialog.askstring("Username", "Enter username:", parent=root)
secure_socket.send(username.encode())
root.deiconify()
root.title(f"Chat - {username}")

# GUI Components
message_area = tk.Text(root, height=15, width=50, state=tk.DISABLED)
message_area.pack(padx=10, pady=10)

entry_box = tk.Entry(root, width=50)
entry_box.pack(padx=10, pady=10)
entry_box.bind("<Return>", lambda e: send_message())

online_users = tk.Listbox(root, height=9, width=25)
online_users.pack(side=tk.LEFT, padx=5)

def update_user_list(users):
    """Update the list of online users in the GUI"""
    online_users.delete(0, tk.END)
    for user in users:
        if user != username:
            online_users.insert(tk.END, user)

def send_message():
    """Send a message to the server"""
    message = entry_box.get().strip()
    if not message:
        return
    
    if message.startswith("/private "):
        parts = message.split(" ", 2)
        if len(parts) == 3:
            target_user, private_msg = parts[1], parts[2]
            secure_socket.send(f"PRIVATE {target_user} {private_msg}".encode())
            # Display local private message with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Add timestamp
            message_area.config(state=tk.NORMAL)
            message_area.insert(tk.END, f"[{timestamp}] To {target_user}: {private_msg}\n")
            message_area.see(tk.END)
            message_area.config(state=tk.DISABLED)
        else:
            message_area.config(state=tk.NORMAL)
            message_area.insert(tk.END, "Invalid private message format\n")
            message_area.config(state=tk.DISABLED)
    else:
        # Display local message immediately with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Add timestamp
        message_area.config(state=tk.NORMAL)
        message_area.insert(tk.END, f"[{timestamp}] You: {message}\n")
        message_area.see(tk.END)
        message_area.config(state=tk.DISABLED)
        secure_socket.send(message.encode())
    
    entry_box.delete(0, tk.END)

def send_file():
    """Send a file to another user"""
    file_path = filedialog.askopenfilename()
    if not file_path:
        return
    
    recipient = simpledialog.askstring("Recipient", "Send to:", parent=root)
    if not recipient or recipient not in online_users.get(0, tk.END):
        return

    # Compress file
    zip_path = f"{file_path}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(file_path, os.path.basename(file_path))

    # Start file server
    file_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    file_socket.bind(('0.0.0.0', 0))
    file_socket.listen(1)
    file_port = file_socket.getsockname()[1]

    secure_socket.send(f"FILE_REQUEST {recipient}".encode())
    secure_socket.send(f"FILE_PORT {recipient} {file_port}".encode())

    conn, addr = file_socket.accept()
    with open(zip_path, "rb") as f:
        while chunk := f.read(4096):
            conn.send(chunk)
    conn.close()
    os.remove(zip_path)

def receive_messages():
    """Receive messages from the server"""
    while True:
        try:
            message = secure_socket.recv(4096).decode()
            if message.startswith("USER_LIST"):
                update_user_list(message.split()[1:])
            elif message.startswith("FILE_ALERT"):
                sender = message.split()[1]
                if tk.messagebox.askyesno("File Transfer", f"Accept file from {sender}?"):
                    secure_socket.send(f"FILE_ACCEPT {sender}".encode())
            elif message.startswith("FILE_CONNECT"):
                _, sender, port = message.split()
                file_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                file_socket.connect((SERVER_IP, int(port)))
                save_path = filedialog.asksaveasfilename(
                    initialfile=f"{sender}_file.zip")
                with open(save_path, "wb") as f:
                    while chunk := file_socket.recv(4096):
                        f.write(chunk)
                file_socket.close()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Add timestamp
                message_area.config(state=tk.NORMAL)
                message_area.insert(tk.END, f"[{timestamp}] 📁 File received from {sender}\n")
                message_area.config(state=tk.DISABLED)
            elif message.startswith("PRIVATE "):
                parts = message.split(" ", 2)
                if len(parts) == 3:
                    _, sender_part, msg = parts
                    sender = sender_part.rstrip(':')
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Add timestamp
                    message_area.config(state=tk.NORMAL)
                    message_area.insert(tk.END, f"[{timestamp}] 🔒 Private from {sender}: {msg}\n")
                    message_area.see(tk.END)
                    message_area.config(state=tk.DISABLED)
            else:
                # Filter out own messages from broadcast
                if not message.startswith(f"{username}:"):
                    message_area.config(state=tk.NORMAL)
                    message_area.insert(tk.END, f"{message}\n")
                    message_area.see(tk.END)
                    message_area.config(state=tk.DISABLED)
        except:
            break

# Buttons
tk.Button(root, text="Send", command=send_message).pack(side=tk.RIGHT)
tk.Button(root, text="Send File", command=send_file).pack(side=tk.RIGHT)

threading.Thread(target=receive_messages, daemon=True).start()
root.mainloop()