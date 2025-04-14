import time
import struct
import board
import threading
from digitalio import DigitalInOut

# if running this on a ATSAMD21 M0 based board
# from circuitpython_nrf24l01.rf24_lite import RF24
from circuitpython_nrf24l01.rf24 import RF24

# invalid default values for scoping
SPI_BUS, CSN_PIN, CE_PIN = (None, None, None)
SPI_BUS2, CSN_PIN2, CE_PIN2 = (None, None, None)

import spidev

SPI_BUS = spidev.SpiDev()  # for a faster interface on linux
CSN_PIN = 0  # use CE0 on default bus (even faster than using any pin)
CE_PIN = DigitalInOut(board.D17)  # using pin gpio22 (BCM numbering)


SPI_BUS2 = spidev.SpiDev()
CSN_PIN2 = 10
CE_PIN2 =  DigitalInOut(board.D27)



# initialize the nRF24L01 on the spi bus object
nrf_tx = RF24(SPI_BUS, CSN_PIN, CE_PIN)
nrf_rx = RF24(SPI_BUS2, CSN_PIN2, CE_PIN2)

# On Linux, csn value is a bit coded
#                 0 = bus 0, CE0  # SPI bus 0 is enabled by default
#                10 = bus 1, CE0  # enable SPI bus 2 prior to running this
#                21 = bus 2, CE1  # enable SPI bus 1 prior to running this

# set the Power Amplifier level to -12 dBm since this test example is
# usually run with nRF24L01 transceivers in close proximity
nrf_tx.pa_level = -12
nrf_rx.pa_level = -12

nrf_tx.channel = 125
nrf_rx.channel = 120

# addresses needs to be in a buffer protocol object (bytearray)
tx_address = b"2Node"
rx_address = b"1Node"

#for nrf in [nrf_rx, nrf_rx]:
#    nrf.data_rate = 1
#    nrf.auto_ack = True
#    #nrf.dynamic_payloads = True
#    nrf.payload_length = 32
#    nrf.crc = True
#    nrf.ack = 1
#    nrf.spi_frequency = 2000000



# set TX address of RX node into the TX pipe
nrf_tx.open_tx_pipe(tx_address)  # always uses pipe 0
# set RX address of TX node into an RX pipe
nrf_rx.open_rx_pipe(1,rx_address)  # using pipe 1

# using the python keyword global is bad practice. Instead we'll use a 1 item
# list to store our float number for the payloads sent
payload = [0.0]

# uncomment the following 3 lines for compatibility with TMRh20 library
# nrf.allow_ask_no_ack = False
# nrf.dynamic_payloads = False
# nrf.payload_length = 4


def send_data(count=10):  # count = 5 will only transmit 5 packets
    """Transmits an incrementing integer every second"""
    nrf_tx.listen = False  # ensures the nRF24L01 is in TX mode

    while count:
        #buffer = struct.pack("<f", payload[0])
        message = "BASE_20!"
        buffer = message.encode("utf-8")
        # "<f" means a single little endian (4 byte) float value.
        start_timer = time.monotonic_ns()  # start timer
        result = nrf_tx.send(buffer)
        end_timer = time.monotonic_ns()  # end timer
        if not result:
            print("send() failed or timed out")
        else:
            print(
                "Transmission successful! Time to Transmit:",
                "{} us. Sent: {}".format((end_timer - start_timer) / 1000, buffer),
            )
            payload[0] += 0.01
        #nrf_tx.flush_tx()
        time.sleep(1)
        count -= 1


def recieve_data(timeout=10):
    """Polls the radio and prints the received value. This method expires
    after 6 seconds of no received transmission"""
    nrf_rx.listen = True  # put radio into RX mode and power up

    start = time.monotonic()
    while True:
        nrf_rx.listen = True
        if nrf_rx.any():
            # grab information about the received payload
            #payload_size, pipe_number = (nrf_rx.any(), nrf_rx.pipe)
            # fetch 1 payload from RX FIFO

            buffer = nrf_rx.read()  # also clears nrf.irq_dr status flag

            message = buffer.decode("utf-8")

            print(
                "Received {}".format(message)
                # "Received {} bytes on pipe {}: {}".format(
                #     payload_size, pipe_number, message#payload[0]
                # )
            )
            time.sleep(0.01)
            start = time.monotonic()

    # recommended behavior is to keep in TX mode while idle
    #nrf_rx.listen = False  # put the nRF24L01 is in TX mode
    nrf_rx.flush_rx()

threading.Thread(target = recieve_data, daemon = True).start()
threading.Thread(target = send_data, daemon = True).start()

while True:
    time.sleep(1)
