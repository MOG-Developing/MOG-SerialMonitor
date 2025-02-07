import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import json
import datetime
import os

class SerialGUI:
    def __init__(self, master):
        self.master = master
        master.title("MOG-SerialMonitor V2")
        
        # --- Theme Colors ---
        self.themes = {
            "light": {
                "bg": "#f0f0f0",
                "fg": "#333333",
                "accent": "#2196F3",  # Material Blue
                "success": "#4CAF50",  # Material Green
                "warning": "#FFC107",  # Material Yellow
                "error": "#F44336",    # Material Red
                "text_bg": "white"
            },
            "dark": {
                "bg": "#2C2C2C",
                "fg": "#E0E0E0",
                "accent": "#90CAF9",
                "success": "#81C784",
                "warning": "#FFD54F",
                "error": "#E57373",
                "text_bg": "#3C3C3C"
            }
        }
        self.current_theme = "light"
        self.theme = self.themes[self.current_theme]
        
        # --- Styling ---
        self.font_family = "Segoe UI"
        self.font_size = 12
        self.padding = 15
        self.button_width = 18
        self.entry_width = 45

        self.setup_styles()
        self.create_menu()
        self.create_gui_elements()
        
        # --- State Variables ---
        self.ser = None
        self.running = False
        self.auto_scroll = True
        self.timestamp_enabled = True
        self.log_file = None
        
        # Load settings
        self.load_settings()

    def setup_styles(self):
        self.master.configure(bg=self.theme["bg"])
        style = ttk.Style()
        style.configure("TLabel", background=self.theme["bg"], foreground=self.theme["fg"],
                       font=(self.font_family, self.font_size))
        style.configure("TCombobox", background=self.theme["bg"], foreground=self.theme["fg"],
                       font=(self.font_family, self.font_size))
        style.configure("TButton", background=self.theme["accent"], foreground="white",
                       font=(self.font_family, self.font_size, "bold"), padding=self.padding/2)

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Start Logging", command=self.start_logging)
        file_menu.add_command(label="Stop Logging", command=self.stop_logging)
        file_menu.add_separator()
        file_menu.add_command(label="Clear Display", command=self.clear_display)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)
        
        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(label="Auto-scroll", command=self.toggle_auto_scroll)
        view_menu.add_checkbutton(label="Show Timestamps", command=self.toggle_timestamps)
        
        # Settings Menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Toggle Theme", command=self.toggle_theme)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_gui_elements(self):
        # Create main container
        main_frame = tk.Frame(self.master, bg=self.theme["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=self.padding, pady=self.padding)
        
        # Connection Frame
        conn_frame = tk.LabelFrame(main_frame, text="Connection Settings", 
                                 bg=self.theme["bg"], fg=self.theme["fg"])
        conn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Port Selection
        port_frame = tk.Frame(conn_frame, bg=self.theme["bg"])
        port_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.port_label = ttk.Label(port_frame, text="COM Port:")
        self.port_label.pack(side=tk.LEFT)
        
        self.ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_var = tk.StringVar(value=self.ports[0] if self.ports else '')
        self.port_dropdown = ttk.Combobox(port_frame, textvariable=self.port_var, 
                                        values=self.ports, state="readonly", width=20)
        self.port_dropdown.pack(side=tk.LEFT, padx=(5, 0))
        
        refresh_btn = tk.Button(port_frame, text="⟳", command=self.refresh_ports,
                              bg=self.theme["accent"], fg="white")
        refresh_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Baud Rate
        baud_frame = tk.Frame(conn_frame, bg=self.theme["bg"])
        baud_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.baud_label = ttk.Label(baud_frame, text="Baud Rate:")
        self.baud_label.pack(side=tk.LEFT)
        
        self.baud_rates = [50, 75, 110, 134, 150, 200, 300, 600, 1200, 1800, 2400, 
                          4800, 9600, 19200, 38400, 57600, 115200]
        self.baud_var = tk.StringVar(value='9600')
        self.baud_dropdown = ttk.Combobox(baud_frame, textvariable=self.baud_var,
                                        values=self.baud_rates, state="readonly", width=20)
        self.baud_dropdown.pack(side=tk.LEFT, padx=(5, 0))
        
        # Connect Button
        self.connect_button = tk.Button(conn_frame, text="Connect", command=self.connect_serial,
                                      bg=self.theme["success"], fg="white",
                                      font=(self.font_family, self.font_size, "bold"))
        self.connect_button.pack(pady=5)
        
        # Terminal Frame
        term_frame = tk.LabelFrame(main_frame, text="Terminal", 
                                 bg=self.theme["bg"], fg=self.theme["fg"])
        term_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Text Area
        self.text_area = tk.Text(term_frame, height=15, width=60,
                               font=(self.font_family, self.font_size),
                               bg=self.theme["text_bg"], fg=self.theme["fg"])
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(term_frame, orient=tk.VERTICAL, command=self.text_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area['yscrollcommand'] = scrollbar.set
        
        # Send Frame
        send_frame = tk.Frame(main_frame, bg=self.theme["bg"])
        send_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.send_entry = tk.Entry(send_frame, width=self.entry_width,
                                 font=(self.font_family, self.font_size),
                                 bg=self.theme["text_bg"], fg=self.theme["fg"])
        self.send_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.send_entry.bind('<Return>', lambda e: self.send_data())
        
        self.send_button = tk.Button(send_frame, text="Send", command=self.send_data,
                                   bg=self.theme["accent"], fg="white",
                                   font=(self.font_family, self.font_size, "bold"))
        self.send_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Status Bar
        self.status_var = tk.StringVar(value="Not Connected")
        self.status_bar = tk.Label(main_frame, textvariable=self.status_var,
                                 bg=self.theme["bg"], fg=self.theme["fg"])
        self.status_bar.pack(fill=tk.X, padx=5)

    def refresh_ports(self):
        self.ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_dropdown['values'] = self.ports
        if self.ports:
            self.port_var.set(self.ports[0])

    def connect_serial(self):
        if not self.running:
            try:
                port = self.port_var.get()
                baud = int(self.baud_var.get())
                self.ser = serial.Serial(port, baudrate=baud, timeout=1)
                self.running = True
                self.connect_button.config(text="Disconnect", bg=self.theme["error"])
                self.status_var.set(f"Connected to {port} at {baud} bps")
                self.log_message(f"Connected to {port} at {baud} bps")
                threading.Thread(target=self.read_serial_data, daemon=True).start()
            except Exception as e:
                self.log_message(f"Error connecting: {e}", error=True)
        else:
            self.close_serial()
            self.connect_button.config(text="Connect", bg=self.theme["success"])
            self.status_var.set("Not Connected")

    def read_serial_data(self):
        while self.running and self.ser and self.ser.is_open:
            try:
                data = self.ser.readline().decode('utf-8').strip()
                if data:
                    self.log_message(f"Received: {data}")
            except Exception as e:
                self.log_message(f"Error reading data: {e}", error=True)
                break

    def send_data(self):
        try:
            if self.ser and self.ser.is_open:
                data = self.send_entry.get()
                self.ser.write(f"{data}\n".encode('utf-8'))
                self.log_message(f"Sent: {data}")
                self.send_entry.delete(0, tk.END)
            else:
                self.log_message("Not connected to a serial port.", error=True)
        except Exception as e:
            self.log_message(f"Error sending data: {e}", error=True)

    def log_message(self, message, error=False):
        if self.timestamp_enabled:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            message = f"[{timestamp}] {message}"
        
        tag = "error" if error else "normal"
        self.text_area.tag_config("error", foreground=self.theme["error"])
        
        self.text_area.insert(tk.END, message + "\n", tag)
        if self.auto_scroll:
            self.text_area.see(tk.END)
            
        if self.log_file:
            self.log_file.write(message + "\n")
            self.log_file.flush()

    def clear_display(self):
        self.text_area.delete(1.0, tk.END)

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.theme = self.themes[self.current_theme]
        self.setup_styles()
        self.save_settings()

    def toggle_auto_scroll(self):
        self.auto_scroll = not self.auto_scroll
        self.save_settings()

    def toggle_timestamps(self):
        self.timestamp_enabled = not self.timestamp_enabled
        self.save_settings()

    def start_logging(self):
        if not self.log_file:
            filename = f"serial_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            try:
                self.log_file = open(filename, 'w')
                self.log_message(f"Started logging to {filename}")
            except Exception as e:
                self.log_message(f"Error starting log: {e}", error=True)

    def stop_logging(self):
        if self.log_file:
            self.log_file.close()
            self.log_file = None
            self.log_message("Logging stopped")

    def show_about(self):
        messagebox.showinfo("About", 
            "MOG-SerialMonitor V2\n\n"
            "Version V2 by @misterofgames_yt\n"
            "A modern, feature-rich serial terminal\n\n"
            "Features:\n"
            "- Multiple baud rates\n"
            "- Auto-scrolling\n"
            "- Timestamps\n"
            "- Logging\n"
            "- Light/Dark themes")

    def load_settings(self):
        try:
            with open('serial_settings.json', 'r') as f:
                settings = json.load(f)
                self.current_theme = settings.get('theme', 'light')
                self.auto_scroll = settings.get('auto_scroll', True)
                self.timestamp_enabled = settings.get('timestamps', True)
                self.theme = self.themes[self.current_theme]
                self.setup_styles()
        except:
            pass

    def save_settings(self):
        settings = {
            'theme': self.current_theme,
            'auto_scroll': self.auto_scroll,
            'timestamps': self.timestamp_enabled
        }
        try:
            with open('serial_settings.json', 'w') as f:
                json.dump(settings, f)
        except:
            pass

    def close_serial(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.log_message("Disconnected from serial port.")
        if self.log_file:
            self.stop_logging()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("MOG-SerialMonitor V2")
    root.geometry("800x600")
    gui = SerialGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: [gui.close_serial(), root.destroy()])
    root.mainloop()