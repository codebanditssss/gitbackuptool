import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import git
from datetime import datetime
from modules.controller import BackupController, load_config

class BackupGUI:
    """
    A polished Tkinter-based GUI for the Git-based File Backup Tool.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Git-based File Backup Tool")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f2f5")
        
        # Load config
        self.config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.toml"))
        self.config = load_config(self.config_path)
        
        self.controller = None
        self.target_path = tk.StringVar(value=os.getcwd())
        
        # Setting variables
        self.debounce_var = tk.StringVar(value=str(self.config.get('watcher', {}).get('debounce_ms', 2000)))
        self.max_size_var = tk.StringVar(value=str(self.config.get('watcher', {}).get('max_file_size_mb', 50)))
        self.remote_enabled_var = tk.BooleanVar(value=self.config.get('remote', {}).get('enabled', False))
        self.remote_url_var = tk.StringVar(value=self.config.get('remote', {}).get('remote_url', ''))
        
        self._setup_style()
        self._create_widgets()
        
    def _setup_style(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Colors
        self.bg_color = "#f0f2f5"
        self.primary_color = "#1a73e8"
        self.text_color = "#202124"
        
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        self.style.configure("TNotebook.Tab", padding=[15, 5], font=("Segoe UI", 10))
        
        self.style.configure("Card.TLabelframe", background="white", relief="flat", borderwidth=1)
        self.style.configure("Card.TLabelframe.Label", font=("Segoe UI", 11, "bold"), foreground=self.primary_color, background="white")
        
        self.style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=10, background=self.primary_color, foreground="white")
        self.style.map("Action.TButton", background=[('active', '#1557b0')])
        
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), background=self.bg_color, foreground=self.text_color)
        self.style.configure("Status.TLabel", font=("Segoe UI", 10), background=self.bg_color)

    def _create_widgets(self):
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        ttk.Label(header_frame, text="Git-based Backup Engine", style="Header.TLabel").pack(side="left")
        
        # Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=20, pady=(0, 20))
        
        # Build Tabs
        self._build_dashboard_tab()
        self._build_history_tab()
        self._build_settings_tab()

    def _build_dashboard_tab(self):
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text=" Dashboard ")
        
        # Folder Card
        folder_card = ttk.LabelFrame(tab, text=" Target Directory ", padding=15, style="Card.TLabelframe")
        folder_card.pack(fill="x", pady=(0, 20))
        
        path_frame = ttk.Frame(folder_card)
        path_frame.pack(fill="x")
        ttk.Entry(path_frame, textvariable=self.target_path, font=("Segoe UI", 10)).pack(side="left", expand=True, fill="x", padx=(0, 10))
        ttk.Button(path_frame, text="Change Folder", command=self._browse_folder).pack(side="right")
        
        # Control Card
        control_card = ttk.Frame(tab)
        control_card.pack(fill="x", pady=10)
        
        self.start_btn = ttk.Button(control_card, text="▶ START BACKUP SERVICE", style="Action.TButton", command=self._toggle_service)
        self.start_btn.pack(side="left")
        
        self.status_label = ttk.Label(control_card, text="● Status: Stopped", style="Status.TLabel", foreground="#5f6368")
        self.status_label.pack(side="left", padx=20)
        
        # Log View
        log_label = ttk.Label(tab, text="Live Activity Activity Log", font=("Segoe UI", 10, "bold"))
        log_label.pack(anchor="w", pady=(10, 5))
        
        log_frame = tk.Frame(tab, bg="white", highlightbackground="#dadce0", highlightthickness=1)
        log_frame.pack(expand=True, fill="both")
        
        self.log_text = tk.Text(log_frame, font=("Consolas", 9), state="disabled", bg="white", relief="flat", padx=10, pady=10)
        self.log_text.pack(expand=True, fill="both")

    def _build_history_tab(self):
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text=" Backup History ")
        
        # Treeview with scrollbar
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(expand=True, fill="both")
        
        columns = ("hash", "message", "time")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("hash", text="HASH")
        self.tree.heading("message", text="BACKUP DESCRIPTION")
        self.tree.heading("time", text="TIMESTAMP")
        
        self.tree.column("hash", width=80, anchor="center")
        self.tree.column("message", width=450)
        self.tree.column("time", width=150)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")
        
        # History Filter / Actions
        actions = ttk.Frame(tab, padding=(0, 15))
        actions.pack(fill="x")
        ttk.Button(actions, text="Refresh Logs", command=self._refresh_history).pack(side="left", padx=5)
        ttk.Button(actions, text="Restore to this Version", command=self._restore_selected).pack(side="right", padx=5)

    def _build_settings_tab(self):
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text=" Advanced Settings ")
        
        container = ttk.LabelFrame(tab, text=" Engine Configuration ", padding=20, style="Card.TLabelframe")
        container.pack(fill="both", expand=True)
        
        # Grid layout for settings
        grid = ttk.Frame(container, background="white")
        grid.pack(fill="x")
        
        # Watcher Settings
        ttk.Label(grid, text="Debounce Window (ms):", background="white").grid(row=0, column=0, sticky="w", pady=10)
        ttk.Entry(grid, textvariable=self.debounce_var, width=10).grid(row=0, column=1, sticky="w", padx=10)
        
        ttk.Label(grid, text="Max File Size (MB):", background="white").grid(row=1, column=0, sticky="w", pady=10)
        ttk.Entry(grid, textvariable=self.max_size_var, width=10).grid(row=1, column=1, sticky="w", padx=10)
        
        # Remote Settings
        ttk.Separator(grid, orient="horizontal").grid(row=2, column=0, columnspan=2, fill="x", pady=20)
        
        ttk.Checkbutton(grid, text="Enable Remote Cloud Sync", variable=self.remote_enabled_var, background="white").grid(row=3, column=0, sticky="w")
        
        ttk.Label(grid, text="Remote URL:", background="white").grid(row=4, column=0, sticky="w", pady=10)
        ttk.Entry(grid, textvariable=self.remote_url_var, width=40).grid(row=4, column=1, sticky="w", padx=10)
        
        # Save Button
        save_btn = ttk.Button(container, text="SAVE CONFIGURATION", command=self._save_settings)
        save_btn.pack(side="bottom", anchor="e", pady=20)

    def _save_settings(self):
        """Update the config.toml file with GUI values."""
        try:
            # Update local config dict
            self.config['watcher']['debounce_ms'] = int(self.debounce_var.get())
            self.config['watcher']['max_file_size_mb'] = int(self.max_size_var.get())
            self.config['remote']['enabled'] = self.remote_enabled_var.get()
            self.config['remote']['remote_url'] = self.remote_url_var.get()
            
            # Write to file (simple TOML writer or formatted string)
            with open(self.config_path, 'w') as f:
                f.write(f"[watcher]\ntarget_directory = \".\"\ndebounce_ms = {self.debounce_var.get()}\nrecursive = true\n"
                        f"exclude_extensions = [\".swp\", \".tmp\", \"~\", \".git\"]\nmax_file_size_mb = {self.max_size_var.get()}\n\n"
                        f"[git]\ncommit_message_template = \"[BACKUP] {{event_type}}: {{filename}} @ {{timestamp}}\"\nbranch = \"main\"\n\n"
                        f"[remote]\nenabled = {str(self.remote_enabled_var.get()).lower()}\nremote_url = \"{self.remote_url_var.get()}\"\n"
                        f"push_interval_commits = 10\npush_interval_minutes = 30\n")
            
            messagebox.showinfo("Success", "Configuration saved successfully!\nRestart the service to apply changes.")
            self._log_gui("Configuration updated.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save config: {e}")

    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_path.set(folder)
            self._refresh_history()

    def _toggle_service(self):
        if self.controller and self.controller._running:
            self.controller.stop()
            self.start_btn.config(text="▶ START BACKUP SERVICE")
            self.status_label.config(text="● Status: Stopped", foreground="#5f6368")
            self._log_gui("Service stopped.")
        else:
            try:
                self.controller = BackupController(self.target_path.get(), self.config)
                self.controller.start()
                self.start_btn.config(text="■ STOP BACKUP SERVICE")
                self.status_label.config(text="● Status: RUNNING", foreground="#1e8e3e")
                self._log_gui(f"Monitoring: {self.target_path.get()}")
                self._refresh_history()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start: {e}")

    def _log_gui(self, message):
        self.log_text.config(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _refresh_history(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            repo = git.Repo(self.target_path.get())
            for c in repo.iter_commits(max_count=50):
                self.tree.insert("", "end", values=(
                    c.hexsha[:7], 
                    c.summary, 
                    datetime.fromtimestamp(c.committed_date).strftime("%Y-%m-%d %H:%M")
                ))
        except:
            pass

    def _restore_selected(self):
        selection = self.tree.selection()
        if not selection: return
        item = self.tree.item(selection[0])
        h = item['values'][0]
        if messagebox.askyesno("Confirm", f"Rollback project to version {h}?"):
            try:
                repo = git.Repo(self.target_path.get())
                repo.git.checkout(h)
                self._log_gui(f"Rolled back to {h}")
                messagebox.showinfo("Success", f"Project state restored to {h}.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

def run_gui():
    root = tk.Tk()
    app = BackupGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
