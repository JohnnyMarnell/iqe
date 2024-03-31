import pyaudio
import time
import math
from dataclasses import dataclass

@dataclass
class Block: index: int; size: int; samples: bytearray; wall_time: float; stream_time: float; \
                         input_buffer_adc_time: float; current_time: float; output_buffer_dac_time: float;

p = pyaudio.PyAudio()

class Audio:
    def __init__(self, block_size=64, sample_rate=48000, seconds=5 * 60):
        self.pyaudio = p
        self.block_size = block_size
        self.sample_rate = sample_rate
        self.block_time = self.block_size / self.sample_rate
        self.num_blocks = math.ceil(seconds * sample_rate / block_size)
        self.devices = self.query_devices()
        self.blocks = list()
        for i in range(self.num_blocks):
            self.blocks.append(Block(index=0, size=0, samples=bytearray(2 * self.block_size), wall_time=0, stream_time=0,
                              input_buffer_adc_time=0, current_time=0, output_buffer_dac_time=0))
        self.num_blocks_read = 0
        self.num_blocks_written = 0
        self.output_stream = None
        self.input_stream = None
        self.input_channels = None
        self.input_time = None
        self.shutdown_called = False
        
    def query_devices(self):
        devices = list()
        for j in range(0, p.get_host_api_count()):    
            api_info = p.get_host_api_info_by_index(j)
            num_devices = api_info.get('deviceCount')
            # print(f"Host API {j}: {api_info}")

            for i in range(0, num_devices):
                dev_info = p.get_device_info_by_host_api_device_index(j, i)
                # print("Audio Device id ", i, " - ", dev_info)
                devices.append({"api": api_info, "device": dev_info})        
        return devices

    def find_output(self, name, require=True):
        devices = [d for d in self.devices if d["device"]["maxOutputChannels"] > 0
                and name in d["device"]["name"]]
        if require and not devices:
            raise ValueError(f"Output device {name} not found")
        return devices[0]

    def find_input(self, name, require=True):
        devices = [d for d in self.devices if d["device"]["maxInputChannels"] > 0
                and name in d["device"]["name"]]
        if require and not devices:
            raise ValueError(f"Input device {name} not found")
        return devices[0]
        
    def time(self):
        return self.input_time
    
    def listen(self, device_name, callback, channels=None):
        device = self.find_input(device_name, require=True)
        self.input_channels = channels or device["device"]["maxInputChannels"]
        print(f"Listening to input {device_name}, {self.input_channels} channels")
        
        def wrapped_callback(data, frame_count, block_time, status):
            try:
                if status:
                    print("**** non zero status XRUN?", status)
                block = self.blocks[self.num_blocks_read % self.num_blocks]
                if block.samples is None or len(block.samples) != len(data):
                    block.samples = bytearray(data)
                else:
                    block.samples[:] = data
                block.index = self.num_blocks_read
                block.size = frame_count
                block.wall_time = time.time()
                block.input_buffer_adc_time = block_time["input_buffer_adc_time"]
                block.output_buffer_dac_time = block_time["output_buffer_dac_time"]
                block.current_time = block_time["current_time"]
                block.stream_time = self.input_stream.get_time()
                
                self.input_time = block.input_buffer_adc_time + self.block_time
                
                callback(block)
                
                self.num_blocks_read = self.num_blocks_read + 1
                return (None, pyaudio.paContinue)
            except Exception as err:
                print("Error in input callback", err)
                return (None, pyaudio.paAbort)
        
        self.input_stream = p.open(
            rate=self.sample_rate,
            channels=self.input_channels,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.block_size,
            input_device_index=device["device"]["index"],
            stream_callback=wrapped_callback,
            start=False
        )
        self.input_stream.start_stream()
        return self.input_stream
    
    def output(self, device_name, callback, channels=None):
        device = self.find_output(device_name)
        channels = channels or device["device"]["maxOutputChannels"]
        print(f"Using output {device['device']['name']}, {channels} channels")
        
        def wrapped_callback(_, frame_count, block_time, status):
            try:
                if status:
                    print("**** non zero status XRUN?", status)
                samples = callback(_, frame_count, block_time, status)
                self.num_blocks_written = self.num_blocks_written + 1
                if isinstance(samples, bytearray):
                    samples = bytes(samples)
                return (samples, pyaudio.paContinue)
            except Exception as err:
                print("Error in output callback", err)
                return (None, pyaudio.paAbort)        
        
        self.output_stream = p.open(
            rate=self.sample_rate,
            channels=channels,
            format=pyaudio.paInt16,
            output=True,
            frames_per_buffer=self.block_size,
            output_device_index=device["device"]["index"],
            stream_callback=wrapped_callback,
            start=False
        )
        self.output_stream.start_stream()
        return self.output_stream
    
    def latest_block_written(self):
        return self.blocks[self.num_blocks_written % self.num_blocks]
        
    def shutdown(self):
        if self.shutdown_called:
            return
        self.shutdown_called = True
        print("Shutting down audio...")
        if self.output_stream:
            self.output_stream.close()
        if self.input_stream:
            self.input_stream.close()
        p.terminate()


# A Simple test
if __name__ == '__main__':
    try:
        print("Will look for and listen to BlackHole loopback'd audio and pipe to Speakers output")
        audio = Audio()
        
        def in_callback(block):
            pass
        audio.listen('BlackHole 2ch', in_callback)

        def out_callback(_, frame_count, block_time, status):
            return audio.latest_block_written().samples
        out = audio.output('Speakers', out_callback)
        
        while audio.input_stream.is_active():
            time.sleep(1)

    except KeyboardInterrupt as err:
        audio.shutdown()
    finally:
        audio.shutdown()