import zlib, streams


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


# TODO - Change this
class DataHolder:
	object_map = {}

	def __init__(self):
		self.data = None
		
	def encode(self, stream):	
		stream.string(self.data.__class__.__name__)
		
		substream = streams.StreamOut()
		substream.add(self.data)
		
		stream.u32(len(substream.get()) + 4)
		stream.buffer(substream.get())
		
	def decode(self, stream):
		name = stream.string()
		substream = stream.substream().substream()
		self.data = substream.extract(self.object_map[name])
		
	@classmethod
	def register(cls, object, name):
		cls.object_map[name] = object


class RVConnectionData(Structure):
	def __init__(self):
		super().__init__()
		self.station = None
		self.special_protocols = []
		self.special_station_protocols = None
		self.server_time = DateTime(0)
	
	def encode(self, stream):
		stream.string(self.station)
		stream.u32(0)
		stream.string(self.special_station_protocols)
		stream.u64(self.server_time)


class DateTime:
    def __init__(self, value):
        self.value = value

    def second(self):
        return self.value & 63
    
    def minute(self):
        return (self.value >> 6) & 63
    
    def hour(self):
        return (self.value >> 12) & 31
    
    def day(self):
        return (self.value >> 17) & 31
    
    def month(self):
        return (self.value >> 22) & 15
    
    def year(self):
        return self.value >> 26
    
    def __repr__(self):
        return "%i-%i-%i %i:%02i:%02i" %(self.day(), self.month(), self.year(), self.hour(), self.minute(), self.second())
    
    @classmethod
    def make(cls, day, month, year, hour, minute, second):
        return cls(second | (minute << 6) | (hour << 12) | (day << 17) | (month << 22) | (year << 26))


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
