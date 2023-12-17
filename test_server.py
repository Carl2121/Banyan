import sys
from python_banyan.banyan_base import BanyanBase


class EchoServer(BanyanBase):
    """
    This class is a simple Banyan echo server
    """

    def __init__(self, ):

        # initialize the parent
        super(EchoServer, self).__init__(process_name='EchoServer')

        # subscribe to receive 'echo' messages from the client
        self.set_subscriber_topic('echo')

        # wait for messages to arrive
        try:
            self.receive_loop()
        except KeyboardInterrupt:
            self.clean_up()
            sys.exit(0)

    def incoming_message_processing(self, topic, payload):
        """
        Process incoming messages from the client
        :param topic: message topic
        :param payload: message payload
        """
        # republish the message with a topic of reply
        self.publish_payload(payload, 'reply')

        # extract the message number from the payload
        print('Message number:', payload['message_number'])
