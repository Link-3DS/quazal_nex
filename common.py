class Structure:
    pass # TODO - Finish the Structure class


class Data(Structure):
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
