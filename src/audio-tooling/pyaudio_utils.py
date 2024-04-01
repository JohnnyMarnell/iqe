import logging
import time
import math
from dataclasses import dataclass
import pyaudio

logger = logging.getLogger(__name__)


@dataclass
class BlockTime:
    """
    Various timestamps that can occur during a block of audio processing
    """

    wall_time: float
    stream_time: float
    current_time: float
    input_buffer_adc_time: float
    output_buffer_dac_time: float


@dataclass
class Block:
    """
    A block, or buffer of audio data, collection of samples
    """

    index: int
    size: int
    samples: bytearray
    time: BlockTime


p = pyaudio.PyAudio()


class Audio:
    """
    Main helper class to manage audio input and output
    """

    input_stream: pyaudio.PyAudio.Stream
    output_stream: pyaudio.PyAudio.Stream

    def __init__(self, block_size=64, sample_rate=48000, seconds=5 * 60):
        self.pyaudio = p
        self.block_size = block_size
        self.sample_rate = sample_rate
        self.block_time = self.block_size / self.sample_rate
        self.num_blocks = math.ceil(seconds * sample_rate / block_size)
        self.devices = self.query_devices()
        self.blocks: list[Block] = []

        self.num_blocks_read = 0
        self.num_blocks_written = 0
        self.input_channels = 0
        self.input_time = 0
        self.shutdown_called = False

    def query_devices(self):
        """Query all audio devices"""
        devices = []
        for j in range(0, p.get_host_api_count()):
            api_info = p.get_host_api_info_by_index(j)
            num_devices = int(api_info.get("deviceCount") or 0)
            for i in range(0, num_devices):
                dev_info = p.get_device_info_by_host_api_device_index(j, i).copy()
                dev_info.update({"api": api_info})
                devices.append(dev_info)
        return devices

    def find_output(self, name):
        """Find output by name"""
        for device in self.devices:
            if device["maxOutputChannels"] > 0 and name in device["name"]:
                return device
        raise ValueError(f"Output device {name} not found")

    def find_input(self, name):
        """Find input by name"""
        for device in self.devices:
            if device["maxInputChannels"] > 0 and name in device["name"]:
                return device
        raise ValueError(f"Input device {name} not found")

    def time(self):
        """Get the current time, relating to the input stream"""
        return self.input_time

    def listen(self, device_name, callback, channels=None):
        """Listen to input device and call callback with block of audio data"""

        device = self.find_input(device_name)
        self.input_channels = channels or device["maxInputChannels"]
        print(
            f"Listening to input {device_name}, {self.input_channels} channels, "
            + f"requested sample rate {self.sample_rate} and block size {self.block_size}"
        )

        # Pre-allocate blocks
        for _ in range(self.num_blocks):
            self.blocks.append(
                Block(
                    index=0,
                    size=0,
                    samples=bytearray(self.input_channels * self.block_size),
                    time=BlockTime(
                        wall_time=0,
                        stream_time=0,
                        current_time=0,
                        input_buffer_adc_time=0,
                        output_buffer_dac_time=0,
                    ),
                )
            )

        def wrapped_callback(data, frame_count, block_time, status):
            try:
                if status:
                    print("**** non zero status BUFFER OVER/UNDER RUN ?", status)

                block = self.blocks[self.num_blocks_read % self.num_blocks]
                block.index = self.num_blocks_read
                block.size = frame_count

                # Copy samples
                if block.samples is None or len(block.samples) != len(data):
                    logger.warning(
                        "Varying block sizes: bs %s, d %s, fc %s, c %s",
                        len(block.samples),
                        len(data),
                        frame_count,
                        self.block_size,
                    )
                    block.samples = bytearray(data)
                else:
                    block.samples[:] = data

                # Update timestamps
                bt = block.time
                bt.wall_time = time.time()
                bt.stream_time = self.input_stream.get_time()
                bt.input_buffer_adc_time = block_time["input_buffer_adc_time"]
                bt.output_buffer_dac_time = block_time["output_buffer_dac_time"]
                bt.stream_time = block_time["current_time"]

                self.input_time = bt.input_buffer_adc_time + self.block_time

                callback(block)

                self.num_blocks_read += 1
                return (None, pyaudio.paContinue)

            except Exception:
                logger.exception("Error in input callback, aborting")
                return (None, pyaudio.paAbort)

        self.input_stream = p.open(
            rate=self.sample_rate,
            channels=self.input_channels,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.block_size // 2,  # maybe 2 periods?
            input_device_index=device["index"],
            stream_callback=wrapped_callback,
            start=False,
        )

        self.input_stream.start_stream()
        return self.input_stream

    def output(self, device_name, callback, channels=None):
        """Register a callback to write to a output device stream"""

        device = self.find_output(device_name)
        channels = channels or device["maxOutputChannels"]
        print(f"Using output {device['name']}, {channels} channels")

        def wrapped_callback(_, frame_count, block_time, status):
            try:
                if status:
                    print("**** non zero status BUFFER OVER/UNDER RUN ?", status)

                samples = callback(_, frame_count, block_time, status)
                if isinstance(samples, bytearray):
                    samples = bytes(samples)

                self.num_blocks_written = self.num_blocks_written + 1
                return (samples, pyaudio.paContinue)

            except Exception:
                logger.exception("Error in output callback, aborting")
                return (None, pyaudio.paAbort)

        self.output_stream = p.open(
            rate=self.sample_rate,
            channels=channels,
            format=pyaudio.paInt16,
            output=True,
            frames_per_buffer=self.block_size // 2,  # maybe 2 periods?
            output_device_index=device["index"],
            stream_callback=wrapped_callback,
            start=False,
        )
        self.output_stream.start_stream()
        return self.output_stream

    def latest_block_written(self):
        """Return the last block written of the ring buffer"""
        return self.blocks[self.num_blocks_written % self.num_blocks]

    def shutdown(self):
        """Shutdown, halt PyAudio processes"""
        if self.shutdown_called:
            return
        self.shutdown_called = True
        print("Shutting down audio...")
        if self.output_stream is not None:
            self.output_stream.close()
        if self.input_stream is not None:
            self.input_stream.close()
        p.terminate()


# A Simple test
if __name__ == "__main__":
    print("Look for sys audio BlackHole and pipe to Speakers output")
    audio = None
    try:
        audio = Audio()

        def in_callback(block):
            """We don't need to do anything else, input is being stored"""

        def out_callback(_, frame_count, block_time, status):
            """Return the next block, thus piped / echoed to"""
            return audio.latest_block_written().samples

        audio.listen("BlackHole 2ch", in_callback)
        audio.output("Speakers", out_callback)

        while audio.input_stream.is_active():
            time.sleep(1)

    except KeyboardInterrupt:
        if audio is not None:
            audio.shutdown()
    finally:
        if audio is not None:
            audio.shutdown()
