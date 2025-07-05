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
        pass # TODO - Finish this

    def decode(self):
        pass # TODO - Finish this