from __future__ import unicode_literals
from tkinter import messagebox
import time


try:
    from tkinter import *
    from tkinter import font
    from tkinter import ttk
    from tkinter import simpledialog
except ImportError:
    from Tkinter import *
    import tkFont as font
    import ttk


import msgpack
import zmq
from python_banyan.banyan_base import BanyanBase

class TkEchoClient(BanyanBase):

    def __init__(self,topics='reply',back_plane_ip_address=None, subscriber_port='43125',
                 publisher_port='43124', process_name='Auction IO'):
        # Prompt the user for their name
        self.user_name = simpledialog.askstring("Your Name", "Enter your name:")
        if not self.user_name:
            sys.exit(0)  # Exit if the user cancels the input


        # Call the constructor of BanyanBase to initialize the publisher
        super(TkEchoClient, self).__init__(back_plane_ip_address=back_plane_ip_address,
                                           subscriber_port=subscriber_port,
                                           publisher_port=publisher_port,
                                           process_name=process_name)
        
        # Set the subscriber topics
        if topics is None:
            raise ValueError('No Topic List Was Specified.')

        for x in topics:
            self.set_subscriber_topic(x)

        # Display a message on the server that the client is ready for auction
        ready_message = f"{self.user_name} is ready for auction"
        payload = {'Action': 'ReadyForAuction', 'Message': ready_message, 'Seller': self.user_name}
        self.publish_payload(payload, 'echo')

        # ... (your existing __init__ code)

        # ... (your existing GUI setup code)
        # establish some banyan variables
        self.back_plane_ip_address = back_plane_ip_address
        self.subscriber_port = subscriber_port
        self.publisher_port = publisher_port

        # subscribe to the topic
        if topics is None:
            raise ValueError('No Topic List Was Specified.')

        # initialize the banyan base class
        super(TkEchoClient, self).__init__(back_plane_ip_address=back_plane_ip_address,
                                           subscriber_port=subscriber_port,
                                           publisher_port=publisher_port,
                                           process_name=process_name)

        # subscribe to all topics specified
        for x in topics:
            self.set_subscriber_topic(x)

        # setup root window
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

        self.sell_button = ttk.Button(self.display_sell_frame, text="Sell", command=None, state="normal")
        self.sell_button.grid(row=1, column=0, padx=(5, 0), pady=10, sticky="w")

        self.delete_sell_button = ttk.Button(self.display_sell_frame, text="Delete", command=None,
                                             state="normal")
        self.delete_sell_button.grid(row=1, column=1, padx=(0, 5), pady=10, sticky="e")

        # Adjust column weights
        self.display_sell_frame.columnconfigure(0, weight=1)
        self.display_sell_frame.columnconfigure(1, weight=1)

        self.display_bid_frame = ttk.LabelFrame(self.frame, text="Items Bidding")
        self.display_bid_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.items_bidding = Listbox(self.display_bid_frame, width=50, height=10)
        self.items_bidding.grid(row=0, column=0, padx=10, pady=10)

        self.bid_button_bidding = ttk.Button(self.display_bid_frame, text="Bid", command=None, state="normal")
        self.bid_button_bidding.grid(row=1, column=0, padx=10, pady=10)

        self.highest_bidder_frame = ttk.LabelFrame(self.frame, text="Highest Bidder")
        self.highest_bidder_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.highest_bidder_list = Listbox(self.highest_bidder_frame, width=110, height=10)
        self.highest_bidder_list.grid(row=0, column=0, padx=10, pady=10, sticky="nsew", columnspan=2)

        self.sell_button.config(command=self.place_sell)
        self.delete_sell_button.config(command=self.delete_sell_item)
        self.bid_button_bidding.config(command=self.place_bid)

        self.highest_bids = {}
        self.bidders_names = {}

        # self.root.after(2, self.place_sell)

        # Adjust column weights

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

    # Add the following method to your TkEchoClient class
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



    def get_message(self):
        """
        This method is called from the tkevent loop "after" call. It will poll for new zeromq messages
        :return:
        """
        try:
            data = self.subscriber.recv_multipart(zmq.NOBLOCK)
            self.incoming_message_processing(data[0].decode(), msgpack.unpackb(data[1]))
            time.sleep(.001)
            self.root.after(1, self.get_message)

        except zmq.error.Again:
            try:
                time.sleep(.001)
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


    def on_closing(self):
        """
        Destroy the window
        :return:
        """
        self.clean_up()
        self.root.destroy()


def gui_client():
    client = TkEchoClient()
    # Add the main loop
    client.root.mainloop()


if __name__ == '__main__':
    gui_client()
