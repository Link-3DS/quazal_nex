from nex import streams
from nex import settings
import socket 
import struct 
import hmac 
import hashlib 


SYN_PACKET = 0
CONNECT_PACKET = 1
DATA_PACKET = 2
DISCONNECT_PACKET = 3
PING_PACKET = 4
USER_PACKET = 5
ROUTE_PACKET = 6
RAW_PACKET = 7

FLAG_ACK = 1
FLAG_RELIABLE = 2
FLAG_NEED_ACK = 4
FLAG_HAS_SIZE = 8
FLAG_MULTI_ACK = 0x200


class PRUDPPacket(settings.Settings):
    def __init__(self, type=None, flags=None):
        super().__init__()
        self.version = None
        self.source_type = None
        self.source_port = None
        self.destination_type = None
        self.destination_port = None
        self.type = type
        self.flags = flags
        self.session_id = 0
        self.substream_id = 0
        self.sequence_id = 0
        self.fragment_id = 0
        self.connection_signature = None
        self.signature = None
        self.payload = b""


class PRUDPPacketV0(PRUDPPacket):
    def __init__(self):
        super().__init__()

    def calc_checksum(self, data):
        checksum = sum(self.access_key)
        if self.quazal:
            data = data.ljust((len(data) + 3) & ~3, b"\0")
            words = struct.unpack("<%iI" %(len(data) // 4), data)
            return ((checksum & 0xFF) + sum(words)) & 0xFFFFFFFF
        else:
            words = struct.unpack_from("<%iI" %(len(data) // 4), data)
            temp = sum(words) & 0xFFFFFFFF
            checksum += sum(data[len(data) & ~3:])
            checksum += sum(struct.pack("<I", temp))
            return checksum & 0xFF
        
    def calc_data_signature(self, session_key):
        data = self.payload
        if self.access_key != "ridfebb9":
            header = struct.pack("<HB", self.sequence_id, self.fragment_id)
            data = session_key + header + data

        if data:
            key = hashlib.md5(self.access_key).digest()
            digest = hmac.digest(key, data, hashlib.md5)
            return digest[:4]
        return struct.pack("<I", 0x12345678)
    
    def calc_connection_signature(self, addr):
        data = socket.inet_aton(addr[0]) + struct.pack(">H", addr[1])
        return hashlib.md5(data).digest()[3::-1]
    
    def calc_signature(self, session_key, connection_signature):
        if self.type == DATA_PACKET:
            return self.calc_data_signature(session_key)
        if self.type == DISCONNECT_PACKET:
            return self.calc_data_signature(session_key)
        if connection_signature:
            return connection_signature
        return bytes(4)

    def encode(self):
        stream = streams.StreamOut()

        stream.u8(self.source_port | (self.source_type << 4))
        stream.u8(self.destination_port | (self.destination_type << 4))

        if self.quazal:
            stream.u8(self.type | (self.flags << 3))
        else:
            stream.u16(self.type | (self.flags << 4))

        stream.u8(self.session_id)
        stream.write(self.signature)
        stream.u16(self.sequence_id)

        if self.type == SYN_PACKET or self.type == CONNECT_PACKET:
            stream.write(self.connection_signature)
        if self.type == DATA_PACKET:
            stream.u8(self.fragment_id)

        if self.flags & FLAG_HAS_SIZE:
            stream.u16(len(self.payload))

        stream.write(self.payload)

        checksum = self.calc_checksum(stream.get())

        if self.quazal:
            stream.u32(checksum)
        else:
            stream.u8(checksum)

        return stream.get()

    def decode(self, data):
        stream = streams.StreamIn(data)

        start = stream.tell()

        source = stream.u8() 
        destination = stream.u8()

        self.source_type = source >> 4
        self.source_port = source & 0xF
        self.destination_type = destination >> 4
        self.destination_port = destination & 0xF

        if self.quazal:
            type_flags = stream.u8()
            self.flags = type_flags >> 3
            self.type = type_flags & 7
        else:
            type_flags = stream.u16()
            self.flags = type_flags >> 4
            self.type = type_flags & 0xF

        self.session_id = stream.u8()
        self.signature = stream.read(4)
        self.sequence_id = stream.u16()

        if self.type in [SYN_PACKET, CONNECT_PACKET]:
            self.connection_signature = stream.read(4)
        if self.type == DATA_PACKET:
            self.fragment_id = stream.u8()

        if self.flags & FLAG_HAS_SIZE:
            payload_size = stream.u16()
        else:
            if self.quazal:
                payload_size = stream.available() - 4
            else:
                payload_size = stream.available() - 1

        self.payload = stream.read(payload_size)

        end = stream.tell()

        checksum_data = stream.get()[start:end]

        calculated_checksum = self.calc_checksum(checksum_data)

        if self.quazal:
            checksum = stream.u32()
        else:
            checksum = stream.u8()

        if checksum != calculated_checksum:
            raise ValueError("Invalid checksum (calculated %i, got %i)" %(calculated_checksum, checksum))


class PRUDPPacketV1(PRUDPPacket):
    def __init__(self):
        super().__init__()
        self.minor_version = 0
        self.supported_functions = 0
        self.max_substream_id = 0
        self.initial_seq_id = 0

    def calc_signature(self, session_key, connection_signature):
        options = self.encode_options()
        header = self.encode_header(len(options))

        key = hashlib.md5(self.access_key).digest()
        mac = hmac.new(key, digestmod=hashlib.md5)
        mac.update(header[4:])
        mac.update(session_key)
        mac.update(struct.pack("<I", sum(self.access_key)))
        mac.update(connection_signature)
        mac.update(options)
        mac.update(self.payload)
        return mac.digest()
    
    def calc_connection_signature(self, addr):
        key = bytes.fromhex("26c31f381e46d6eb38e1af6ab70d11")
        data = socket.inet_aton(addr[0]) + struct.pack(">H", addr[1])
        return hmac.digest(key, data, hashlib.md5)

    def encode_options(self):
        option_stream = streams.StreamOut()

        if self.type == SYN_PACKET or self.type == CONNECT_PACKET:
            option_stream.u8(0)
            option_stream.u8(4)
            option_stream.u32(self.minor_version | (self.supported_functions << 8))

            option_stream.u8(1)
            option_stream.u8(16)
            option_stream.write(self.connection_signature)

            if self.type == CONNECT_PACKET:
                option_stream.u8(3)
                option_stream.u8(2)
                option_stream.u16(self.initial_seq_id)

            option_stream.u8(4)
            option_stream.u8(1)
            option_stream.u8(self.max_substream_id)

        elif self.type == DATA_PACKET:
            option_stream.u8(2)
            option_stream.u8(1)
            option_stream.u8(self.fragment_id)

        return option_stream.get()

    def decode_options(self, data):
        option_stream = streams.StreamIn(data)

        option_id = option_stream.u8()

        if self.type == SYN_PACKET or self.type == CONNECT_PACKET:
            if option_id == 0:
                self.supported_functions = option_stream.u32()
                self.minor_version = self.supported_functions & 0xFF
                self.supported_functions = self.supported_functions >> 8
            if option_id == 1:
                self.connection_signature = option_stream.read(16)
            if option_id == 4:
                self.max_substream_id = option_stream.u8()
        if self.type == CONNECT_PACKET:
            if option_id == 3:
                self.initial_seq_id = option_stream.u16()    
        if self.type == DATA_PACKET:
            if option_id == 2:
                self.fragment_id = option_stream.u8()

    def encode_header(self, option_size):
        stream = streams.StreamOut()

        stream.u8(1)
        stream.u8(option_size)
        stream.u16(len(self.payload))
        stream.u8(self.source_port | (self.source_type << 4))
        stream.u8(self.destination_port | (self.destination_type << 4))
        stream.u16(self.type | (self.flags << 4))
        stream.u8(self.session_id)
        stream.u8(self.substream_id)
        stream.u16(self.sequence_id)
        
        return stream.get()

    def encode(self):
        options = self.encode_options()
        option_size = len(options)

        header = self.encode_header(option_size)

        stream = streams.StreamOut()

        stream.write(b"\xEA\xD0")
        stream.write(header)
        stream.write(self.signature)
        stream.write(options)
        stream.write(self.payload)

        return stream.get()

    def decode(self, data):
        stream = streams.StreamIn(data)

        magic = stream.read(2)
        if magic != b"\xEA\xD0":
            raise ValueError("Invalid magic number")
        
        version = stream.u8()
        if version != 1:
            raise ValueError("Invalid Version")
        
        option_size = stream.u8()
        payload_size = stream.u16()

        source = stream.u8()
        destination = stream.u8()

        self.source_type = source >> 4
        self.source_port = source & 0xF
        self.destination_type = destination >> 4
        self.destination_port = destination & 0xF

        type_flags = stream.u16()

        self.flags = type_flags >> 4
        self.type = type_flags & 0xF

        self.session_id = stream.u8()
        self.substream_id = stream.u8()
        self.sequence_id = stream.u8()

        self.signature = stream.read(16)

        option_data = stream.read(option_size)
        self.decode_options(option_data)

        self.payload = stream.read(payload_size)


class PRUDPClient(settings.Settings):
    def __init__(self):
        super().__init__()
