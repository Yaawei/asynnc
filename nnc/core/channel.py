

class Channel:
    def __init__(self, channel):
        self.channel = channel
        self.users_online = set()

    def add_user(self, user):
        self.users_online.add(user)

    def remove_user(self, user):
        self.users_online.discard(user)

