from nex import rc4


def test_rc4():
    key = b"mykey"

    plaintext = b"Hello"
    cipher = rc4.RC4Cipher(key)

    encrypted = cipher.encrypt(plaintext)
    print("Encrypted bytes:", encrypted)

    decipher = rc4.RC4Cipher(key)

    decrypted = decipher.decrypt(encrypted)
    print("Decrypted:", decrypted)
