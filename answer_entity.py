from utils import get_current_seconds


class Answer:
    def __init__(self, answer_type, ttl, data):
        self.type = answer_type
        self.ttl = int(ttl, 16) + get_current_seconds()
        self.data = data

    def create_ttl(self):
        current_time = get_current_seconds()
        return hex(self.ttl - current_time)[2:].rjust(8, '0')

    def create_length(self):
        return hex(len(self.data) // 2)[2:].rjust(4, '0')

    def create_response(self):
        return 'c00c' + self.type + '0001' + self.create_ttl() + self.create_length() + self.data
