import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import threading
import os

class SerialGUI:
    def __init__(self, master):
        self.master = master
        master.title("MOG-SERIAL V1-Lightweight")  # Changed title

        # --- Styling ---
        bg_color = "#f0f0f0"  # Light gray background
        fg_color = "#333333"  # Dark gray text
        accent_color = "#4CAF50"  # Green accent color (Material Design)
        font_family = "Segoe UI"  # Modern font
        font_size = 12
        padding = 15
        button_width = 18
        entry_width = 45

        master.configure(bg=bg_color)  # Set background color for the main window

        # --- Styles for ttk widgets ---
        style = ttk.Style()
        style.configure("TLabel", background=bg_color, foreground=fg_color, font=(font_family, font_size))
        style.configure("TCombobox", background=bg_color, foreground=fg_color, font=(font_family, font_size))
        style.configure("TButton", background=accent_color, foreground="white", font=(font_family, font_size, "bold"), padding=padding/2)

        # --- COM Port Selection ---
        self.port_label = ttk.Label(master, text="Select COM Port:")
        self.port_label.grid(row=0, column=0, padx=padding, pady=padding, sticky="w")

        self.ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_var = tk.StringVar(value=self.ports[0] if self.ports else '')
        self.port_dropdown = ttk.Combobox(master, textvariable=self.port_var, values=self.ports, state="readonly")  # prevent user from typing
        self.port_dropdown.grid(row=0, column=1, padx=padding, pady=padding, sticky="ew")

        # --- Baud Rate Selection ---
        self.baud_label = ttk.Label(master, text="Baud Rate:")
        self.baud_label.grid(row=1, column=0, padx=padding, pady=padding, sticky="w")

        self.baud_rates = [
            50, 75, 110, 134, 150, 200, 300, 600, 1200, 1800, 2400, 4800, 9600,
            19200, 38400, 57600, 115200
        ]
        self.baud_var = tk.StringVar(value='9600')
        self.baud_dropdown = ttk.Combobox(master, textvariable=self.baud_var, values=self.baud_rates, state="readonly")  # prevent user from typing
        self.baud_dropdown.grid(row=1, column=1, padx=padding, pady=padding, sticky="ew")

        # --- Connect Button ---
        self.connect_button = tk.Button(master, text="Connect", command=self.connect_serial, width=button_width, font=(font_family, font_size, "bold"), bg=accent_color, fg="white", relief=tk.FLAT)
        self.connect_button.grid(row=2, column=0, columnspan=2, padx=padding, pady=padding)

        # --- Text Area ---
        self.text_area_frame = tk.Frame(master, bg=bg_color, borderwidth=2, relief=tk.SUNKEN) # use tk.SUNKEN
        self.text_area_frame.grid(row=3, column=0, columnspan=2, padx=padding, pady=padding, sticky="nsew")

        self.text_area = tk.Text(self.text_area_frame, height=15, width=60, font=(font_family, font_size), bg="white", fg=fg_color)
        self.text_area.pack(padx=padding/2, pady=padding/2, fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(self.text_area_frame, orient=tk.VERTICAL, command=self.text_area.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area['yscrollcommand'] = self.scrollbar.set

        # --- Send Data Entry ---
        self.send_label = ttk.Label(master, text="Data to Send:")
        self.send_label.grid(row=4, column=0, padx=padding, pady=padding, sticky="w")

        self.send_entry = tk.Entry(master, width=entry_width, font=(font_family, font_size), bg="white", fg=fg_color)
        self.send_entry.grid(row=4, column=1, padx=padding, pady=padding, sticky="ew")

        # --- Send Button ---
        self.send_button = tk.Button(master, text="Send", command=self.send_data, width=button_width, font=(font_family, font_size, "bold"), bg=accent_color, fg="white", relief=tk.FLAT)
        self.send_button.grid(row=5, column=0, columnspan=2, padx=padding, pady=padding)

        # --- Configure Grid Weights ---
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(3, weight=1)

        self.ser = None
        self.running = False

    def connect_serial(self):
        try:
            port = self.port_var.get()
            baud = int(self.baud_var.get())
            self.ser = serial.Serial(port, baudrate=baud, timeout=1)
            self.text_area.insert(tk.END, f"Connected to {port} at {baud} bps\n")
            self.running = True
            threading.Thread(target=self.read_serial_data, daemon=True).start()
        except Exception as e:
            self.text_area.insert(tk.END, f"Error connecting: {e}\n")

    def read_serial_data(self):
        while self.running and self.ser and self.ser.is_open:
            try:
                data = self.ser.readline().decode('utf-8').strip()
                if data:
                    self.text_area.insert(tk.END, f"Received: {data}\n")
                    self.text_area.see(tk.END)
            except Exception as e:
                self.text_area.insert(tk.END, f"Error reading data: {e}\n")
                break

    def send_data(self):
        try:
            if self.ser and self.ser.is_open:
                data = self.send_entry.get()
                self.ser.write(data.encode('utf-8'))
                self.text_area.insert(tk.END, f"Sent: {data}\n")
                self.send_entry.delete(0, tk.END)
            else:
                self.text_area.insert(tk.END, "Not connected to a serial port.\n")
        except Exception as e:
            self.text_area.insert(tk.END, f"Error sending data: {e}\n")

    def close_serial(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.text_area.insert(tk.END, "Disconnected from serial port.\n")

root = tk.Tk()
root.geometry("700x600")  # Set initial window size
gui = SerialGUI(root)
root.protocol("WM_DELETE_WINDOW", gui.close_serial)
root.mainloop()
