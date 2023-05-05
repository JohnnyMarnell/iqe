import numpy as np
import pyaudio
import time

BLOCK_SIZE = 256
SAMPLE_RATE = 48000
CHANNELS = 2

BLOCKS_BUFFER_SZ = 1024 * 1024
blocks = [None] * BLOCKS_BUFFER_SZ
block = 0
block_out = 0

def callback_in(data, frame_count, block_time, status):
    global block
    blocks[block % BLOCKS_BUFFER_SZ] = bytes(data)
    block = block + 1
    return (None, pyaudio.paContinue)
    
def callback_out(_, frame_count, block_time, status):
    global block_out
    data = blocks[block_out % BLOCKS_BUFFER_SZ]
    block_out = block_out + 1
    return (bytes(data), pyaudio.paContinue)
    

p = pyaudio.PyAudio()
for j in range(0, p.get_host_api_count()):    
    info = p.get_host_api_info_by_index(j)
    numdevices = info.get('deviceCount')
    # print(f"Host API {j}: {info}")

    for i in range(0, numdevices):
        dev_info = p.get_device_info_by_host_api_device_index(j, i)
        # print("Audio Device id ", i, " - ", dev_info)

out_stream = p.open(
    rate=SAMPLE_RATE,
    channels=CHANNELS,
    format=pyaudio.paInt16,
    output=True,
    frames_per_buffer=BLOCK_SIZE,
    output_device_index=2,
    stream_callback=callback_out,
    start=False
)

in_stream = p.open(
    rate=SAMPLE_RATE,
    channels=CHANNELS,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=BLOCK_SIZE,
    input_device_index=0,
    stream_callback=callback_in,
    start=False
)

print("Reported latencies, in", in_stream.get_input_latency(), "out", out_stream.get_output_latency())

try:
    in_stream.start_stream()
    time.sleep(.1)
    out_stream.start_stream()
    while in_stream.is_active():
        time.sleep(1)
except KeyboardInterrupt as err:
    print("Stopping...")
    out_stream.close()
    in_stream.close()
    p.terminate()