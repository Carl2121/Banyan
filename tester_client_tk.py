from __future__ import unicode_literals
from tkinter import messagebox
import time
import sys

try:
    from tkinter import *
    from tkinter import ttk
    from tkinter import simpledialog
except ImportError:
    from Tkinter import *
    import ttk

import msgpack
import zmq
from python_banyan.banyan_base import BanyanBase


class CountdownWindow(Toplevel):
    def __init__(self, parent, duration, callback):
        super().__init__(parent)
        self.title("Set Countdown Timer")
        self.geometry("300x150")

        self.duration_label = ttk.Label(self, text="Set countdown duration (seconds):")
        self.duration_label.pack(pady=10)

        self.duration_entry = ttk.Entry(self)
        self.duration_entry.pack(pady=10)

        self.set_button = ttk.Button(self, text="Set Timer", command=self.start_countdown)
        self.set_button.pack(pady=10)

        self.duration = duration
        self.callback = callback  # Fixed: Make sure to set the callback

    def start_countdown(self):
        try:
            self.duration = int(self.duration_entry.get())
            self.callback(self.duration)  # Fixed: Call the callback with the duration
            self.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid input. Please enter a valid integer.")


class TkEchoClient(BanyanBase):
    def __init__(self, topics='reply', back_plane_ip_address=None, subscriber_port='43125',
                 publisher_port='43124', process_name='Auction IO'):
        self.user_name = simpledialog.askstring("Your Name", "Enter your name:")
        if not self.user_name:
            sys.exit(0)

        super(TkEchoClient, self).__init__(back_plane_ip_address=back_plane_ip_address,
                                           subscriber_port=subscriber_port,
                                           publisher_port=publisher_port,
                                           process_name=process_name)

        if topics is None:
            raise ValueError('No Topic List Was Specified.')

        for x in topics:
            self.set_subscriber_topic(x)

        ready_message = f"{self.user_name} is ready for auction"
        payload = {'Action': 'ReadyForAuction', 'Message': ready_message, 'Seller': self.user_name}
        self.publish_payload(payload, 'echo')

        self.root = Tk()
        self.root.title(f"Auction.IO | {self.user_name}")

        self.frame = ttk.Frame(self.root)
        self.frame.pack()

        self.countdown_frame = ttk.LabelFrame(self.frame, text="Countdown")
        self.countdown_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.countdown_label = ttk.Label(self.countdown_frame, text="Time Left: 00:00 second(s)")
        self.countdown_label.grid(row=0, column=0, padx=10, pady=10)

        self.display_sell_frame = ttk.LabelFrame(self.frame, text="Items Selling")
        self.display_sell_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.items_selling = Listbox(self.display_sell_frame, width=50, height=10)
        self.items_selling.grid(row=0, column=0, padx=10, pady=10, columnspan=2)

        self.sell_button = ttk.Button(self.display_sell_frame, text="Sell", command=self.place_sell, state="normal")
        self.sell_button.grid(row=1, column=0, padx=(5, 0), pady=10, sticky="w")

        self.delete_sell_button = ttk.Button(self.display_sell_frame, text="Delete", command=self.delete_sell_item,
                                             state="normal")
        self.delete_sell_button.grid(row=1, column=1, padx=(0, 5), pady=10, sticky="e")

        self.display_sell_frame.columnconfigure(0, weight=1)
        self.display_sell_frame.columnconfigure(1, weight=1)

        self.display_bid_frame = ttk.LabelFrame(self.frame, text="Items Bidding")
        self.display_bid_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.items_bidding = Listbox(self.display_bid_frame, width=50, height=10)
        self.items_bidding.grid(row=0, column=0, padx=10, pady=10)

        self.bid_button_bidding = ttk.Button(self.display_bid_frame, text="Bid", command=self.place_bid, state="normal")
        self.bid_button_bidding.grid(row=1, column=0, padx=10, pady=10)

        self.highest_bidder_frame = ttk.LabelFrame(self.frame, text="Highest Bidder")
        self.highest_bidder_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.highest_bidder_list = Listbox(self.highest_bidder_frame, width=110, height=10)
        self.highest_bidder_list.grid(row=0, column=0, padx=10, pady=10, sticky="nsew", columnspan=2)

        self.timer_seconds = 0  # Initialize timer to 0
        self.timer_active = False

        self.timer_popup_button = ttk.Button(self.countdown_frame, text="Set Timer", command=self.set_timer)
        self.timer_popup_button.grid(row=0, column=1, padx=10, pady=10)
        self.sell_button.config(command=self.place_sell)
        self.delete_sell_button.config(command=self.delete_sell_item)
        self.bid_button_bidding.config(command=self.place_bid)

        self.highest_bids = {}
        self.bidders_names = {}
        self.disable_duration = 0  # Add this line to initialize disable_duration
        



    def disable_buttons(self):
        self.sell_button.config(state="disabled")
        self.delete_sell_button.config(state="disabled")
        self.bid_button_bidding.config(state="disabled")

    def set_timer(self):
        timer_value = simpledialog.askinteger("Set Timer", "Enter the timer value in seconds:")
        if timer_value is not None:
            self.timer_seconds = timer_value
            self.update_timer_display()
            self.send_timer_info_to_server()  # Fixed: Call the method to send timer info to the server
            self.start_timer()

    def handle_echo_messages(self, topic, payload):
        action = payload.get('Action', '')

        if action == 'SetTimer':
            timer_value = payload.get('TimerValue', 0)
            seller_name = payload.get('Seller', 'Unknown Seller')
            print(f"Received Timer Set Request from {seller_name}. Timer Value: {timer_value} seconds")

    def enable_buttons(self):
        self.sell_button.config(state="normal")
        self.delete_sell_button.config(state="normal")
        self.bid_button_bidding.config(state="normal")

    def place_sell(self):
        sell_item = simpledialog.askstring("Sell Item", "Enter item to sell:")
        if sell_item:
            price = simpledialog.askfloat("Set Price", f"Enter the price for {sell_item}:")
            if price is not None:
                try:
                    item_info = f"{sell_item} - ₱{price:.2f} - {self.user_name}"
                    self.items_selling.insert(END, item_info)
                    self.items_bidding.insert(END, item_info)
                    self.show_highest_bids()
                    payload = {'Action': 'Selling', 'Item': sell_item, 'Price': price, 'Seller': self.user_name}
                    self.publish_payload(payload, 'echo')
                except Exception as e:
                    print(f"Error sending payload: {e}")
                self.start_timer()

    def delete_sell_item(self):
        selected_index = self.items_selling.curselection()
        if selected_index:
            item_info = self.items_selling.get(selected_index)
            self.items_selling.delete(selected_index)
            self.items_bidding.delete(self.items_bidding.get(0, END).index(item_info))
            item_name = item_info.split(' - ')[0]
            if item_name in self.highest_bids:
                del self.highest_bids[item_name]
            self.show_highest_bids()
            payload = {'Action': 'Deleted', 'Item Name': item_name, 'Seller': self.user_name}
            self.publish_payload(payload, 'echo')

    def place_bid(self):
        selected_index = self.items_bidding.curselection()
        if selected_index:
            selected_item = self.items_bidding.get(selected_index)
            current_bid = float(selected_item.split(" - ")[1][1:])
            new_bid = simpledialog.askfloat("Place Bid", f"Enter your bid for {selected_item}:",
                                            minvalue=current_bid + 0.01)
            if new_bid is not None:
                bidder_name = self.user_name
                item_name = selected_item.split(' - ')[0]
                current_highest_bid = self.get_highest_bid(item_name)
                if new_bid > current_highest_bid:
                    self.update_highest_bid(item_name, new_bid, bidder_name)
                    updated_item = f"{item_name} - ₱{new_bid:.2f} - Bidder: {bidder_name}"
                    self.items_bidding.insert(END, updated_item)
                    self.show_highest_bids()
                    payload = {'Action': 'Bidding', 'Item': item_name, 'New Bid': new_bid,
                               'Bidder Name': bidder_name, 'Seller': self.user_name}
                    self.publish_payload(payload, 'echo')
                    print(f"Placed bid for item: {selected_item} - New Bid: ₱{new_bid:.2f} - "
                          f"Highest Bid: ₱{new_bid:.2f} - Bidder: {bidder_name}")
                else:
                    print("Your bid is not higher than the current highest bid.")

    def get_highest_bid(self, item):
        return self.highest_bids.get(item, 0.0)

    def update_highest_bid(self, item, bid, bidder_name):
        current_bid = self.get_highest_bid(item)
        self.highest_bids[item] = max(current_bid, bid)
        self.bidders_names[item] = bidder_name

    def show_highest_bids(self):
        self.highest_bidder_list.delete(0, END)
        for item, bid in self.highest_bids.items():
            bidder_name = self.bidders_names.get(item, "Unknown Bidder")
            self.highest_bidder_list.insert(END, f" Bidder: {bidder_name} - {item} - ₱{bid:.2f} ")

    def update_user_countdown(self, formatted_time):
        self.countdown_label.config(text=f"Countdown: {formatted_time}")

    def show_highest_bidders_popup(self):
        popup = Toplevel(self.root)
        popup.title("Winners")
        popup.geometry("400x400")  # Set the size of the popup window

        Label(popup, text="Winners", font=("Helvetica", 16, "bold")).pack(pady=10)

        for item, bid in self.highest_bids.items():
            bidder_name = self.bidders_names.get(item, "Unknown Bidder")
            Label(popup, text=f"Item: {item}", font=("Helvetica", 12, "bold")).pack(pady=5)
            Label(popup, text=f"Highest Bid: ₱{bid:.2f}", font=("Helvetica", 10)).pack()
            Label(popup, text=f"Bidder: {bidder_name}", font=("Helvetica", 10)).pack()
            Label(popup, text="-------------------------", font=("Helvetica", 10)).pack()

        Button(popup, text="Close", command=popup.destroy).pack(pady=10)

    def send_timer_info_to_server(self):
        payload = {'Action': 'SetTimer', 'TimerValue': self.timer_seconds, 'Seller': self.user_name}
        self.publish_payload(payload, 'your_server_topic')  # Replace 'your_server_topic' with the actual server topic

    def update_timer(self):
        if self.timer_active and self.timer_seconds > 0:
            self.timer_seconds -= 1
            self.update_timer_display()
            self.root.after(1000, self.update_timer)
        elif self.timer_seconds == 0:
            self.timer_active = False
            self.disable_buttons()  # Disable the buttons when the timer reaches 0
            # Add any additional logic you want to execute when the timer reaches 0



    def update_timer_display(self):
        formatted_time = time.strftime("%M:%S", time.gmtime(self.timer_seconds))
        self.countdown_label.config(text=f"Time Left: {formatted_time} seconds")

    def start_timer(self):
        if self.timer_seconds > 0:
            self.timer_active = True
            self.enable_buttons()  # Enable the buttons when the timer starts
            self.update_timer()  # Start the countdown immediately


    def get_message(self):
        try:
            data = self.subscriber.recv_multipart(zmq.NOBLOCK)
            self.incoming_message_processing(data[0].decode(), msgpack.unpackb(data[1]))
            time.sleep(0.001)
            self.root.after(1, self.get_message)
        except zmq.error.Again:
            try:
                time.sleep(0.001)
                self.root.after(1, self.get_message)
            except KeyboardInterrupt:
                self.root.destroy()
                self.publisher.close()
                self.subscriber.close()
                self.my_context.term()
                sys.exit(0)
        except KeyboardInterrupt:
            self.root.destroy()
            self.publisher.close()
            self.subscriber.close()
            self.my_context.term()
            sys.exit(0)


def gui_client():
    client = TkEchoClient()
    client.get_message()
    client.root.mainloop()

if __name__ == '__main__':
    gui_client()
