# test.py
print("Step 1: Python works")

try:
    import tkinter as tk
    print("Step 2: tkinter OK")
except Exception as e:
    print(f"Step 2 FAILED: {e}")

try:
    root = tk.Tk()
    print("Step 3: Tk window OK")
    root.destroy()
except Exception as e:
    print(f"Step 3 FAILED: {e}")

try:
    from gui import LoginWindow
    print("Step 4: GUI import OK")
except Exception as e:
    print(f"Step 4 FAILED: {e}")

try:
    from smtp_handler import send_email
    print("Step 5: SMTP import OK")
except Exception as e:
    print(f"Step 5 FAILED: {e}")

try:
    from imap_handler import fetch_emails
    print("Step 6: IMAP import OK")
except Exception as e:
    print(f"Step 6 FAILED: {e}")

print("Done!")