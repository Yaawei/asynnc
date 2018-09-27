

class Channel:
    def __init__(self, channels):
        self.channels = {}
        for channel in channels:
            self.channels[channel] = set()

    def add_user(self, user, channel):
        self.channels[channel].add(user)

    def remove_user(self, user, channel):
        self.channels[channel].discard(user)

