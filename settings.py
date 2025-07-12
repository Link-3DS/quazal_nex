import common


class Settings:
    def __init__(self):
        self.access_key = "".encode()
        self.prudp_version = 0
        self.nex_version = None
        self.fragment_size = 1300
        self.kerberos_key_size = 32
        self.kerberos_key_derivation = None
        self.kerberos_ticket_version = 0
        self.counter = common.SeqCounter(10)
        self.session_key = None