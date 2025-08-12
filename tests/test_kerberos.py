from nex import kerberos


def test_kerberos():
    password = b"password"
    pid = 2
    kerb = kerberos.derive_key(pid, password)
    print(kerb)
