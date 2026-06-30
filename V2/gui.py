import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import config
from smtp_handler import send_email
from imap_handler  import fetch_emails, get_folders, delete_email, mark_as_read


# ── Colors & Fonts ───────────────────────────────────────────────────────────
BG_DARK    = "#1e1e2e"
BG_MEDIUM  = "#2a2a3e"
BG_LIGHT   = "#313145"
ACCENT     = "#7c6af7"
ACCENT_HOV = "#6a5ae0"
TEXT_WHITE = "#ffffff"
TEXT_GRAY  = "#a0a0b0"
SUCCESS    = "#4caf50"
ERROR      = "#f44336"
WARNING    = "#ff9800"

FONT_TITLE  = ("Segoe UI", 18, "bold")
FONT_HEADER = ("Segoe UI", 12, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI", 9)


# ── Reusable Widgets ─────────────────────────────────────────────────────────
def styled_button(parent, text, command, color=ACCENT, width=15):
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg=TEXT_WHITE, font=FONT_NORMAL,
        relief="flat", cursor="hand2", width=width,
        activebackground=ACCENT_HOV, activeforeground=TEXT_WHITE,
        padx=10, pady=6, bd=0
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=ACCENT_HOV))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def styled_entry(parent, show=None, width=35):
    return tk.Entry(
        parent,
        bg=BG_LIGHT, fg=TEXT_WHITE,
        insertbackground=TEXT_WHITE,
        relief="flat", font=FONT_NORMAL,
        width=width, show=show,
        highlightthickness=1,
        highlightcolor=ACCENT,
        highlightbackground=BG_MEDIUM
    )


# ── Login Window ─────────────────────────────────────────────────────────────
class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Strato Mail - Login")
        self.root.geometry("420x400")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(False, False)
        self._center_window(420, 400)
        self._build_ui()

    def _center_window(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=ACCENT, height=70)
        header.pack(fill="x")
        tk.Label(header, text="✉  Strato Mail",
                 font=FONT_TITLE, bg=ACCENT, fg=TEXT_WHITE).pack(pady=18)

        # Form
        form = tk.Frame(self.root, bg=BG_DARK, padx=40)
        form.pack(fill="both", expand=True, pady=20)

        # Email
        tk.Label(form, text="Email Address", font=FONT_SMALL,
                 bg=BG_DARK, fg=TEXT_GRAY).pack(anchor="w", pady=(10, 2))
        self.email_entry = styled_entry(form, width=32)
        self.email_entry.pack(fill="x", ipady=8)

        # Password
        tk.Label(form, text="Password", font=FONT_SMALL,
                 bg=BG_DARK, fg=TEXT_GRAY).pack(anchor="w", pady=(12, 2))
        self.pass_entry = styled_entry(form, show="•", width=32)
        self.pass_entry.pack(fill="x", ipady=8)

        # Status
        self.status_label = tk.Label(form, text="", font=FONT_SMALL,
                                      bg=BG_DARK, fg=ERROR)
        self.status_label.pack(pady=(8, 0))

        # Login button
        styled_button(form, "Login", self._login,
                      width=32).pack(fill="x", pady=(10, 0), ipady=4)

        # Enter key
        self.root.bind("<Return>", lambda e: self._login())

    def _login(self):
        email_val = self.email_entry.get().strip()
        pass_val  = self.pass_entry.get().strip()

        if not email_val or not pass_val:
            self.status_label.config(text="Please fill in all fields.", fg=ERROR)
            return
        if "@" not in email_val:
            self.status_label.config(text="Enter a valid email address.", fg=ERROR)
            return

        self.status_label.config(text="Connecting...", fg=WARNING)
        self.root.update()
        threading.Thread(
            target=self._test_connection,
            args=(email_val, pass_val),
            daemon=True
        ).start()

    def _test_connection(self, email_val, pass_val):
        import smtplib, ssl
        try:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                config.SMTP_HOST, config.SMTP_PORT, context=ctx
            ) as s:
                s.login(email_val, pass_val)

            config.EMAIL    = email_val
            config.PASSWORD = pass_val
            self.root.after(0, self._open_main)

        except smtplib.SMTPAuthenticationError:
            self.root.after(0, lambda: self.status_label.config(
                text="Wrong email or password.", fg=ERROR))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(
                text=f"Connection failed: {e}", fg=ERROR))

    def _open_main(self):
        self.root.destroy()
        root = tk.Tk()
        MainWindow(root)
        root.mainloop()


# ── Main Window ──────────────────────────────────────────────────────────────
class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Strato Mail  —  {config.EMAIL}")
        self.root.geometry("1150x720")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)
        self._center_window(1150, 720)

        self.current_folder = "INBOX"
        self.emails         = []
        self.current_email  = None

        self._build_ui()
        self._load_emails()

    def _center_window(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # ── Layout ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_topbar()

        content = tk.Frame(self.root, bg=BG_DARK)
        content.pack(fill="both", expand=True)

        self._build_sidebar(content)
        self._build_email_panel(content)

    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=ACCENT, height=55)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="✉  Strato Mail",
                 font=FONT_HEADER, bg=ACCENT, fg=TEXT_WHITE
                 ).pack(side="left", padx=20)

        tk.Label(bar, text=config.EMAIL,
                 font=FONT_SMALL, bg=ACCENT, fg="#d0d0ff"
                 ).pack(side="left", padx=5)

        styled_button(bar, "⇦ Logout",   self._logout,
                      color="#555577", width=10).pack(side="right", padx=10,  pady=10)
        styled_button(bar, "↻ Refresh",  self._load_emails,
                      color="#444466", width=10).pack(side="right", padx=5,   pady=10)
        styled_button(bar, "✎ Compose",  self._open_compose,
                      color=SUCCESS,   width=12).pack(side="right", padx=5,   pady=10)

    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=BG_MEDIUM, width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="FOLDERS", font=FONT_SMALL,
                 bg=BG_MEDIUM, fg=TEXT_GRAY
                 ).pack(pady=(20, 5), padx=15, anchor="w")

        # ✅ Display name, icon, folder key passed to handler
        self.folder_buttons = {}
        folders = [
            ("INBOX",   "📥", "INBOX"),
            ("Sent",    "📤", "Sent"),
            ("Drafts",  "📝", "Drafts"),
            ("Archive", "📦", "Archive"),
            ("Spam",    "⚠️",  "Spam"),
            ("Trash",   "🗑", "Trash"),
        ]

        for label, icon, key in folders:
            btn = tk.Button(
                sidebar,
                text=f"  {icon}  {label}",
                command=lambda k=key, l=label: self._switch_folder(k, l),
                bg=BG_MEDIUM, fg=TEXT_WHITE,
                font=FONT_NORMAL, relief="flat",
                anchor="w", cursor="hand2",
                activebackground=BG_LIGHT,
                activeforeground=TEXT_WHITE
            )
            btn.pack(fill="x", padx=5, pady=2, ipady=7)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=BG_LIGHT))
            btn.bind("<Leave>", lambda e, b=btn: b.config(
                bg=ACCENT if b == self.folder_buttons.get("active") else BG_MEDIUM
            ))
            self.folder_buttons[key] = btn

        # Highlight INBOX by default
        self.folder_buttons["INBOX"].config(bg=ACCENT)
        self.folder_buttons["active"] = self.folder_buttons["INBOX"]

        # Status
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(sidebar, textvariable=self.status_var,
                 font=FONT_SMALL, bg=BG_MEDIUM, fg=TEXT_GRAY,
                 wraplength=165
                 ).pack(side="bottom", pady=10, padx=10)

    def _build_email_panel(self, parent):
        panel = tk.Frame(parent, bg=BG_DARK)
        panel.pack(side="left", fill="both", expand=True)

        pane = tk.PanedWindow(panel, orient="horizontal",
                               bg=BG_DARK, sashwidth=5,
                               sashrelief="flat", sashpad=2)
        pane.pack(fill="both", expand=True)

        list_frame   = tk.Frame(pane, bg=BG_MEDIUM, width=360)
        reader_frame = tk.Frame(pane, bg=BG_DARK)

        pane.add(list_frame,   minsize=260)
        pane.add(reader_frame, minsize=420)

        self._build_email_list(list_frame)
        self._build_email_reader(reader_frame)

    def _build_email_list(self, parent):
        # Folder title
        self.folder_label = tk.Label(
            parent, text="INBOX",
            font=FONT_HEADER, bg=BG_MEDIUM, fg=TEXT_WHITE
        )
        self.folder_label.pack(pady=(15, 5), padx=15, anchor="w")

        # Search
        sf = tk.Frame(parent, bg=BG_MEDIUM)
        sf.pack(fill="x", padx=10, pady=(0, 8))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._filter_emails)
        search = tk.Entry(
            sf, textvariable=self.search_var,
            bg=BG_LIGHT, fg=TEXT_GRAY,
            insertbackground=TEXT_WHITE,
            relief="flat", font=FONT_SMALL,
            highlightthickness=1,
            highlightcolor=ACCENT,
            highlightbackground=BG_LIGHT
        )
        search.pack(fill="x", ipady=7, padx=2)
        search.insert(0, "🔍  Search emails...")
        search.bind("<FocusIn>",  lambda e: (
            search.delete(0, "end"),
            search.config(fg=TEXT_WHITE)
        ) if "Search" in search.get() else None)
        search.bind("<FocusOut>", lambda e: (
            search.insert(0, "🔍  Search emails..."),
            search.config(fg=TEXT_GRAY)
        ) if not search.get() else None)

        # Listbox
        lf = tk.Frame(parent, bg=BG_MEDIUM)
        lf.pack(fill="both", expand=True, padx=5)

        sb = tk.Scrollbar(lf, bg=BG_MEDIUM, troughcolor=BG_DARK)
        sb.pack(side="right", fill="y")

        self.email_listbox = tk.Listbox(
            lf,
            bg=BG_MEDIUM, fg=TEXT_WHITE,
            selectbackground=ACCENT,
            selectforeground=TEXT_WHITE,
            font=FONT_SMALL,
            relief="flat", borderwidth=0,
            yscrollcommand=sb.set,
            activestyle="none",
            cursor="hand2"
        )
        self.email_listbox.pack(fill="both", expand=True)
        sb.config(command=self.email_listbox.yview)
        self.email_listbox.bind("<<ListboxSelect>>", self._show_email)

        # Delete button
        styled_button(parent, "🗑  Delete Selected",
                      self._delete_email,
                      color="#c0392b", width=22).pack(pady=8)

    def _build_email_reader(self, parent):
        # Info header
        self.reader_header = tk.Frame(parent, bg=BG_LIGHT)
        self.reader_header.pack(fill="x", padx=10, pady=(10, 0))

        self.reader_subject = tk.Label(
            self.reader_header,
            text="Select an email to read",
            font=FONT_HEADER, bg=BG_LIGHT, fg=TEXT_WHITE,
            wraplength=520, justify="left"
        )
        self.reader_subject.pack(anchor="w", padx=15, pady=(12, 2))

        self.reader_from = tk.Label(
            self.reader_header, text="",
            font=FONT_SMALL, bg=BG_LIGHT, fg=TEXT_GRAY
        )
        self.reader_from.pack(anchor="w", padx=15)

        self.reader_date = tk.Label(
            self.reader_header, text="",
            font=FONT_SMALL, bg=BG_LIGHT, fg=TEXT_GRAY
        )
        self.reader_date.pack(anchor="w", padx=15, pady=(2, 10))

        # Action buttons (hidden until email selected)
        self.action_frame = tk.Frame(self.reader_header, bg=BG_LIGHT)
        self.action_frame.pack(anchor="w", padx=15, pady=(0, 12))

        self.reply_btn = styled_button(
            self.action_frame, "↩ Reply", self._reply_email,
            color=ACCENT, width=10
        )
        self.reply_btn.pack(side="left", padx=(0, 8))

        self.forward_btn = styled_button(
            self.action_frame, "➦ Forward", self._forward_email,
            color="#444466", width=10
        )
        self.forward_btn.pack(side="left")

        # Hide buttons initially
        self.action_frame.pack_forget()

        # Body
        self.reader_body = scrolledtext.ScrolledText(
            parent,
            bg=BG_DARK, fg=TEXT_WHITE,
            font=FONT_NORMAL, relief="flat",
            wrap="word", state="disabled",
            insertbackground=TEXT_WHITE,
            padx=20, pady=15
        )
        self.reader_body.pack(fill="both", expand=True, padx=10, pady=10)

    # ── Actions ──────────────────────────────────────────────────────────────
    def _load_emails(self):
        self.status_var.set("Loading...")
        self.email_listbox.delete(0, "end")
        self.email_listbox.insert("end", "  ⏳ Loading emails...")
        threading.Thread(
            target=self._fetch_thread, daemon=True
        ).start()

    def _fetch_thread(self):
        emails = fetch_emails(self.current_folder, limit=30)
        self.emails = emails
        self.root.after(0, self._populate_list)

    def _populate_list(self, emails=None):
        if emails is None:
            emails = self.emails

        self.email_listbox.delete(0, "end")

        if not emails:
            self.email_listbox.insert("end", "  📭  No emails found.")
            self.status_var.set("No emails.")
            return

        for em in emails:
            sender  = em["from"]
            subject = em["subject"]
            date    = em["date"][:16] if em["date"] else ""

            # Truncate long strings
            if len(sender)  > 28: sender  = sender[:25]  + "..."
            if len(subject) > 32: subject = subject[:29] + "..."

            self.email_listbox.insert("end", f"  📧  {sender}")
            self.email_listbox.insert("end", f"       {subject}")
            self.email_listbox.insert("end", f"       {date}")
            self.email_listbox.insert("end", "  " + "─" * 38)  # divider

        self.status_var.set(f"{len(emails)} emails")

    def _filter_emails(self, *args):
        query = self.search_var.get().lower()
        if "search" in query or not query:
            self._populate_list()
            return
        filtered = [
            em for em in self.emails
            if query in em["subject"].lower()
            or query in em["from"].lower()
            or query in em["body"].lower()
        ]
        self._populate_list(filtered)

    def _show_email(self, event):
        selection = self.email_listbox.curselection()
        if not selection:
            return

        # Each email = 4 lines (sender, subject, date, divider)
        idx = selection[0] // 4
        if idx >= len(self.emails):
            return

        em = self.emails[idx]
        self.current_email = em

        # Update header
        self.reader_subject.config(text=em["subject"])
        self.reader_from.config(text=f"From:  {em['from']}")
        self.reader_date.config(text=f"Date:  {em['date']}")

        # Show action buttons
        self.action_frame.pack(anchor="w", padx=15, pady=(0, 12))

        # Update body
        self.reader_body.config(state="normal")
        self.reader_body.delete("1.0", "end")
        self.reader_body.insert("end", em["body"] or "(No content)")
        self.reader_body.config(state="disabled")

        # Mark as read
        threading.Thread(
            target=mark_as_read,
            args=(em["id"], self.current_folder),
            daemon=True
        ).start()

    def _delete_email(self):
        selection = self.email_listbox.curselection()
        if not selection:
            messagebox.showinfo("Delete", "Select an email first.")
            return

        idx = selection[0] // 4
        if idx >= len(self.emails):
            return

        em = self.emails[idx]
        if messagebox.askyesno("Delete", f"Delete:\n{em['subject']}?"):
            success, msg = delete_email(em["id"], self.current_folder)
            if success:
                self.emails.pop(idx)
                self._populate_list()
                self._clear_reader()
            messagebox.showinfo("Delete", msg)

    def _clear_reader(self):
        self.reader_subject.config(text="Select an email to read")
        self.reader_from.config(text="")
        self.reader_date.config(text="")
        self.action_frame.pack_forget()
        self.reader_body.config(state="normal")
        self.reader_body.delete("1.0", "end")
        self.reader_body.config(state="disabled")
        self.current_email = None

    def _switch_folder(self, folder, label):
        # Update active button highlight
        for key, btn in self.folder_buttons.items():
            if key != "active":
                btn.config(bg=BG_MEDIUM)
        self.folder_buttons[folder].config(bg=ACCENT)
        self.folder_buttons["active"] = self.folder_buttons[folder]

        self.current_folder = folder
        self.folder_label.config(text=label.upper())
        self._clear_reader()
        self._load_emails()

    def _reply_email(self):
        if self.current_email:
            em = self.current_email
            ComposeWindow(
                self.root,
                to      = em["from"],
                subject = f"Re: {em['subject']}",
                body    = f"\n\n\n— Original Message —\nFrom: {em['from']}\nDate: {em['date']}\n\n{em['body']}"
            )

    def _forward_email(self):
        if self.current_email:
            em = self.current_email
            ComposeWindow(
                self.root,
                to      = "",
                subject = f"Fwd: {em['subject']}",
                body    = f"\n\n\n— Forwarded Message —\nFrom: {em['from']}\nDate: {em['date']}\n\n{em['body']}"
            )

    def _open_compose(self):
        ComposeWindow(self.root)

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            config.EMAIL    = ""
            config.PASSWORD = ""
            self.root.destroy()
            root = tk.Tk()
            LoginWindow(root)
            root.mainloop()


# ── Compose Window ───────────────────────────────────────────────────────────
class ComposeWindow:
    def __init__(self, parent, to="", subject="", body=""):
        self.window = tk.Toplevel(parent)
        self.window.title("Compose Email")
        self.window.geometry("700x600")
        self.window.configure(bg=BG_DARK)
        self.window.resizable(True, True)
        self.attachments = []
        self._center_window(700, 600, parent)
        self._build_ui(to, subject, body)

    def _center_window(self, w, h, parent):
        sw = parent.winfo_screenwidth()
        sh = parent.winfo_screenheight()
        self.window.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self, to, subject, body):
        # Header
        hdr = tk.Frame(self.window, bg=ACCENT, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="✎  New Message",
                 font=FONT_HEADER, bg=ACCENT, fg=TEXT_WHITE
                 ).pack(side="left", padx=20, pady=12)

        # Form
        form = tk.Frame(self.window, bg=BG_DARK, padx=20)
        form.pack(fill="both", expand=True, pady=10)
        form.columnconfigure(1, weight=1)

        fields = [
            ("To *",      0, False),
            ("Cc",        1, False),
            ("Bcc",       2, False),
            ("Subject *", 3, False),
        ]

        self.entries = {}
        for label, row, _ in fields:
            tk.Label(form, text=label, font=FONT_SMALL,
                     bg=BG_DARK, fg=TEXT_GRAY, width=9, anchor="e"
                     ).grid(row=row, column=0, sticky="e",
                             padx=(0, 8), pady=4)

            entry = styled_entry(form, width=55)
            entry.grid(row=row, column=1, sticky="ew",
                       padx=(0, 5), pady=4, ipady=7)
            self.entries[label] = entry

        # Prefill
        self.entries["To *"].insert(0, to)
        self.entries["Subject *"].insert(0, subject)

        # Attachments row
        tk.Label(form, text="Files", font=FONT_SMALL,
                 bg=BG_DARK, fg=TEXT_GRAY, width=9, anchor="e"
                 ).grid(row=4, column=0, sticky="e", padx=(0, 8), pady=4)

        af = tk.Frame(form, bg=BG_DARK)
        af.grid(row=4, column=1, sticky="ew", pady=4)

        styled_button(af, "📎 Attach File",
                      self._add_attachment,
                      color="#555577", width=13).pack(side="left")

        self.attach_label = tk.Label(
            af, text="No files attached",
            font=FONT_SMALL, bg=BG_DARK, fg=TEXT_GRAY
        )
        self.attach_label.pack(side="left", padx=12)

        # Body
        tk.Label(form, text="Body", font=FONT_SMALL,
                 bg=BG_DARK, fg=TEXT_GRAY, width=9, anchor="ne"
                 ).grid(row=5, column=0, sticky="ne", padx=(0, 8), pady=(10, 0))

        self.body_text = scrolledtext.ScrolledText(
            form,
            bg=BG_LIGHT, fg=TEXT_WHITE,
            insertbackground=TEXT_WHITE,
            font=FONT_NORMAL, relief="flat",
            wrap="word", height=14
        )
        self.body_text.grid(row=5, column=1, sticky="nsew",
                             padx=(0, 5), pady=6)
        self.body_text.insert("1.0", body)
        form.rowconfigure(5, weight=1)

        # Status
        self.status_label = tk.Label(
            self.window, text="",
            font=FONT_SMALL, bg=BG_DARK, fg=SUCCESS
        )
        self.status_label.pack(pady=(0, 4))

        # Buttons
        bf = tk.Frame(self.window, bg=BG_DARK)
        bf.pack(pady=(0, 14))

        styled_button(bf, "✈  Send Email",
                      self._send, color=SUCCESS, width=16
                      ).pack(side="left", padx=10)
        styled_button(bf, "✕  Cancel",
                      self.window.destroy, color="#c0392b", width=10
                      ).pack(side="left", padx=10)

    def _add_attachment(self):
        files = filedialog.askopenfilenames(
            title="Select Files to Attach"
        )
        if files:
            self.attachments.extend(files)
            names = [f.split("/")[-1].split("\\")[-1]
                     for f in self.attachments]
            display = ", ".join(names[:3])
            if len(names) > 3:
                display += f" (+{len(names)-3} more)"
            self.attach_label.config(text=display, fg=TEXT_WHITE)

    def _send(self):
        to      = self.entries["To *"].get().strip()
        cc      = self.entries["Cc"].get().strip()      or None
        bcc     = self.entries["Bcc"].get().strip()     or None
        subject = self.entries["Subject *"].get().strip()
        body    = self.body_text.get("1.0", "end").strip()

        if not to:
            self.status_label.config(
                text="❌ Recipient (To) is required!", fg=ERROR)
            return
        if not subject:
            self.status_label.config(
                text="❌ Subject is required!", fg=ERROR)
            return
        if not body:
            self.status_label.config(
                text="❌ Message body is empty!", fg=ERROR)
            return

        self.status_label.config(text="⏳ Sending...", fg=WARNING)
        self.window.update()

        threading.Thread(
            target=self._send_thread,
            args=(to, subject, body, cc, bcc),
            daemon=True
        ).start()

    def _send_thread(self, to, subject, body, cc, bcc):
        success, msg = send_email(
            to          = to,
            subject     = subject,
            body        = body,
            attachments = self.attachments or None,
            cc          = cc,
            bcc         = bcc
        )
        color = SUCCESS if success else ERROR
        icon  = "✅" if success else "❌"
        self.window.after(
            0, lambda: self.status_label.config(
                text=f"{icon} {msg}", fg=color)
        )
        if success:
            self.window.after(2000, self.window.destroy)