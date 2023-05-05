import pyaudio
import numpy as np

BUFFER_SIZE = 256
SAMPLE_RATE = 48000
NOTE_AMP = 0.1


p = pyaudio.PyAudio()
for j in range(0, p.get_host_api_count()):    
    info = p.get_host_api_info_by_index(j)
    numdevices = info.get('deviceCount')
    print(f"Host API {j}: {info}")

    for i in range(0, numdevices):
        dev_info = p.get_device_info_by_host_api_device_index(j, i)
        print("Audio Device id ", i, " - ", dev_info)

out_stream = p.open(
    rate=SAMPLE_RATE,
    channels=2,
    format=pyaudio.paFloat32,
    input=False,
    output=True,
    frames_per_buffer=BUFFER_SIZE,
    # output_device_index=0,
    output_device_index=2,
    start=True,
)

in_stream = p.open(
    rate=SAMPLE_RATE,
    channels=2,
    format=pyaudio.paFloat32,
    input=True,
    output=False,
    frames_per_buffer=BUFFER_SIZE,
    input_device_index=0,
    start=True,
)

# -- RUN --
try:
    print("Starting...")
    in_stream.start_stream()
    out_stream.start_stream()
    ts = in_stream.get_time()
    while True:
        if in_stream.get_read_available() < BUFFER_SIZE:
            continue
        # print("tick", stream.is_active(), stream.get_write_available(), stream.get_time())
        try:
            data1 = in_stream.read(BUFFER_SIZE, exception_on_overflow=False)
        except Exception:
            # print("read ex")
            pass
        
        now = in_stream.get_time()
        
        # print((now - ts) * 1_000)
        ts = now
            
        try:
            out_stream.write(data1, exception_on_underflow=False)
        except Exception:
            # print("write ex")
            pass


except KeyboardInterrupt as err:
    out_stream.close()
    in_stream.close()
    print("Stopping...")