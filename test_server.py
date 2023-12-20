import sys
import tkinter as tk
from tkinter import ttk
from python_banyan.banyan_base import BanyanBase
import threading

class EchoServerWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Echo Server")

        # Server Logs Frame
        self.logs_label_frame = tk.LabelFrame(self.root, text="Server Logs")
        self.logs_label_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.text_logs = tk.Listbox(self.logs_label_frame, width=50, height=20)
        self.text_logs.pack(padx=10, pady=10, fill="both", expand=True)

        # Timer Frame
        self.timer_label_frame = tk.LabelFrame(self.root, text="Timer")
        self.timer_label_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Entry for setting the countdown time
        self.countdown_value = tk.IntVar(value=300)  # Initial countdown value in seconds (5 minutes)
        self.time_entry = ttk.Entry(self.timer_label_frame, textvariable=self.countdown_value)
        self.time_entry.grid(row=0, column=0, padx=10, pady=10)

        # Start and stop buttons
        self.start_button = ttk.Button(self.timer_label_frame, text="Start", command=self.start_server)
        self.stop_button = ttk.Button(self.timer_label_frame, text="Stop", command=self.stop_server, state=tk.DISABLED)
        self.start_button.grid(row=0, column=1, padx=5, pady=10)
        self.stop_button.grid(row=0, column=2, padx=5, pady=10)

        self.countdown_label = tk.Label(self.timer_label_frame, text=f"Countdown: {self.format_time(self.countdown_value.get())}")
        self.countdown_label.grid(row=1, column=0, columnspan=3, pady=10)

        self.countdown_active = False

    def format_time(self, seconds):
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def start_server(self):
        if not self.countdown_active:
            self.countdown_active = True
            self.update_countdown()

    def stop_server(self):
        self.countdown_active = False

    def update_countdown(self):
        if self.countdown_value.get() > 0 and self.countdown_active:
            self.countdown_value.set(self.countdown_value.get() - 1)
            formatted_time = self.format_time(self.countdown_value.get())
            self.countdown_label.config(text=f"Countdown: {formatted_time}")
            self.root.after(1000, self.update_countdown)  # Update every 1000 milliseconds (1 second)
        else:
            self.countdown_label.config(text="Countdown reached zero")
            self.countdown_active = False

class EchoServer(BanyanBase):
    def __init__(self, server_window):
        super(EchoServer, self).__init__(process_name='EchoServer')
        self.set_subscriber_topic('echo')
        self.server_window = server_window

        # Start the server in a separate thread
        server_thread = threading.Thread(target=self.run_server)
        server_thread.start()

    def run_server(self):
        try:
            self.receive_loop()
        except KeyboardInterrupt:
            pass

    def incoming_message_processing(self, topic, payload):
        action = payload.get('Action', None)
        seller_name = payload.get('Seller', 'Unknown Seller')  # Default to 'Unknown Seller' if not provided
    
        if action == 'Selling':
            item = payload.get('Item', 'N/A')
            price = payload.get('Price', 'N/A')
            self.server_window.text_logs.insert(tk.END, f'{seller_name} Selling {item} for ₱{price:.2f}\n')
            self.server_window.text_logs.yview(tk.END)
        elif action == 'Deleted':
            item_name = payload.get('Item Name', 'N/A')
            self.server_window.text_logs.insert(tk.END, f'{seller_name} Deleted {item_name}\n')
            self.server_window.text_logs.yview(tk.END)
        elif action == 'Bidding':
            item = payload.get('Item', 'N/A')
            new_bid = payload.get('New Bid', 'N/A')
            bidder = payload.get('Bidder Name', 'Unknown Bidder')
            self.server_window.text_logs.insert(tk.END, f'{bidder} Bidding for {item} - New Bid: ₱{new_bid:.2f}\n')
            self.server_window.text_logs.yview(tk.END)
        elif action == 'ReadyForAuction':
            message = payload.get('Message', 'Ready for auction')
            self.server_window.text_logs.insert(tk.END, f'{message}\n')
            self.server_window.text_logs.yview(tk.END)



if __name__ == "__main__":
    root = tk.Tk()
    echo_server_window = EchoServerWindow(root)
    echo_server = EchoServer(echo_server_window)
    root.mainloop()