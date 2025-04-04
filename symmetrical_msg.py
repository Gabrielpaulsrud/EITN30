import board
from digitalio import DigitalInOut
import spidev
from circuitpython_nrf24l01.rf24 import RF24
import threading
import time


# Sender module setup
SPI_BUS = spidev.SpiDev()
CSN_SEND = 0  # SPI CE0
CE_SEND = DigitalInOut(board.D17)
nrf_send = RF24(SPI_BUS, CSN_SEND, CE_SEND)
nrf_send.pa_level = -12

# Receiver module setup
SPI_BUS2 = spidev.SpiDev()
CSN_RECV = 10  # SPI CE1
CE_RECV = DigitalInOut(board.D27)
nrf_recv = RF24(SPI_BUS2, CSN_RECV, CE_RECV)
nrf_recv.pa_level = -12

def receive_loop(nrf):
    while True:
        if nrf.any():
            data = nrf.read()
            try:
                msg = data.decode("utf-8")
                print(f"\nReceived: {msg}")
            except:
                print("\nReceived non-UTF8 data")
        time.sleep(0.01)  # prevent busy-waiting

def main(radio_number):
    addresses = [b"1Node", b"2Node"]
    # Radio number is either 0 or 1, used to initalize the different radios with different addresses
    # addresses needs to be in a buffer protocol object (bytearray)
    my_addres = addresses[radio_number]
    other_addres = addresses[1-radio_number]

    nrf_send.channel = 76 + radio_number   # depending on destination
    nrf_send.open_tx_pipe(other_addres)
    nrf_send.listen = False

    nrf_recv.channel = 77 - radio_number   # opposite of sender
    nrf_recv.open_rx_pipe(1, my_addres)
    nrf_recv.listen = True

    recv_thread = threading.Thread(target=receive_loop, args=(nrf_recv,), daemon=True)
    recv_thread.start()

    print("Chat ready. Type and press Enter to send.")
    while True:
        user_input = input("> ")
        if not user_input:
            continue
        nrf_send.send(user_input.encode("utf-8"))
        print("Message sent.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2 or sys.argv[1] not in ["0", "1"]:
        print("Usage: python symmetrical_msg.py [0|1]")
        sys.exit(1)

    radio_number = int(sys.argv[1])
    main(radio_number)