import socket


class Socket:
	UDP = 0
	TCP = 1

	def __init__(self, type):
		if type == self.UDP:
			self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		else:
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
		self.s.setblocking(False)
		
	def connect(self, host, port): self.s.connect((host, port))
	def bind(self, host, port): self.s.bind((host, port))
	def close(self): self.s.close()
	def send(self, data): self.s.sendall(data)
	def recv(self, num=2048):
		try:
			return self.s.recv(2048)
		except BlockingIOError:
			pass
			
	def get_address(self): return self.s.getsockname()[0]
	def get_port(self): return self.s.getsockname()[1]
