import numpy as np
import pyaudio
import time

"""
 Notes 20230819:
    Yeesh. Unearthing these audio scripts. I vaguely recall "SoundDevice" lib being buggy, and maybe
    (MAYBE) pyaudio was more promising. So first test is simple, can I do a simple loopback of an input
    (like Blackhole) and write to output (like Airpods), and in Reaper with BH out selected, can I hear
    in Airpods. Seems to work! (Note Airpods have noticable latency, wired external headphones maybe not)
"""
# OUT_ID = 5 # e.g. set this to Airpods out
OUT_ID = 3 # e.g. set this to Airpods out
IN_ID = 1 # e.g. set this to BlackHole input, test piping

# BLOCK_SIZE = 256
BLOCK_SIZE = 64
SAMPLE_RATE = 48000
CHANNELS = 2

BLOCKS_BUFFER_SZ = 1024 * 1024
blocks = [None] * BLOCKS_BUFFER_SZ
block = 0
block_out = 0

def callback_in(data, frame_count, block_time, status):
    global block
    # print(block_time) # input_adc dac etc
    if status:
        print("**** non zero status XRUN?", status)
    blocks[block % BLOCKS_BUFFER_SZ] = bytes(data)
    block = block + 1
    return (None, pyaudio.paContinue)
    
def callback_out(_, frame_count, block_time, status):
    global block_out
    print(block_time) # input_adc dac etc
    if status:
        print("**** non zero status XRUN?", status)
    data = blocks[block_out % BLOCKS_BUFFER_SZ]
    block_out = block_out + 1
    return (bytes(data), pyaudio.paContinue)
    

p = pyaudio.PyAudio()
for j in range(0, p.get_host_api_count()):    
    info = p.get_host_api_info_by_index(j)
    numdevices = info.get('deviceCount')
    print(f"Host API {j}: {info}")

    for i in range(0, numdevices):
        dev_info = p.get_device_info_by_host_api_device_index(j, i)
        print("Audio Device id ", i, " - ", dev_info)

in_stream = p.open(
    rate=SAMPLE_RATE,
    channels=CHANNELS,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=BLOCK_SIZE,
    input_device_index=IN_ID,
    stream_callback=callback_in,
    start=False
)

out_stream = p.open(
    rate=SAMPLE_RATE,
    channels=CHANNELS,
    format=pyaudio.paInt16,
    output=True,
    frames_per_buffer=BLOCK_SIZE,
    output_device_index=OUT_ID,
    stream_callback=callback_out,
    start=False
)

print("Reported latencies, in", in_stream.get_input_latency(), "out", out_stream.get_output_latency())

try:
    in_stream.start_stream()
#     time.sleep(.1)
    out_stream.start_stream()
    while in_stream.is_active():
        time.sleep(1)
except KeyboardInterrupt as err:
    print("Stopping...")
    out_stream.close()
    in_stream.close()
    p.terminate()