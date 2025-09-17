# This uses the AdaFruit matrixportal (matrixportal s3) as a midi clock and recording indicator.

import time
import board
import terminalio
import usb_midi
from adafruit_matrixportal.matrixportal import MatrixPortal
import adafruit_midi
from adafruit_midi.midi_message import MIDIUnknownEvent
from adafruit_midi.control_change import ControlChange
from adafruit_midi.midi_message import MIDIMessage
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff


time_array = ["0", "0", ":", "0", "0", ":", "0", "0"]
def decode_character(character_code):
    if character_code >= 0x40:
        character_code = character_code - 0x40
        dot = "."
    else:
        dot = " "

    if character_code < 0x20:
        return chr(character_code + 0x40), dot

    return chr(character_code), dot
      

midi = adafruit_midi.MIDI(midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1], in_channel=0, out_channel=0)

matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=True)


RED = '#cf2727'
GOLDENROD = "#daa520"
GREEN = "#0F4D0F"

transport_status = {
	'playing': False,
	'recording': False,
	'status': 'Stand By'
}

# timecode = matrixportal.add_text(text_position=(8,20), text=''.join(time_array), text_color=RED)
pause_text = matrixportal.add_text(text_position=(8,7), text="Stand By", text_color=GOLDENROD)
recording_text = matrixportal.add_text(text_position=(5,7), text="", text_color=RED)
playing_text = matrixportal.add_text(text_position=(11,7), text="", text_color=GREEN)



hour_1 = matrixportal.add_text(text_position=(8,20), text="0", text_color=RED)
hour_2 = matrixportal.add_text(text_position=(14,20), text="0", text_color=RED)
colon_1 = matrixportal.add_text(text_position=(20,20), text=":", text_color=RED)
minute_1 = matrixportal.add_text(text_position=(26,20), text="0", text_color=RED)
minute_2 = matrixportal.add_text(text_position=(32,20), text="0", text_color=RED)
colon_2 = matrixportal.add_text(text_position=(38,20), text=":", text_color=RED)
second_1 = matrixportal.add_text(text_position=(44,20), text="0", text_color=RED)
second_2 = matrixportal.add_text(text_position=(50,20), text="0", text_color=RED)

# current_timecode = ''.join(time_array)

timecode_change = False
while True:
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
					if time_array[0] != converted[0]:
						time_array[0] = converted[0]
						matrixportal.set_text(converted[0], hour_1)
				elif position == 5:
					#time_array[1] = converted[0]
					if time_array[1] != converted[0]:
						time_array[1] = converted[0]
						matrixportal.set_text(converted[0], hour_2)
				elif position == 7:
					if time_array[3] != converted[0]:
						time_array[3] = converted[0]
					#time_array[3] = converted[0]
						matrixportal.set_text(converted[0], minute_1)
				elif position == 9:
					if time_array[4] != converted[0]:
						time_array[4] = converted[0]
					#time_array[4] = converted[0]
						matrixportal.set_text(converted[0], minute_2)
				elif position == 11:
					if time_array[6] != converted[0]:
						time_array[6] = converted[0]
					#time_array[6] = converted[0]
						matrixportal.set_text(converted[0], second_1)
				elif position == 13:
					if time_array[7] != converted[0]:
						time_array[7] = converted[0]
					#time_array[7] = converted[0]
						matrixportal.set_text(converted[0], second_2)


 		if isinstance(msg, NoteOn) or isinstance(msg, NoteOff):
 			if msg.note == 94:
 				if msg.velocity == 127:
 					transport_status['playing'] = True
 				else:
 					transport_status['playing'] = False
 			if msg.note == 95:
 				if msg.velocity == 127:
 					transport_status['recording'] = True
 				else:
 					transport_status['recording'] = False
 					
 		if transport_status['playing'] and transport_status['recording']:
 			status = "Recording"
 			if transport_status['status'] != status:
 				transport_status['status'] = status
 				matrixportal.set_text('', pause_text)
 				matrixportal.set_text('', playing_text)
 				matrixportal.set_text(status, recording_text)
 		if transport_status['playing'] and transport_status['recording'] is False:
 			status = "Playing"
 			if transport_status['status'] != status:
 				transport_status['status'] = status
 				matrixportal.set_text('', pause_text)
 				matrixportal.set_text('', recording_text)
 				matrixportal.set_text(status, playing_text)
 		if transport_status['playing'] is False and transport_status['recording'] is False:
 			status = "Stand By"
 			if transport_status['status'] != status:
 				transport_status['status'] = status
 				matrixportal.set_text('', playing_text)
 				matrixportal.set_text('', recording_text)
 				matrixportal.set_text(status, pause_text)

 			   
