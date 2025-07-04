import zlib


class DummyCompression:
    def compress(self, data): 
        return data

    def decompress(self, data): 
        return data


class ZlibCompression:
    def compress(self, data):
        compressed = zlib.compress(data)
        ratio = int(len(data) / len(compressed) + 1)
        return bytes([ratio]) + compressed

    def decompress(self, data):
        if data[0] == 0:
            return data[1:]

        decompressed = zlib.decompress(data[1:])
        ratio = int(len(decompressed) / (len(data) - 1) + 1)
        if ratio != data[0]:
            raise ValueError("Unexpected compression ratio (expected %i, got %i)" %ratio, data[0])
        return decompressed


class Structure:
    def hierarchy(self):
        return [self]
    
    def encode(self, stream):
        pass
    
    def decode(self, stream):
        pass


class Data(Structure):
    def encode(self, stream):
        pass
    
    def decode(self, stream):
        pass


class StationURL:
    def __init__(self, scheme="prudp", **kwargs):
        self.scheme = scheme
        self.fields = {}
        self.set_fields(**kwargs)

    def set_fields(self, **kwargs):
        for k, v in kwargs.items():
            if v is not None:
                self.fields[k] = str(v)

    def get(self, key, default=None):
        return self.fields.get(key, default)

    def __str__(self):
        return f"{self.scheme}:/" + ';'.join(f"{k}={v}" for k, v in self.fields.items())

    @classmethod
    def from_url(cls, url):
        instance = cls()
        if not url.startswith(('prudp:', 'prudps:', 'udp:')):
            raise ValueError("Invalid Station URL scheme")

        parts = url.split('/', 1)
        instance.scheme = parts[0][:-1]

        if len(parts) > 1:
            for entry in parts[1].split(';'):
                if '=' in entry:
                    key, value = entry.split('=', 1)
                    instance.fields[key] = value
        return instance


class SeqCounter:
    def __init__(self, start=0):
        self.value = start

    def increment(self):
        self.value += 1
        return self.value
