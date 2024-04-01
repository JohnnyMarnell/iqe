import sys
import time
import threading
import math
import argparse
from dataclasses import dataclass
from pythonosc import udp_client
import librosa
import numpy as np
from pyaudio_utils import Audio, Block


@dataclass
class Window:
    """Sample window built from recently heard blocks. Could we cache these?"""

    samples: np.ndarray
    start_block: Block
    end_block: Block


class BeatDetective:
    """Detect past beats using librosa, and fire events for upcoming ones"""

    def __init__(self, block_size=64, sample_rate=48000, seconds=5 * 60):
        self.audio = Audio(
            block_size=block_size, sample_rate=sample_rate, seconds=seconds
        )
        self.osc = udp_client.SimpleUDPClient("127.0.0.1", 3232)
        self.predict_thread = None
        self.running = False
        self.bpm = 0
        self.spb = 0
        self.last_beat = 0
        self.last_update = None
        self.tempo_clear()

    def fire_beat(self):
        """ToDo:make these configurable event handlers"""
        self.osc.send_message("/lx/tempo/beat", 1.0)

    def tempo_update(self, bpm, beat_time, now):
        """ToDo:make these configurable event handlers"""
        # Set clock back to internal
        self.osc.send_message("/lx/tempo/bpm", self.bpm)
        self.osc.send_message("/lx/tempo/clockSource", 0)

        self.bpm = bpm
        self.spb = 60 / self.bpm  # seconds per beat
        self.last_beat = beat_time + math.floor((now - beat_time) / self.spb) * self.spb

        print(f"Tempo update sent for {bpm:2f} bpm")

    def tempo_clear(self):
        """ToDo:make these configurable event handlers"""
        self.bpm = 0
        self.last_update = None
        # Temporarily set clock source to OSC (2), so it doesn't auto tick
        self.osc.send_message("/lx/tempo/clockSource", 2)
        print("Tempo cleared, clock stopped.")

    def check_and_fire_beat(self):
        """Called per tick, check if we need to fire a beat event"""
        if not self.bpm:
            return
        now = self.audio.time()
        if now - self.last_beat >= self.spb:
            self.fire_beat()
            self.last_beat += self.spb

    def predict(self, secs_back=10, update=True):
        """Make a prediction using librosa analysis of past, set next beat and update tempo if needed"""

        now = self.audio.time()
        start = now
        window = self.window(secs_back_start=secs_back)
        bpm, beats = self.detect_recent_past_beats(
            window.samples, sr=self.audio.sample_rate
        )

        # Clear the last tempo if we need to
        if not bpm or len(beats) < 1:
            if update:
                print("Skipping this prediction update...")
            elif self.last_update:
                self.tempo_clear()
            self.bpm = 0
            return

        if bpm >= 160:
            bpm = bpm / 2
        spb = 60 / bpm

        # anchor_beat_index = 0
        anchor_beat_index = len(beats) - 1
        beat_ests = [
            beat + (anchor_beat_index - k) * spb for k, beat in enumerate(beats)
        ]
        anchor = np.mean(beat_ests)
        beat_time = window.start_block.time.input_buffer_adc_time + anchor

        if update or not self.last_update:
            self.tempo_update(bpm, beat_time, now)
        if update:
            self.last_update = now

        wsecs = len(window.samples) / self.audio.sample_rate
        avg_tempo = 60 / np.average(np.diff(beats))
        run_time = self.audio.time() - start
        print(
            f"Window secs: {wsecs:.2f}, returned tempo {bpm:.2f}, "
            + f"avg {avg_tempo:.2f}, # beats {len(beats)}, in {run_time:.2f} secs"
        )

    def past_block(self, secs_back):
        """Get a block from the past, some seconds back (shift by one for added insurance)"""
        # ToDo: the frame buffer will wrap, problems?
        spb = self.audio.sample_rate / self.audio.block_size
        return self.audio.num_blocks_read - math.ceil(secs_back * spb) - 1

    def window(self, secs_back_start=10, secs_back_end=0):
        """Rounded to blocks, build a mono, [-1, 1] normalized numpy array window of near desired length"""

        end_block = self.past_block(secs_back_end)
        start_block = max(self.past_block(secs_back_start), 0)

        # print(f"Num blocks read: {self.audio.num_blocks_read} about {self.audio.num_blocks_read \
        #   * self.audio.block_size / self.audio.sample_rate} secs")
        # print(f"Start and end block {start_block} => {end_block}")

        # First concat (hopefully fast) all the block bytes to one array (assuming 16 bit integers, 2 bytes)
        stream_bytes = bytearray()
        for i in range(start_block, end_block + 1):
            stream_bytes.extend(self.audio.blocks[i % self.audio.num_blocks].samples)

        # Now convert this to [-1, 1] mono mixed numpy array for librosa
        audio_array = np.frombuffer(stream_bytes, dtype=np.int16)
        # Reshape the audio array into separate channels
        audio_array = audio_array.reshape((-1, self.audio.input_channels))
        # Mix channels to create a mono signal
        mono_signal = np.mean(audio_array, axis=1)
        # Normalize the mono signal between -1 and 1
        max_sample = np.max(np.abs(mono_signal))
        if max_sample > 0:
            mono_signal = mono_signal / max_sample

        return Window(
            samples=mono_signal,
            start_block=self.audio.blocks[start_block % self.audio.num_blocks],
            end_block=self.audio.blocks[end_block % self.audio.num_blocks],
        )

    def detect_recent_past_beats(self, samples, sr, hop_length=256):
        """Use librosa to detect recent beats from the past"""

        predict_env = librosa.onset.onset_strength_multi
        onset_env = predict_env(
            y=samples,
            sr=sr,
            hop_length=hop_length,
            aggregate=np.median,  # default is mean
            lag=1,  # default, unit? "time lag for computing differences"
            max_size=1,  # default, do not filter freq bins
            detrend=False,  # default, do not "filter onset strength to remove DC component"
            center=True,  # Centered frame analysis in STFT, by hop length
        )
        onset_env = onset_env[..., 0, :]
        # HOP_LENGTH = 512
        # predict_env = librosa.onset.onset_strength
        # onset_env = predict_env(y=samples, sr=sr,
        #                         # hop_length=hop_length,
        #                         aggregate=np.median, # default is mean
        #                         lag=1, # default, unit? "time lag for computing differences"
        #                         max_size=1, # default, do not filter freq bins
        #                         detrend=False, # default, do not "filter onset strength to remove DC component"
        #                         center=True, # Centered frame analysis in STFT, by hop length
        #                         )

        return librosa.beat.beat_track(
            onset_envelope=onset_env,
            sr=sr,
            units="time",
            hop_length=hop_length,
            tightness=1000,  # yikers island, what does this do... good? 800 1000, bad 400 600 1600
            # start_bpm=126,
            # trim=False,
        )

    def predict_loop(self, predict_interval_secs=5, secs_back=None, update=True):
        """Build a loop that runs predictions at an interval"""

        secs_back = predict_interval_secs if secs_back is None else secs_back

        def loop():
            print(
                f"Starting prediction loop calculating every {predict_interval_secs} secs"
            )
            time.sleep(predict_interval_secs)
            while self.running:
                start = time.time()
                self.predict(secs_back=secs_back, update=update)
                time.sleep(max(0, predict_interval_secs - (time.time() - start)))

        return loop

    def run(
        self,
        predict_interval_secs=5,
        secs_back=None,
        in_device="BlackHole 2ch",
        pipe=False,
        out_device="Speakers",
    ):
        """Build a short and longer prediction loop and start them running in multiple threads"""

        self.predict_thread = threading.Thread(
            target=self.predict_loop(
                predict_interval_secs=predict_interval_secs, secs_back=secs_back
            )
        )
        tempo_thread = threading.Thread(
            target=self.predict_loop(
                predict_interval_secs=1, secs_back=1.5, update=False
            )
        )

        def in_callback(block):
            self.check_and_fire_beat()

        self.audio.listen(in_device, in_callback)

        if pipe:

            def out_callback(_, frame_count, block_time, status):
                return self.audio.latest_block_written().samples

            self.audio.output(out_device, out_callback)

        self.running = True
        self.predict_thread.start()
        tempo_thread.start()
        while self.audio.input_stream.is_active():
            time.sleep(1)

    def shutdown(self):
        """Shutdown underlying audio"""
        self.running = False
        self.audio.shutdown()

    def dump_env_info(self):
        """Debug info"""
        print("Python version:" + sys.version)
        print("****** Enumerating sys.modules:")
        for module in sys.modules.items():
            print(module)
        print("****** Package resources distros:")
        for dist in __import__("pkg_resources").working_set:
            print(dist.project_name.replace("Python", ""))


# Setup command arguments
parser = argparse.ArgumentParser(
    description="Beat detective: predict and fire beat events, e.g. with MIDI or OSC",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    "-i",
    "--input",
    type=str,
    metavar="IN",
    default="BlackHole 2ch",
    help="Input to listen for beats",
)
parser.add_argument(
    "-o",
    "--output",
    type=str,
    metavar="OUT",
    default="Speakers",
    help="Output device name, if piping audio thru",
)
parser.add_argument(
    "--pipe",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="Pipe audio through to output device",
)

args = parser.parse_args()

beat_detective = BeatDetective(block_size=64, sample_rate=48000, seconds=30)
# beat_detective.dump_env_info()
try:
    beat_detective.run(
        predict_interval_secs=10,
        secs_back=10,
        in_device=args.input,
        pipe=args.pipe,
        out_device=args.output,
    )
except KeyboardInterrupt as err:
    beat_detective.shutdown()
