import board
from adafruit_ht16k33.segments import BigSeg7x4
import usb_midi
import adafruit_midi
from analogio import AnalogIn
from adafruit_midi.control_change import ControlChange

btn = AnalogIn(board.A1)


def decode_character(character_code):
    if character_code >= 0x40:
        character_code = character_code - 0x40
        dot = "."
    else:
        dot = " "

    if character_code < 0x20:
        return chr(character_code + 0x40), dot

    return chr(character_code), dot


i2c = board.STEMMA_I2C()
display1 = BigSeg7x4(i2c, address=0x71)
display2 = BigSeg7x4(i2c, address=0x72)

display1.brightness = 0.25
display1.print("0000")
display1.colons[0] = True
display2.brightness = .25
display2.print("0000")
display2.colons[0] = True
display2.colons[1] = True


midi = adafruit_midi.MIDI(midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1], in_channel=0, out_channel=0)
while True:
    #if not btn.value:
    #    print("BTN is down")
    #else:
    #    print("BTN is up")
    msg = midi.receive()
    if msg is not None:
        if isinstance(msg, ControlChange):
            msg_bytes = msg.__bytes__()
            msg_hex = hex_string = ' '.join(f'{byte:02X}' for byte in msg_bytes)
            hex = msg_hex.split(" ")
            msg_type = "0x" + hex[1]

            if (int(msg_type, 16) & 0xF0) == 0x40:
                position = int(msg_type, 16) & 0x0F
                string_hex = "0x" + str(hex[2])
                converted = decode_character(int(string_hex, 16))
                position = 19 - (position * 2)

                if position == 3:
                    display1[0] = converted[0]
                elif position == 5:
                    display1[1] = converted[0]
                elif position == 7:
                    display1[2] = converted[0]
                elif position == 9:
                    display1[3] = converted[0]
                elif position == 11:
                    display2[0] = converted[0]
                elif position == 13:
                    display2[1] = converted[0]
                elif position == 17:
                    display2[2] = converted[0]
                elif position == 19:
                    display2[3] = converted[0]
