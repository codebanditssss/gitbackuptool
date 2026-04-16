import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import git
from datetime import datetime
from modules.controller import BackupController, load_config

class BackupGUI:
    """
    Tkinter-based GUI for non-technical users to manage backups.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Git-based File Backup Tool")
        self.root.geometry("700x500")
        
        # Load config
        config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "config")
        self.config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.toml"))
        self.config = load_config(self.config_path)
        
        self.controller = None
        self.target_path = tk.StringVar(value=os.getcwd())
        
        self._setup_style()
        self._create_widgets()
        
    def _setup_style(self):
        self.style = ttk.Style()
        self.style.configure("TButton", padding=5)
        self.style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))
        self.style.configure("Status.TLabel", font=("Helvetica", 10, "italic"))

    def _create_widgets(self):
        # Main Layout: Notebook for Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Tab 1: Dashboard
        self.dash_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.dash_tab, text="Dashboard")
        self._setup_dashboard(self.dash_tab)
        
        # Tab 2: History/Restore
        self.history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.history_tab, text="Backup History")
        self._setup_history(self.history_tab)
        
        # Tab 3: Settings
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")
        self._setup_settings(self.settings_tab)

    def _setup_dashboard(self, parent):
        # Folder Selection
        folder_frame = ttk.LabelFrame(parent, text="Watched Folder", padding=10)
        folder_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Entry(folder_frame, textvariable=self.target_path).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ttk.Button(folder_frame, text="Browse", command=self._browse_folder).pack(side="right")
        
        # Controls
        ctrl_frame = ttk.Frame(parent, padding=10)
        ctrl_frame.pack(fill="x")
        
        self.start_btn = ttk.Button(ctrl_frame, text="Start Backup service", command=self._toggle_service)
        self.start_btn.pack(side="left", padx=5)
        
        self.status_label = ttk.Label(ctrl_frame, text="Status: Stopped", style="Status.TLabel")
        self.status_label.pack(side="left", padx=20)
        
        # Activity Log
        log_frame = ttk.LabelFrame(parent, text="Live Activity Log", padding=10)
        log_frame.pack(expand=True, fill="both", padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, state="disabled", bg="#f4f4f4")
        self.log_text.pack(expand=True, fill="both")

    def _setup_history(self, parent):
        ttk.Label(parent, text="Recent Backups", style="Header.TLabel").pack(pady=10)
        
        # History Treeview
        columns = ("hash", "message", "time")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings")
        self.tree.heading("hash", text="Commit Hash")
        self.tree.heading("message", text="Change")
        self.tree.heading("time", text="Timestamp")
        
        self.tree.column("hash", width=100)
        self.tree.column("message", width=350)
        self.tree.column("time", width=150)
        
        self.tree.pack(expand=True, fill="both", padx=10, pady=5)
        
        btn_frame = ttk.Frame(parent, padding=10)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Refresh Logs", command=self._refresh_history).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Restore Selected", command=self._restore_selected).pack(side="right", padx=5)

    def _setup_settings(self, parent):
        # Simple settings display
        ttk.Label(parent, text="Configuration (edit config.toml for now)", style="Header.TLabel").pack(pady=20)
        
        settings_text = f"Debounce: {self.config.get('watcher', {}).get('debounce_ms')}ms\n"
        settings_text += f"Max File Size: {self.config.get('watcher', {}).get('max_file_size_mb')}MB\n"
        settings_text += f"Remote Sync: {'Enabled' if self.config.get('remote', {}).get('enabled') else 'Disabled'}"
        
        ttk.Label(parent, text=settings_text, justify="left").pack(padx=20, pady=10)

    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_path.set(folder)

    def _toggle_service(self):
        if self.controller and self.controller._running:
            self.controller.stop()
            self.start_btn.config(text="Start Backup Service")
            self.status_label.config(text="Status: Stopped")
            self._log_gui("Service stopped.")
        else:
            try:
                self.controller = BackupController(self.target_path.get(), self.config)
                self.controller.start()
                self.start_btn.config(text="Stop Backup Service")
                self.status_label.config(text="Status: Running")
                self._log_gui(f"Service started for {self.target_path.get()}")
                
                # Update history after start for good measure
                self._refresh_history()
            except Exception as e:
                messagebox.showerror("Error", f"Could not start service: {e}")

    def _log_gui(self, message):
        self.log_text.config(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _refresh_history(self):
        # Clear tree
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        try:
            repo = git.Repo(self.target_path.get())
            commits = list(repo.iter_commits(max_count=20))
            for c in commits:
                self.tree.insert("", "end", values=(
                    c.hexsha[:7], 
                    c.summary, 
                    datetime.fromtimestamp(c.committed_date).strftime("%Y-%m-%d %H:%M")
                ))
        except:
            pass

    def _restore_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a backup from the list.")
            return
            
        item = self.tree.item(selected[0])
        commit_hash = item['values'][0]
        
        if messagebox.askyesno("Confirm Restore", f"Restore all files to state at {commit_hash}?"):
            try:
                repo = git.Repo(self.target_path.get())
                repo.git.checkout(commit_hash)
                self._log_gui(f"Restored project to {commit_hash}")
                messagebox.showinfo("Success", f"Project restored to {commit_hash}.")
            except Exception as e:
                messagebox.showerror("Error", f"Restore failed: {e}")

def run_gui():
    root = tk.Tk()
    app = BackupGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
