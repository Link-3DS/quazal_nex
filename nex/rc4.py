class RC4Cipher:
    def __init__(self, key):
        self.key = key
        self.s = list(range(256))
        j = 0
        for i in range(256):
            j = (j + self.s[i] + self.key[i % len(self.key)]) % 256
            self.s[i], self.s[j] = self.s[j], self.s[i]
        self.i = 0
        self.j = 0
    
    def keystream(self):
        self.i = (self.i + 1) % 256
        self.j = (self.j + self.s[self.i]) % 256
        self.s[self.i], self.s[self.j] = self.s[self.j], self.s[self.i]
        return self.s[(self.s[self.i] + self.s[self.j]) % 256]

    def encrypt(self, data):
        return bytes(byte ^ self.keystream() for byte in data)

    def decrypt(self, data):
        return self.encrypt(data)
