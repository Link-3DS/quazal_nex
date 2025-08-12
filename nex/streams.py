# TODO: Use another stream library that does the same task

from nex import common
from anynet import streams


class StreamOut(streams.StreamOut):
	def __init__(self):
		super().__init__("<")

	def string(self, string):
		if string is None:
			self.u16(0)
		else:
			data = (string + "\0").encode("utf8")
			self.u16(len(data))
			self.write(data)

	def buffer(self, data):
		self.u32(len(data))
		self.write(data)

	def datetime(self, datetime):
		self.u64(datetime.get())
		
		
class StreamIn(streams.StreamIn):
	def __init__(self, data):
		super().__init__(data, "<")

	def string(self):
		length = self.u16()
		if length:
			return self.read(length).decode("utf8")[:-1]

	def buffer(self): return self.read(self.u32())

	def datetime(self):
		return common.DateTime(self.u64())
