import streams, struct


ERROR_MASK = 1 << 31


class RMCMessage:
    def __init__(self):
        self.is_request = False
        self.is_success = False
        self.protocol_id = None
        self.call_id = None
        self.method_id = None
        self.error_code = None
        self.method_parameters = b""

    @staticmethod
    def request():
        inst = RMCMessage()
        inst.is_request = True
        return inst

    @staticmethod
    def success(method_paramaters):
        inst = RMCMessage()
        inst.is_request = False
        inst.is_success = True
        inst.method_parameters = method_paramaters
        return inst

    @staticmethod
    def error(error_code):
        inst = RMCMessage()
        if error_code & ERROR_MASK == 0:
            error_code |= ERROR_MASK

        inst.is_request = False
        inst.is_success = False
        inst.error_code = error_code
        return inst

    def encode(self):
        stream = streams.StreamOut()

        flag = 0x80 if self.is_request else 0

        if self.protocol_id < 0x80:
            stream.u8(self.protocol_id | flag)
        else:
            stream.u8(0x7F | flag)
            stream.u16(self.protocol_id)

        if self.is_request:
            stream.u32(self.call_id)
            stream.u32(self.method_id)
            stream.write(self.method_parameters)
        else:
            if self.is_success:
                stream.bool(True)
                stream.u32(self.call_id)
                stream.u32(self.method_id | 0x8000)
                stream.write(self.method_parameters)
            else:
                stream.bool(False)
                stream.u32(self.error_code)
                stream.u32(self.call_id)
        return struct.pack("I", stream.size()) + stream.get()


    def decode(self, data):
        stream = streams.StreamIn(data)

        length = stream.u32()
        if length != stream.size() - 4:
            raise ValueError("RMC Message has unexpected size")
        
        protocol_id = stream.u8()

        self.protocol_id = protocol_id & ~0x80

        if self.protocol_id == 0x7F:
            self.protocol_id = stream.u16()

        if protocol_id&0x80:
            self.is_request = True
            self.call_id = stream.u32()
            self.method_id = stream.u32()
            self.method_parameters = stream.readall()
        else:
            self.is_request = False

            if stream.bool():
                self.call_id = stream.u32()
                self.method_id = stream.u32() & ~0x8000
                self.method_parameters = stream.readall()
            else:
                self.error_code = stream.u32()
                self.call_id = stream.u32()
