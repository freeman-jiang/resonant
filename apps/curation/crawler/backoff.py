class ExponentialBackoff:
    def __init__(self):
        self.count = 1

    def reset(self):
        self.count = 1

    def backoff(self):
        self.count += 1
        return min(2 ** self.count, 5)
