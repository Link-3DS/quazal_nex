from nex import rc4
from nex import settings
from nex import streams
import hmac
import hashlib
import os


class KerberosEncryption:
    def __init__(self, key):
        self.key = key

    def validate(self, buffer):
        data = buffer[:-16] # 0x10
        checksum = buffer[-16:] # 0x10
        mac = hmac.new(self.key, data, hashlib.md5)
        return hmac.compare_digest(checksum, mac.digest())

    def decrypt(self, buffer):
        if not self.validate(buffer):
            raise ValueError("Invalid Kerberos checksum (incorrect password)")
        cipher = rc4.RC4Cipher(self.key)
        decrypted = cipher.decrypt(buffer[:-16]) # 0x10
        return decrypted

    def encrypt(self, buffer):
        cipher = rc4.RC4Cipher(self.key)
        encrypted = cipher.encrypt(buffer)
        mac = hmac.new(self.key, encrypted, hashlib.md5)
        checksum = mac.digest()
        return encrypted + checksum


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


class TicketInternalData(settings.Settings):
    def __init__(self):
        super().__init__()
        self.timestamp = None
        self.source = None
        self.session_key = None

    def encrypt(self, key):
        stream = streams.StreamOut()
        stream.datetime(self.timestamp)
        stream.u32(self.source)
        stream.write(self.session_key)
        data = stream.get()
        
        if self.kerberos_ticket_version == 1:
            ticket_key = os.urandom(16)
            hash_key = hashlib.md5(key + ticket_key).digest()
            encryption = KerberosEncryption(hash_key)
            encrypted = encryption.encrypt(data)
            final_stream = streams.StreamOut()
            final_stream.buffer(ticket_key)
            final_stream.buffer(encrypted)
            return final_stream.get()
        
        encryption = KerberosEncryption(key)
        return encryption.encrypt(data)

    def decrypt(self, key):
        if self.kerberos_ticket_version == 1:
            stream = streams.StreamIn(data)
            ticket_key = stream.buffer()
            data = stream.buffer()
            hash_key = hashlib.md5(key + ticket_key).digest()
            key = hash_key

        encryption = KerberosEncryption(key)
        decrypted = encryption.decrypt(stream.get())
        stream = streams.StreamIn(decrypted)

        self.timestamp = stream.datetime()
        self.source = stream.u32()
        self.session_key = stream.read(self.kerberos_key_size)


def derive_key(pid, password):
    key = password
    for _ in range(65000+pid%1024):
        key = hashlib.md5(key).digest()
    return key
