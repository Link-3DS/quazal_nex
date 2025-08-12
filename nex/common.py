from nex import streams
from nex import settings
from nex.errors import ERROR_MASK
import time


class Structure(settings.Settings):
    def __init__(self):
        super().__init__()
        self.structure_version = 0

    def encode(self, stream, content_size):
        if self.use_structure_header:
            stream.u8(self.structure_version)
            stream.u32(content_size)

    def decode(self, stream):
        if self.use_structure_header:
            version = stream.u8()
            content_size = stream.u32()

            if stream.available() < content_size:
                raise Exception("Structure content size longer than data size")

            self.structure_version = version


class Data(Structure):
    def encode(self, stream): pass
    def decode(self, stream): pass


# TODO: Change this
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
        self.special_station = None
        self.time = DateTime(0)

    def encode(self, stream):
        stream.string(self.station)
        stream.u8(self.special_protocols)
        stream.string(self.special_station)

        if self.nex_version >= 30500:
            self.structure_version = 1
            stream.datetime(self.time)

        return stream.get()

    def decode(self, stream):
        self.station = stream.string()
        self.special_protocols = stream.u8()
        self.special_station = stream.string()

        if self.nex_version >= 30500:
            self.structure_version = 1
            self.time = stream.datetime()

        return stream.get()


class DateTime:
    def __init__(self, value):
        self.value = value

    def make(self, year, month, day, hour, minute, second):
        self.value = (second | (minute << 6) | (hour << 12) | 
                      (day << 17) | (month << 22) | (year << 26))
        return self

    def from_timestamp(self, timestamp: time.struct_time):
        year = timestamp.tm_year
        month = timestamp.tm_mon
        day = timestamp.tm_mday
        hour = timestamp.tm_hour
        minute = timestamp.tm_min
        second = timestamp.tm_sec

        return self.make(year, month, day, hour, minute, second)

    def now(self): 
        return self.from_timestamp(time.gmtime())

    def get(self): 
        return self.value

    def second(self): return self.value & 63
    def minute(self): return (self.value >> 6) & 63
    def hour(self): return (self.value >> 12) & 31
    def day(self): return (self.value >> 17) & 31
    def month(self): return (self.value >> 22) & 15
    def year(self): return self.value >> 26

    def standard(self):
        return time.mktime((self.year(), self.month(), self.day(),
                             self.hour(), self.minute(), self.second(), 0, 0, 0))
    

class StationURL:
    def __init__(self):
        pass


class Result:
    def __init__(self, code):
        self.error_code = code

    def is_success(self):
        return not self.error_code&ERROR_MASK
    
    def is_error(self):
        return bool(self.error_code&ERROR_MASK)
    
    def decode(self, stream):
        error_code = stream.u32()
        self.error_code = error_code

    def encode(self, stream):
        stream.u32(self.error_code)
        return stream.get()


class ResultRange(Structure):
    def __init__(self, offset, size):
        self.offset = offset
        self.size = size

    def encode(self, stream):
        stream.u32(self.offset)
        stream.u32(self.size)

    def decode(self, stream):
        self.offset = stream.u32()
        self.size = stream.u32()
