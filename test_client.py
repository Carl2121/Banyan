import sys
from python_banyan.banyan_base import BanyanBase


class EchoClient(BanyanBase):
    """
    This is a simple echo client derived from the BanyanBase class.
    It sends out a series of messages and expects an
    echo reply from the server.
    """

    def __init__(self):

        # initialize the parent
        super(EchoClient, self).__init__(process_name='EchoClient')

        # accept banyan messages with the topic of reply
        self.set_subscriber_topic('reply')

        # sequence number of messages and total number of messages to send
        self.message_number = self.number_of_messages = 10

        # send the first message - make sure that the server is already started
        self.publish_payload({'message_number': self.message_number}, 'echo')

        # get the reply messages
        try:
            self.receive_loop()
        except KeyboardInterrupt:
            self.clean_up()
            sys.exit(0)

    def incoming_message_processing(self, topic, payload):
        """
        Process incoming messages received from the echo client
        :param topic: Message Topic string
        :param payload: Message Data
        """

        # When a message is received and its number is zero, finish up.
        if payload['message_number'] == 0:
            print(str(self.number_of_messages) + ' messages sent and received. ')
            input('Press enter to exit.')
            self.clean_up()
            sys.exit(0)
        # bump the message number and send the message out
        else:
            self.message_number -= 1
            if self.message_number >= 0:
                self.publish_payload({'message_number': self.message_number}, 'echo')

