import math
import pyaudio
import itertools
import numpy as np
from pygame import midi
import os

BUFFER_SIZE = 256
SAMPLE_RATE = 48000
NOTE_AMP = 0.5

# -- HELPER FUNCTIONS --
def get_sin_oscillator(freq=55, amp=1, sample_rate=SAMPLE_RATE):
    increment = (2 * math.pi * freq) / sample_rate
    return (
        math.sin(v) * amp * NOTE_AMP for v in itertools.count(start=0, step=increment)
    )


def get_samples(notes_dict, num_samples=BUFFER_SIZE):
    return [
        sum([int(next(osc) * 32767) for _, osc in notes_dict.items()])
        for _ in range(num_samples)
    ]


# -- INITIALIZION --
midi.init()
for i in range(0, midi.get_count()):
    interf, name, input, output, opened = midi.get_device_info(i)
    print("Pygame MIDI device", i, interf, name, "Input:", not not input,
          "Output:", not not output, "Opened:", not not opened)

# midi_device_id = midi.get_default_input_id()
midi_device_id = int(os.environ.get("IQE_MIDI_IN") or 0)
midi_input = midi.Input(device_id=midi_device_id)
print("Opened midi input", midi_device_id, midi.get_device_info(midi_device_id))

p = pyaudio.PyAudio()
for j in range(0, p.get_host_api_count()):    
    info = p.get_host_api_info_by_index(j)
    numdevices = info.get('deviceCount')
    print(f"Host API {j}: {info}")

    for i in range(0, numdevices):
        dev_info = p.get_device_info_by_host_api_device_index(j, i)
        print("Input Device id ", i, " - ", dev_info)

out_id = int(os.environ.get("IQE_AUDIO_OUT") or 0)
print("Opening audio output", p.get_device_info_by_host_api_device_index(0, out_id))

stream = p.open(
    rate=SAMPLE_RATE,
    channels=2,
    format=pyaudio.paInt16,
    output=True,
    frames_per_buffer=BUFFER_SIZE,
    output_device_index=0,
    start=True,
)
stream.start_stream()

def note_on(notes_dict, note, vel):
    if note not in notes_dict:
        freq = midi.midi_to_frequency(note)
        notes_dict[note] = get_sin_oscillator(freq=freq, amp=vel / 127)

def note_off(notes_dict, note):
    if note in notes_dict:
        del notes_dict[note]
    
# -- RUN THE SYNTH --
try:
    print("Starting...")
    notes_dict = {}
    while True:
        # print("tick", stream.is_active(), stream.get_write_available(), stream.get_time())
        if notes_dict and stream.get_write_available():
            # Play the notes
            samples = get_samples(notes_dict)
            samples = np.int16(samples).tobytes()
            stream.write(samples)

        if midi_input.poll():
            # Add or remove notes from notes_dict
            for event in midi_input.read(num_events=16):
                (status, note, vel, _), _ = event
                print("midi in", status & 0xF0 == 0x80, status & 0xF0 == 0x90, event)
                if status & 0xF0 == 0x80:
                    note_off(notes_dict, note)
                if status & 0xF0 == 0x90:
                    note_on(notes_dict, note, vel)

except KeyboardInterrupt as err:
    midi_input.close()
    stream.close()
    print("Stopping...")