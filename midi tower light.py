# Uses a feather board with USB Host plus the tri-color usb controlled tower light
import board
import usb_host
import usb.core
from adafruit_midi import MIDI
from adafruit_midi.note_on import NoteOn
import usb_midi
import sys

# --- CH341 constants from ch341.c ---
CH341_REQ_SERIAL_INIT  = 0xA1
CH341_REQ_WRITE_REG    = 0x9A
CH341_REQ_MODEM_CTRL   = 0xA4

CH341_REG_PRESCALER    = 0x12
CH341_REG_DIVISOR      = 0x13
CH341_REG_LCR          = 0x18
CH341_REG_LCR2         = 0x25

CH341_LCR_ENABLE_RX    = 0x80
CH341_LCR_ENABLE_TX    = 0x40
CH341_LCR_CS8          = 0x03

CH341_BIT_DTR          = 1 << 5
CH341_BIT_RTS          = 1 << 6

# 0) bring up the USB-host port
host = usb_host.Port(board.USB_HOST_DATA_PLUS,
                     board.USB_HOST_DATA_MINUS)

# 1) find & detach
usb_list = list(usb.core.find(find_all=True))
sys.stdout.write(f"Found {len(usb_list)} USB devices")
for device in usb_list:
	sys.stdout.write(f"Vendor id: {hex(device.idVendor)}, Product id: {hex(device.idProduct)}")
dev = usb.core.find(idVendor=0x1A86, idProduct=0x7523)
if not dev:
    raise RuntimeError("Tower light not found!")
if dev.is_kernel_driver_active(0):
    dev.detach_kernel_driver(0)
dev.set_configuration()

# 2) serial-init
dev.ctrl_transfer(0x40, CH341_REQ_SERIAL_INIT, 0, 0, None)

# 3) set baud to 9600
def get_divisor_val(baud=9600):
    CH341_CLKRATE = 48_000_000
    def clk_div(ps, fact): return 1 << (12 - 3*ps - fact)
    min_rates = [CH341_CLKRATE//(clk_div(ps,1)*512) for ps in range(4)]
    speed = max(min(baud, CH341_CLKRATE//(clk_div(3,0)*2)),
                (CH341_CLKRATE//(clk_div(0,0)*256) + 255)//256)
    fact = 1
    for ps in range(3, -1, -1):
        if speed > min_rates[ps]:
            break
    div = CH341_CLKRATE//(clk_div(ps,fact)*speed)
    if div < 9 or div > 255:
        div //= 2
        fact = 0
    # rounding correction
    if (16*CH341_CLKRATE//(clk_div(ps,fact)*div)
        - 16*speed >=
        16*speed - 16*CH341_CLKRATE//(clk_div(ps,fact)*(div+1))):
        div += 1
    if fact == 1 and (div % 2) == 0:
        div //= 2
        fact = 0
    return ((0x100 - div) << 8) | (fact << 2) | ps

DIV = get_divisor_val(9600)
dev.ctrl_transfer(
    0x40, CH341_REQ_WRITE_REG,
    (CH341_REG_DIVISOR << 8) | CH341_REG_PRESCALER,
    DIV, None
)

# 4) set data format to 8N1 + enable RX/TX
LCR = CH341_LCR_ENABLE_RX | CH341_LCR_ENABLE_TX | CH341_LCR_CS8
dev.ctrl_transfer(
    0x40, CH341_REQ_WRITE_REG,
    (CH341_REG_LCR2 << 8) | CH341_REG_LCR,
    LCR, None
)

# 5) assert DTR+RTS so the UART clock runs
MODEM = ~(CH341_BIT_DTR | CH341_BIT_RTS) & 0xFF
dev.ctrl_transfer(0x40, CH341_REQ_MODEM_CTRL, MODEM, 0, None)

# Helper to send a single-byte command
def send_cmd(cmd):
    dev.write(0x02, bytes([cmd]))

# Feature on/off functions
def red_on():
    send_cmd(0x11)

def red_off():
    send_cmd(0x21)

def yellow_on():
    send_cmd(0x12)

def yellow_off():
    send_cmd(0x22)

def green_on():
    send_cmd(0x14)

def green_off():
    send_cmd(0x24)

def buzzer_on():
    send_cmd(0x18)

def buzzer_off():
    send_cmd(0x28)


# MIDI transport & arm/disarm constants
_PLAY   = 0x5E
_STOP   = 0x5D
_RECORD = 0x5F

rec = False
# Set up MIDI input and output ports
# Use port 0 for input, port 1 for output
midi = MIDI(midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1])

while True:
    msg = midi.receive()
    if msg is None:
        # periodically re-poll if no messages for a time
        continue

    # Handle NoteOn on channel 1 for transport commands
    if isinstance(msg, NoteOn) and msg.channel == 0 and msg.velocity > 0:
        if msg.note == _STOP:
        	rec = False
        	red_off(); yellow_off(); green_on()
        	print("Stop Command Received")
        elif msg.note == _PLAY and rec == False:
            red_off(); green_off(); yellow_on()
            print("Play Command Received")
        elif msg.note == _RECORD:
        	rec = True
        	green_off(); yellow_off(); red_on()
        	print("Record Command Received")