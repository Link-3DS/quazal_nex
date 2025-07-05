from anynet import streams


class StreamOut(streams.StreamOut):
    def __init__(self):
        super().__init__("<")


class StreamIn(streams.StreamIn):
    def __init__(self, data):
        super().__init__(data, "<")