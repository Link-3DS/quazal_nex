from nex import prudp


def test_packets():
    pkt_v0 = prudp.PRUDPPacketV0()
    pkt_v0.quazal = False
    pkt_v0.source_type = 1
    pkt_v0.source_port = 2
    pkt_v0.destination_type = 3
    pkt_v0.destination_port = 4
    pkt_v0.type = 5
    pkt_v0.flags = 6
    pkt_v0.signature = b"\x00" * 16
    pkt_v0.connection_signature = b""
    pkt_v0.payload = b""
    encoded_v0 = pkt_v0.encode()
    print(f"Encoded Packet V0 Bytes: {encoded_v0}")
    print(f"Encoded Packet V0 Hex: {encoded_v0.hex()}")

    pkt_v1 = prudp.PRUDPPacketV1()
    pkt_v1.source_type = 1
    pkt_v1.source_port = 2
    pkt_v1.destination_type = 3
    pkt_v1.destination_port = 4
    pkt_v1.type = 5
    pkt_v1.flags = 6
    pkt_v1.signature = b"\x00" * 16
    pkt_v1.connection_signature = b""
    pkt_v1.payload = b""
    encoded_v1 = pkt_v1.encode()
    print(f"Encoded Packet V1 Bytes: {encoded_v1}")
    print(f"Encoded Packet V1 Hex: {encoded_v1.hex()}")
