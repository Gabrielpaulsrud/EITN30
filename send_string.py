import time
import struct
import board
from digitalio import DigitalInOut

# if running this on a ATSAMD21 M0 based board
# from circuitpython_nrf24l01.rf24_lite import RF24
from circuitpython_nrf24l01.rf24 import RF24

# invalid default values for scoping
SPI_BUS, CSN_PIN, CE_PIN = (None, None, None)

import spidev

SPI_BUS = spidev.SpiDev()  # for a faster interface on linux
CSN_PIN = 0  # use CE0 on default bus (even faster than using any pin)
CE_PIN = DigitalInOut(board.D17)  # using pin gpio22 (BCM numbering)


# initialize the nRF24L01 on the spi bus object
nrf = RF24(SPI_BUS, CSN_PIN, CE_PIN)
# On Linux, csn value is a bit coded
#                 0 = bus 0, CE0  # SPI bus 0 is enabled by default
#                10 = bus 1, CE0  # enable SPI bus 2 prior to running this
#                21 = bus 2, CE1  # enable SPI bus 1 prior to running this

# set the Power Amplifier level to -12 dBm since this test example is
# usually run with nRF24L01 transceivers in close proximity
nrf.pa_level = -12

# addresses needs to be in a buffer protocol object (bytearray)
address = [b"1Node", b"2Node"]

MAX_PAYLOAD = 32
HEADER_SIZE = 4
CHUNK_SIZE = MAX_PAYLOAD - HEADER_SIZE

def send_long_string(text):

    radio_number = 1
    nrf.open_tx_pipe(address[radio_number])  # always uses pipe 0
    nrf.open_rx_pipe(1, address[not radio_number])  # using pipe 1
    nrf.listen = False

    data_bytes = text.encode('utf-8')
    total_chunks = (len(data_bytes) + CHUNK_SIZE - 1) // CHUNK_SIZE
    packet_id = 42  # Just an example, increment for each message

    for seq in range(total_chunks):
        start = seq * CHUNK_SIZE
        end = start + CHUNK_SIZE
        chunk = data_bytes[start:end]
        header = bytes([packet_id, total_chunks, seq, 0])  # last byte = flags or reserved
        packet = header + chunk
        nrf.send(packet)

def receive():

    radio_number = 0
    nrf.open_tx_pipe(address[radio_number])  # always uses pipe 0
    nrf.open_rx_pipe(1, address[not radio_number])  # using pipe 1
    nrf.listen = True

    message_parts = {}
    expected_chunks = None
    packet_id = None

    while True:
        if nrf.any():
            packet = nrf.read()
            pid, total, seq, _ = packet[:4]
            data = packet[4:]

            # First packet: set expectations
            if packet_id is None:
                packet_id = pid
                expected_chunks = total

            # Ignore other packet_ids
            if pid != packet_id:
                continue

            message_parts[seq] = data

            if len(message_parts) == expected_chunks:
                break  # Message complete

    nrf.listen = False
    
    # Reassemble message
    full_bytes = b''.join(message_parts[i] for i in sorted(message_parts))
    full_msg = full_bytes.decode('utf-8')
    print(f"Construced message of {expected_chunks} chunks:")
    print(full_msg)
