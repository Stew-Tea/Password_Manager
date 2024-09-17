import sqlite3
import hashlib
import os
from tkinter import *
from tkinter import messagebox
from cryptography.fernet import Fernet

# Database setup for storing the master password hash and user passwords
def setup_database():
    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS master_password
                      (id INTEGER PRIMARY KEY, password_hash TEXT, salt TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS passwords
                      (id INTEGER PRIMARY KEY, website TEXT, username TEXT, password TEXT)''')
    conn.commit()
    conn.close()

# Hash the password with a salt
def hash_password(password, salt):
    return hashlib.sha256(password.encode() + salt).hexdigest()

# Save the master password hash to the database
def save_master_password(master_password):
    salt = os.urandom(16)
    password_hash = hash_password(master_password, salt)

    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO master_password (password_hash, salt) VALUES (?, ?)',
                   (password_hash, salt))
    conn.commit()
    conn.close()

# Check if a master password exists
def master_password_exists():
    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM master_password')
    result = cursor.fetchone()
    conn.close()
    return result is not None

# Verify the entered master password
def verify_master_password(master_password):
    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash, salt FROM master_password')
    result = cursor.fetchone()
    conn.close()

    if result:
        password_hash, salt = result
        return hash_password(master_password, salt) == password_hash
    return False

# Generate encryption key using the master password
def generate_key(master_password):
    return hashlib.sha256(master_password.encode()).digest()

# Encrypt the password
def encrypt_password(key, password):
    cipher_suite = Fernet(key)
    encrypted_password = cipher_suite.encrypt(password.encode())
    return encrypted_password

# Decrypt the password
def decrypt_password(key, encrypted_password):
    cipher_suite = Fernet(key)
    decrypted_password = cipher_suite.decrypt(encrypted_password).decode()
    return decrypted_password

# Save password to database
def save_password():
    website = website_entry.get()
    username = username_entry.get()
    password = password_entry.get()

    if not website or not username or not password:
        messagebox.showwarning("Input Error", "Please fill in all fields")
        return

    encrypted_password = encrypt_password(key, password)

    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO passwords (website, username, password) VALUES (?, ?, ?)', 
                   (website, username, encrypted_password))
    conn.commit()
    conn.close()

    website_entry.delete(0, END)
    username_entry.delete(0, END)
    password_entry.delete(0, END)

    messagebox.showinfo("Success", "Password saved successfully")

# Retrieve and display passwords
def view_passwords():
    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()
    cursor.execute('SELECT website, username, password FROM passwords')
    rows = cursor.fetchall()
    conn.close()

    display_text = ""
    for row in rows:
        website, username, encrypted_password = row
        decrypted_password = decrypt_password(key, encrypted_password)
        display_text += f"Website: {website}\nUsername: {username}\nPassword: {decrypted_password}\n\n"

    result_text.delete(1.0, END)
    result_text.insert(INSERT, display_text)

# Main Application
def main_app():
    global website_entry, username_entry, password_entry, result_text

    app = Tk()
    app.title("Password Manager")

    Label(app, text="Website:").grid(row=0, column=0, padx=10, pady=10)
    Label(app, text="Username:").grid(row=1, column=0, padx=10, pady=10)
    Label(app, text="Password:").grid(row=2, column=0, padx=10, pady=10)

    website_entry = Entry(app, width=40)
    website_entry.grid(row=0, column=1, padx=10, pady=10)

    username_entry = Entry(app, width=40)
    username_entry.grid(row=1, column=1, padx=10, pady=10)

    password_entry = Entry(app, width=40, show="*")
    password_entry.grid(row=2, column=1, padx=10, pady=10)

    Button(app, text="Save Password", command=save_password).grid(row=3, column=0, columnspan=2, pady=10)
    Button(app, text="View Passwords", command=view_passwords).grid(row=4, column=0, columnspan=2, pady=10)

    result_text = Text(app, height=10, width=60)
    result_text.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    app.mainloop()

# Prompt the user to create a master password
def create_master_password():
    def save_password():
        password1 = master_password_entry.get()
        password2 = confirm_password_entry.get()

        if password1 == password2:
            save_master_password(password1)
            messagebox.showinfo("Success", "Master password created successfully!")
            root.destroy()
            enter_master_password()
        else:
            messagebox.showerror("Error", "Passwords do not match. Please try again.")

    root = Tk()
    root.title("Create Master Password")

    Label(root, text="Create Master Password:").pack(padx=10, pady=10)
    master_password_entry = Entry(root, width=30, show="*")
    master_password_entry.pack(padx=10, pady=10)

    Label(root, text="Confirm Master Password:").pack(padx=10, pady=10)
    confirm_password_entry = Entry(root, width=30, show="*")
    confirm_password_entry.pack(padx=10, pady=10)

    Button(root, text="Save Password", command=save_password).pack(pady=10)

    root.mainloop()

# Function to enter the master password for existing users
def enter_master_password():
    def check_password():
        entered_password = master_password_entry.get()
        global key
        if verify_master_password(entered_password):
            key = Fernet.generate_key()
            messagebox.showinfo("Success", "Master password verified!")
            root.destroy()
            main_app()
        else:
            messagebox.showerror("Error", "Incorrect master password. Please try again.")

    root = Tk()
    root.title("Enter Master Password")

    Label(root, text="Enter Master Password:").pack(padx=10, pady=10)
    master_password_entry = Entry(root, width=30, show="*")
    master_password_entry.pack(padx=10, pady=10)

    Button(root, text="Enter", command=check_password).pack(pady=10)

    root.mainloop()

# Main function to check master password existence
def main():
    setup_database()

    if master_password_exists():
        enter_master_password()
    else:
        create_master_password()

# Start the application
if __name__ == "__main__":
    main()
