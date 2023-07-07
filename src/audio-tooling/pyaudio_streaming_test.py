import numpy as np
import pyaudio
import time
import math
from typing import NamedTuple
import threading
import rtmidi2
import os

class Block(NamedTuple): index: int; stream_time: float; samples: bytes; time: dict

BLOCK_SIZE = int(os.environ.get("IQE_BLOCK_SIZE") or 1024)
SAMPLE_RATE = int(os.environ.get("IQE_SAMPLE_RATE") or 48000)
CHANNELS = int(os.environ.get("IQE_CHANNELS") or 2)
SILENCE = (np.zeros(BLOCK_SIZE * CHANNELS, dtype=np.float32).tobytes(), pyaudio.paContinue)
RUNNING = True

BLOCKS_BUFFER_SZ = 1024 * 1024
blocks = [None] * BLOCKS_BUFFER_SZ
block_index = 0
num_blocks_written = 0

beat_time = None
spb = None # seconds per beat

def now():
    global in_stream
    return in_stream.get_time()

def callback_in(data, frame_count, block_time, status):
    global blocks, block_index
    if status:
        print("**** XRUN", status)
    blocks[block_index % BLOCKS_BUFFER_SZ] = Block(index=block_index, time=block_time, samples=data, stream_time=now())
    block_index = block_index + 1
    return (None, pyaudio.paContinue)
    
def callback_out(_, frame_count, block_time, status):
    global block_index, num_blocks_written
    block = blocks[num_blocks_written % BLOCKS_BUFFER_SZ]
    if block is None:
        return SILENCE
    if status:
        print("**** XRUN", status)
    
    # print(num_blocks_written, block_index, block_time["output_buffer_dac_time"] - block.time["input_buffer_adc_time"])
    num_blocks_written = num_blocks_written + 1
    return (block.samples, pyaudio.paContinue)

""" Build numpy window of mono mixed samples form interleaved block bytes, back maximum seconds """
def build_samples_window(secs_ago):
    global block_index
    next_block = block_index - 1
    earliest_block = max(0, next_block - math.ceil(secs_ago * SAMPLE_RATE / BLOCK_SIZE))
    window = np.empty((next_block - earliest_block) * BLOCK_SIZE)
    print("wtf", len(window), earliest_block, next_block, block_index)
    for bi in range(earliest_block, next_block):
        block = blocks[bi % BLOCKS_BUFFER_SZ]
        block_start = (bi - earliest_block) * BLOCK_SIZE
        interleaved = np.frombuffer(block.samples, dtype=np.float32)
        for i in range(0, BLOCK_SIZE * CHANNELS, CHANNELS):
            window[block_start + int(i / 2)] = (interleaved[i] + interleaved[i + 1]) * 0.5
    return window, earliest_block * BLOCK_SIZE

""" Simple method to look at stretches of silence to infer bpm and phase (tempo) """
def simple_detect_tempo(window):
    # Build silence ranges, make array that is 1 where sample is 0 (silent), pad ends
    iszero = np.concatenate(([0], np.equal(window, 0), [0]))
    absdiff = np.abs(np.diff(iszero))
    # Runs start and end where absdiff is 1.
    zero_runs = np.where(absdiff == 1)[0].reshape(-1, 2)
    zero_runs = list(map(list, zero_runs))
    
    # Make sure we have at least 4, and use inner (since outers can be incomplete)
    if len(zero_runs) >= 4:
        silence_end = zero_runs[2][1]
        silence_start = zero_runs[2][0]
        prev_silence_end = zero_runs[1][1]
        spb = (silence_end - prev_silence_end) / SAMPLE_RATE
        beep_len = (silence_start - prev_silence_end + 1) / SAMPLE_RATE
        print("Detected BPM {} and beep length {}s, secs per beat {}, a beat sample # {}".format(60 / spb, beep_len, spb, silence_end))
        return (60 / spb, silence_end)
    return (None, None)

""" Try detecting tempo (look back max 6 seconds), and schedule metronome click """
def tempo_detect_thread():
    time.sleep(5)
    print("Starting tempo detection thread")
    def tick():
        global beat_time, spb
        while RUNNING:
            time.sleep(2)
            window, sample_start = build_samples_window(1.5)
            bpm, beat_sample_index_in_window = simple_detect_tempo(window)
            if bpm:
                # Using stream time and sample buffer index, get stream time of the beat, advance to next
                spb = 60 / bpm
                beat_sample = sample_start + beat_sample_index_in_window
                beat_block = blocks[math.floor(beat_sample / BLOCK_SIZE) % BLOCKS_BUFFER_SZ]
                beat_time = beat_block.time["input_buffer_adc_time"] + (beat_sample - beat_block.index * BLOCK_SIZE) / SAMPLE_RATE
                print("Beat occured at sample {} of block # {}, ranged [{}, {}), stream time {}".format(
                    beat_sample, beat_block.index, beat_block.index * BLOCK_SIZE, (beat_block.index + 1) * BLOCK_SIZE, beat_time
                ))

                # Cook / fudge time seconds by output latency only (shrug) and current DAW settings (double shrug)
                # beat_time = beat_time - audio_stream.latency[1]
                # beat_time = beat_time - float(os.environ.get("IQE_LATENCY_SHIFT") or (2 * 64 / 48000))
                
                # Set two beats in the future for metronome to have time to click
                beat_time = beat_time + (math.ceil((now() - beat_time) / spb) + 1) * spb
                break
    return threading.Thread(target=tick)

""" Busy-ish waiting to play clicks on time """
def metronome_click_thread(midi_out):
    def tick():
        global beat_time, spb
        print("Starting click thread")
        while RUNNING:
            if beat_time is None or spb is None:
                time.sleep(0.300)
            else:
                ts = now()
                until_beat = beat_time - ts
                if until_beat <= 0:
                    print("click")
                    midi_out.send_noteon(11, 37, 127)
                    def note_off():
                        time.sleep(0.30)
                        midi_out.send_noteoff(11, 37)
                    threading.Thread(target=note_off).start()
                    beat_time = ts + spb + until_beat
                elif until_beat <= 0.005:
                    time.sleep(0)
                else:
                    time.sleep(until_beat * 0.50)
    return threading.Thread(target=tick)

p = pyaudio.PyAudio()
out_stream = p.open(
    rate=SAMPLE_RATE,
    channels=CHANNELS,
    format=pyaudio.paFloat32,
    output=True,
    frames_per_buffer=BLOCK_SIZE,
    output_device_index=int(os.environ.get('IQE_AUDIO_OUT') or 2),
    stream_callback=callback_out,
    start=False
)

in_stream = p.open(
    rate=SAMPLE_RATE,
    channels=CHANNELS,
    format=pyaudio.paFloat32,
    input=True,
    frames_per_buffer=BLOCK_SIZE,
    input_device_index=int(os.environ.get('IQE_AUDIO_IN') or 0),
    stream_callback=callback_in,
    start=False
)

print("Reported latencies, in", in_stream.get_input_latency(), "out", out_stream.get_output_latency())

try:
    in_stream.start_stream()
    out_stream.start_stream()
    midi_out = rtmidi2.MidiOut()
    midi_port = int(os.environ.get('IQE_MIDI_OUT') or 0)
    midi_out.open_port(midi_port)
    print("Opened midi output", midi_out.get_port_name(midi_port))
    metronome_click_thread(midi_out).start()
    tempo_detect_thread().start()
    while in_stream.is_active():
        time.sleep(1)
except KeyboardInterrupt as err:
    print("Stopping...")
    RUNNING = False
    out_stream.close()
    in_stream.close()
    p.terminate()