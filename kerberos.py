from Crypto.Cipher import ARC4
import hashlib, hmac, secrets, streams, common, settings


class KerberosEncryption:
    def __init__(self, key):
        self.key = key
        self.rc4 = ARC4.new(self.key)

    def encrypt(self, buffer):
        encrypted = self.rc4.encrypt(buffer)
        mac = hmac.new(self.key, encrypted, digestmod=hashlib.md5)
        return encrypted + mac.digest()
    
    def decrypt(self, buffer):
        if not self.validate(buffer):
            raise ValueError("Kerberos hmac validation failed")

        offset = len(buffer)
        offset = offset - 0x10

        encrypted = buffer[:offset]

        decrypted = self.rc4.decrypt(encrypted)
        return decrypted
    
    def validate(self, buffer):
        data = buffer[:-0x10]
        checksum = buffer[-0x10:]
        mac = hmac.new(self.key, data, digestmod=hashlib.md5)
        return checksum == mac.digest()


class Ticket:
    def __init__(self):
        self.session_key = None
        self.target = None
        self.internal = b""

    def encrypt(self, key):
        stream = streams.StreamOut()
        encryption = KerberosEncryption(key)

        stream.write(self.session_key)
        stream.u32(self.target)
        stream.buffer(self.internal)

        return encryption.encrypt(stream.get())
    

class TicketInternal(settings.Settings):
    def __init__(self):
        super().__init__()
        self.timestamp = common.DateTime(0)
        self.user = None
        self.session_key = b""

    def encrypt(self, key):
        stream = streams.StreamOut()

        stream.u64(self.timestamp.value)
        stream.u32(self.user)
        stream.write(self.session_key)

        if self.kerberos_ticket_version == 1:
            ticket_key = secrets.token_bytes(16)
            final_key = hashlib.md5(key + ticket_key).digest()
            encryption = KerberosEncryption(final_key)
            encrypted = encryption.encrypt(stream.get())

            final_stream = streams.StreamOut()

            final_stream.buffer(ticket_key)
            final_stream.buffer(encrypted)

            return final_stream.get()
        else:
            encryption = KerberosEncryption(key)
            return encryption.encrypt(stream.get())
        
    def decrypt(self, data, key):
        stream = streams.StreamIn(data)
        
        if self.kerberos_ticket_version == 1:
            ticket_key = stream.buffer()
            data = stream.buffer()
            key = hashlib.md5(key + ticket_key).digest()

        encryption = KerberosEncryption(key)
        decrypted = encryption.decrypt(stream.get())

        stream = streams.StreamIn(decrypted)

        self.timestamp = stream.datetime()
        self.user = stream.u32()
        self.session_key = stream.read(self.kerberos_key_size)


def derive_kerberos_key(pid, password):
    key = password
    for i in range(65000+pid%1024):
        key = hashlib.md5(key).digest()
    return key
