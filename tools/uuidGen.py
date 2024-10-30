import random

class UUID:
    def __init__(self):
        self.hex_chars = '0123456789abcdef'
        self.lengths = [8, 4, 4, 4, 12]  # Формат UUID: 8-4-4-4-12

    def generate_uuid(self):
        uuid = ''
        for length in self.lengths:
            for _ in range(length):
                uuid += random.choice(self.hex_chars)
            uuid += '-' if length != self.lengths[-1] else ''
        return uuid