

class Channel:
    def __init__(self, channels):
        self.channels = {}
        self.users_online = set()

        for channel in channels:
            self.channels[channel] = set()

    def add_user(self, user, channel):
        self.channels[channel].add(user)

    def remove_user(self, user, channel):
        self.channels[channel].discard(user)

