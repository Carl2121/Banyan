import sys
from python_banyan.banyan_base import BanyanBase


class EchoServer(BanyanBase):
    def __init__(self):

        super(EchoServer, self).__init__(process_name='EchoServer')

        self.set_subscriber_topic('echo')

        try:
            self.receive_loop()
        except KeyboardInterrupt:
            self.clean_up()
            sys.exit(0)

    def incoming_message_processing(self, topic, payload):
        action = payload.get('Action', None)

        if action == 'Selling':
            print('[SERVER]', payload)
            # Process the payload and perform necessary actions

            # Republish the message with a topic of 'reply'
            self.publish_payload(payload, 'reply')
        elif action == 'delete_sell':
            print('Received delete_sell request:', payload)
            # Process the payload and perform necessary actions

            # Republish the message with a topic of 'reply'
            self.publish_payload(payload, 'reply')
        elif action == 'place_bid':
            print('Received place_bid request:', payload)
            # Process the payload and perform necessary actions

            # Republish the message with a topic of 'reply'
            self.publish_payload(payload, 'reply')


def echo_server():
    EchoServer()


if __name__ == '__main__':
    echo_server()
