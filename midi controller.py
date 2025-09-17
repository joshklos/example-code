# This was a semi-succesful attempt at making a DAW remote control. I ran into delay issues
# with receiving updates, but I think that may have been more of a bluetooth midi problem
# than a problem with the code.

import board
from adafruit_neokey.neokey1x4 import NeoKey1x4
import adafruit_ble
import adafruit_ble_midi
import adafruit_midi
from adafruit_ble import BLERadio
from adafruit_ble.advertising import Advertisement
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_midi.note_on import NoteOn
from adafruit_midi.midi_message import MIDIUnknownEvent


def check_msgs(midi, transport_status):
    msg = midi.receive()
    if msg is not None:
        if isinstance(msg, MIDIUnknownEvent) is False:
            if msg.note == 94:
                print(msg)
                if msg.velocity == 127:
                    transport_status['playing'] = True
                else:
                    transport_status['playing'] = False
            if msg.note == 95:
                print(msg)
                if msg.velocity == 127:
                    transport_status['recording'] = True
                else:
                    transport_status['recording'] = False
    return transport_status

print("Hello!!")
midi_service = adafruit_ble_midi.MIDIService()
advertisement = ProvideServicesAdvertisement(midi_service)

print("Started!")
ble = BLERadio()
ble.name = 'Reaper Controller'
if ble.connected:
    for c in ble.connections:
        c.disconnect()

midi = adafruit_midi.MIDI(midi_in=midi_service, in_channel=0, midi_out=midi_service, out_channel=0)

print("advertising")
ble.start_advertising(advertisement)

# use default I2C bus
i2c_bus = board.I2C()

# Create a NeoKey object
neokey = NeoKey1x4(i2c_bus, addr=0x30)

print("Adafruit NeoKey simple test")
neokey_status = {
    'a': False,
    'b': False,
    'c': False,
    'd': False
}

neo_colors = {
    'red': 0xFF0000,
    'yellow': 0xFFFF00,
    'green': 0x00FF00,
    'blue': 0x00FFFF,
    'off': 0x0
}

transport_status = {
    'playing': False,
    'recording': False
}

def transport_lights(neokeys, transport):
    if transport['recording']:
        neokeys.pixels[1] = 0xFF0000
    else:
        neokeys.pixels[1] = 0x0
    if transport['playing']:
        neokeys.pixels[2] = 0x00FF00
    else:
        neokeys.pixels[2] = 0x0

# Check each button, if pressed, light up the matching neopixel!
while True:
    transport_status = check_msgs(midi, transport_status)
    transport_lights(neokey, transport_status)
    if neokey[0]:
        if neokey_status['a'] == False:
            print("Button A")
        neokey.pixels[0] = 0xFF0000 # Red
        neokey_status['a'] = True
    else:
        neokey.pixels[0] = 0x0
        neokey_status['a'] = False
    transport_status = check_msgs(midi, transport_status)
    transport_lights(neokey, transport_status)
    if neokey[1]:
        if neokey_status['b'] == False:
            print("Record")
            midi.send(NoteOn(95, 127))
        neokey.pixels[1] = neo_colors['red']
        neokey_status['b'] = True
    else:
        if transport_status['recording'] is False:
            neokey.pixels[1] = 0x0
        else:
            neokey.pixels[1] = neo_colors['red']
        neokey_status['b'] = False
    transport_status = check_msgs(midi, transport_status)
    transport_lights(neokey, transport_status)
    if neokey[2]:
        if transport_status['playing'] is False:
            midi.send(NoteOn(94, 127))
            transport_status['playing'] = True
        else:
            midi.send(NoteOn(93, 127))
            transport_status['playing'] = False
        neokey.pixels[2] = 0x00FF00 # Green
        neokey_status['c'] = True
    else:
        if transport_status['playing'] is False:
            neokey.pixels[2] = 0x0
        else:
            neokey.pixels[2] = neo_colors['green']
        neokey_status['c'] = False
    transport_status = check_msgs(midi, transport_status)
    transport_lights(neokey, transport_status)
    if neokey[3]:
        if neokey_status['d'] == False:
            print("Marker")
            midi.send(NoteOn(84, 127))
        neokey.pixels[3] = 0x00FFFF # Blue
        neokey_status['d'] = True
    else:
        if neokey_status['d'] == True:
            midi.send(NoteOn(84, 0))
        neokey.pixels[3] = 0x0
        neokey_status['d'] = False
