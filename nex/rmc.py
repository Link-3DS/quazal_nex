from nex import streams


class RMCMessage:
    def __init__(self, request=False, success=False):
        self.request = request
        self.success = success
        self.protocol_id = None
        self.call_id = None
        self.method_id = None
        self.error_code = 0
        self.method_parameters = b""

    def encode(self):
        stream = streams.StreamOut()

        protocol_flag = 0x80 if self.request else 0

        if self.protocol_id < 0x80:
            stream.u8(self.protocol_id | protocol_flag)
        else:
            stream.u8(0x7F | protocol_flag)
            stream.u16(self.protocol_id)

        if self.request:
            stream.u32(self.call_id)
            stream.u32(self.method_id)
            stream.write(self.method_parameters)
        else:
            if self.success:
                stream.bool(True)
                stream.u32(self.call_id)
                stream.u32(self.method_id | 0x8000)
                stream.write(self.method_parameters)
            else:
                stream.bool(False)
                stream.u32(self.error_code)
                stream.u32(self.call_id)
        
        serialized = stream.get()

        message = streams.StreamOut()
        message.u32(len(serialized))
        message.write(serialized)

        return message.get()

    def decode(self, data):
        stream = streams.StreamIn(data)

        length = stream.u32()
        if length != stream.size() - 4:
            raise ValueError("RMC message has unexpected size")

        protocol_id = stream.u8()
        self.protocol_id = protocol_id & ~0x80
        if self.protocol_id == 0x7F:
            self.protocol_id = stream.u16()

        if protocol_id & 0x80 != 0:
            self.request = True
            self.call_id = stream.u32()
            self.method_id = stream.u32()
            self.method_parameters = stream.readall()
        else:
            self.request = False
            self.success = stream.bool()

            if self.success:
                self.call_id = stream.u32()
                self.method_id = stream.u32()
                self.method_id = self.method_id & ~0x8000
                self.method_parameters = stream.readall()
            else:
                self.error_code = stream.u32()
                self.call_id = stream.u32()
