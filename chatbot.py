import fbchat
import markovify

import json
import sys

import secret

class UserBotClient(fbchat.Client):
    def __init__(self, thread_id, name="Bot", thread=None, reverse=False):
        try:
            cookies = json.loads(open('./cookies.json', 'r').read())
            print(cookies)
        except:
            cookies = None
            print(cookies)
        super().__init__(secret.MY_USERNAME, secret.MY_PASSWORD, session_cookies=cookies)

        if not (thread_id or thread):
            raise ValueError('Must specify either thread or thread_id')

        self.thread_id = thread_id
        self.thread = thread if thread else self.get_thread_by_id(thread_id)
        self.messages = self.thread['messages']
        self.name = name if name else self.thread['name']
        self.reverse = reverse
        self.mm = self.generate_markov(self.messages)

    def onMessage(self, author_id, message, thread_id, thread_type, **kwargs):
        self.markAsDelivered(author_id, thread_id)
        self.markAsRead(author_id)

        fbchat.log.info("==================================")
        fbchat.log.info("Message from {} in {} ({}): {}".format(author_id, thread_id, thread_type.name, message))
        fbchat.log.info("self.thread_id: {}".format(self.thread_id))

        # If you're not the author, echo
        if (str(author_id) == str(self.thread_id) or str(thread_id) == str(self.thread_id)) and author_id != self.uid:
            fbchat.log.info("RespOnding")
            self.sendMessage(self.make_sentence(), thread_id=thread_id, thread_type=thread_type)

    def get_thread_by_id(self, tid):
        # tid is an integer
        print('Fetching Thread')
        thread = self.fetchThreadInfo(str(tid))[str(tid)]
        print(thread)
        messages = self.fetchThreadMessages(thread_id=tid, limit=10000)
        messages.reverse()
        thread_info = {
            'name': thread.name if thread.name != "" else thread.uid,
            'messages': messages,
            'is_user': thread.type is fbchat.ThreadType.USER,
            'chat_length': len(messages),
            'init_date': messages[0].timestamp
        }
        return thread_info

    def generate_markov(self, message_list):
        print('Generating Model')
        text = '\n'.join([m.text for m in message_list if m.text and (m.author == self.uid) == self.reverse])
        text_model = markovify.NewlineText(input_text=text, state_size=3)
        print('Finished Model')
        return text_model

    def make_sentence(self):
        while True:
            sentence = self.mm.make_sentence()
            if sentence is not None:
                return sentence

    def chat(self):
        while True:
            input('You: ')
            print('{}: {}'.format(self.name, self.make_sentence()))

    def load_model(self, filename=None):
        if filename is None:
            filename = '{}.json'.format(self.thread_id)
        self.mm = markovify.NewlineText.from_json(open(filename, 'r').read())

    def save_model(self, filename=None):
        if filename is None:
            filename = '{}.json'.format(self.thread_id)
        open(filename, 'w').write(self.mm.to_json())

    def save_cookies(self, filename='./cookies.json'):
        open(filename, 'w').write(json.dumps(self.getSession()))

if __name__ == "__main__":
    args = sys.argv[1:]
    bot = UserBotClient(args[0], args[1])
    bot.chat()
