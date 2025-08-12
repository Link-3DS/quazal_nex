from nex import rmc


def test_rmc():
    msg = rmc.RMCMessage(request=True)

    msg.protocol_id = 1
    msg.call_id = 42
    msg.method_id = 123
    msg.method_parameters = b"Hello World"

    encoded_data = msg.encode()
    print(f"Encoded data: {encoded_data.hex()}")

    decoded_msg = rmc.RMCMessage()
    decoded_msg.decode(encoded_data)

    print("Mode:", "REQUEST" if msg.request else "RESPONSE")
    print("Protocol:", decoded_msg.protocol_id)
    print("Call ID:", decoded_msg.call_id)
    print("Method:", decoded_msg.method_id)
    print("Method Parameters:", decoded_msg.method_parameters)
