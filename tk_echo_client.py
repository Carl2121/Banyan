#tk_echo_client.py
from __future__ import unicode_literals

import time


try:
    from tkinter import *
    from tkinter import font
    from tkinter import ttk
except ImportError:
    from Tkinter import *
    import tkFont as font
    import ttk


import msgpack
import zmq
from python_banyan.banyan_base import BanyanBase


class TkEchoClient(BanyanBase):
    """
    A graphical echo client.
    """

    def __init__(self,topics='reply', number_of_messages=10,
                 back_plane_ip_address=None, subscriber_port='43125',
                 publisher_port='43124', process_name='Auction IO'):
        """

        :param topics: A list of topics to subscribe to
        :param number_of_messages: Default number of echo messages to send
        :param back_plane_ip_address:
        :param subscriber_port:
        :param publisher_port:
        :param process_name:
        """

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
        self.root.title("Auction.IO | Client")

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

        # messages to be sent
        # self.messages_to_be_sent = StringVar()
        # self.messages_to_be_sent.set(str(number_of_messages))
        #
        # # messages sent count
        # self.message_sent_count = 0
        # self.messages_sent = StringVar()
        # self.messages_sent.set(str(self.message_sent_count))






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

    def incoming_message_processing(self, topic, payload):
        # When a message is received and its number is zero, finish up.
        if self.message_number == 0:
            self.messages_sent.set(str(self.number_of_messages))

        # bump the message number and send the message out
        else:
            self.message_number -= 1
            self.message_sent_count += 1
            self.messages_sent.set(str(self.message_sent_count))
            self.publish_payload({'message_number': self.message_number}, 'echo')

    def send(self, *args):
        msgs = self.to_send_entry.get()
        # reset the sent count variables to zero
        self.message_sent_count = 0
        self.messages_sent.set(str(self.message_sent_count))

        # set current message number to the number of messages to be sent
        self.message_number = int(msgs)

        # update the number of messages to be sent
        self.number_of_messages = int(msgs)
        self.publish_payload({'message_number': int(msgs)}, 'echo')

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
