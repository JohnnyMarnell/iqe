import numpy as np, sounddevice as sd
import time, threading, rtmidi2, math, os
from typing import NamedTuple

class Block(NamedTuple): index: int; size: int; start: int; end: int; wall_time: float; stream_time: float; \
    inputBufferAdcTime: float; outputBufferDacTime: float; currentTime: float

# Can change to system dependent, e.g. JACK, SoundFlower, channel counts etc
thru_in = sd.query_devices(device=os.environ.get('IQE_IN') or 'BlackHole', kind='input')
default_out = sd.query_devices(device=os.environ.get('IQE_OUT') or None, kind='output')

SAMPLES_SZ = BLOCK_TIMES_SZ = 1024 * 1024
samples = [None] * SAMPLES_SZ
blocks = [None] * BLOCK_TIMES_SZ
sr = 48000 # sample rate
audio_stream = None
block_index = 0
block_size = None
beat_time = None
spb = None # seconds per beat
midi_out = rtmidi2.MidiOut()
midi_port = int(os.environ.get('IQE_MIDI_OUT') or 0)
midi_out.open_port(midi_port)
print("Opened midi output", midi_out.get_port_name(midi_port))
running = True

""" Simple callback, write data to ring buffers """
def stream_callback(indata, outdata, num_frames, block_time, status):
    global block_index, audio_stream, samples, beat_time, spb
    
    stream_time = audio_stream.time
    wall_time = time.time()
    
    # Mix to mono, store in listened samples ring buffer, and pipe to speakers as well, so it becomes audible
    sample_start = block_index * num_frames
    sample_end = sample_start + num_frames
    for i in range(sample_start, sample_end):
        io_buffers_index = i - sample_start
        mono_mixed = (indata[io_buffers_index, 0] + indata[io_buffers_index, 1]) * 0.50
        samples[i % SAMPLES_SZ] = outdata[io_buffers_index, 0] = outdata[io_buffers_index, 1] = mono_mixed
    
    # Store info about this block in block ring buffer
    blocks[block_index % BLOCK_TIMES_SZ] = Block(index=block_index, size=num_frames,
                                                 start=sample_start, end=sample_end,
                                                 wall_time=wall_time, stream_time=stream_time,
                                                 inputBufferAdcTime=block_time.inputBufferAdcTime,
                                                 outputBufferDacTime=block_time.outputBufferDacTime,
                                                 currentTime=block_time.currentTime)

    if status:
        print("**** xrun STATUS:", status)
    block_index = block_index + 1


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
        spb = (silence_end - prev_silence_end) / sr
        beep_len = (silence_start - prev_silence_end + 1) / sr
        print("Detected BPM {} and beep length {}s, secs per beat {}, a beat sample # {}".format(60 / spb, beep_len, spb, silence_end))
        return (60 / spb, silence_end)
    return (None, None)


""" Try detecting tempo (look back max 6 seconds), and schedule metronome click """
def tempo_detect_thread():
    print("Starting tempo detection thread")
    def tick():
        global beat_time, spb
        while running:
            bidx = block_index - 1
            
            # Build numpy window of samples back maximum 6 seconds
            sample_end = bidx * block_size + block_size
            sample_start = max(0, sample_end - math.ceil(6 * sr))
            window = np.empty(sample_end - sample_start)
            for i in range(sample_start, sample_end):
                window[i - sample_start] = samples[i % SAMPLES_SZ]
            
            bpm, beat_sample_index_in_window = simple_detect_tempo(window)

            if bpm:
                # Using stream time and sample buffer index, get stream time of the beat, advance to next
                spb = 60 / bpm
                beat_sample = sample_start + beat_sample_index_in_window
                beat_block = blocks[math.floor(beat_sample / block_size) % BLOCK_TIMES_SZ]
                beat_time = beat_block.inputBufferAdcTime + (beat_sample - beat_block.start) / sr
                print("Beat occured at sample {} of block # {}, ranged [{}, {}) over {} samples == {} block size, stream time {}".format(
                    beat_sample, beat_block.index, beat_block.start, beat_block.end,
                    beat_block.end - beat_block.start, block_size, beat_time
                ))

                # Cook / fudge time seconds by output latency only (shrug) and current DAW settings (double shrug)
                beat_time = beat_time - audio_stream.latency[1]
                beat_time = beat_time - float(os.environ.get("IQE_LATENCY_SHIFT") or (2 * 64 / 48000))
                
                # Set two beats in the future for metronome to have time to click
                beat_time = beat_time + (math.ceil((audio_stream.time - beat_time) / spb) + 1) * spb
                
                # Debug
                print("\n\n ######## Debug info for last 40 blocks:")
                idiffCounts = {}
                for i in range(max(1, bidx - 40), bidx + 1):
                    block = blocks[i % BLOCK_TIMES_SZ]
                    prev = blocks[(i - 1) % BLOCK_TIMES_SZ]
                    idiff = block.inputBufferAdcTime - prev.inputBufferAdcTime
                    if (idiff < 0):
                        print("**** STRANGE, input clock went back in time for these blocks...\n", prev, "\n", block)
                    idiffCounts[idiff] = (idiffCounts.get(idiff) or 0) + 1
                print("Counts of differences of subsequent input clocks:", idiffCounts, "\n\n")
                break
            time.sleep(0.300)
    return threading.Thread(target=tick)


""" Busy-ish waiting to play clicks on time """
def metronome_click_thread():
    def tick():
        global midi_out, beat_time, spb
        print("Starting click thread")
        while running:
            if beat_time is None or spb is None:
                time.sleep(0.300)
            else:
                now = audio_stream.time
                until_beat = beat_time - now
                if until_beat <= 0:
                    print("click")
                    midi_out.send_noteon(11, 37, 127)
                    midi_out.send_noteoff(11, 37)
                    beat_time = now + spb + until_beat
                elif until_beat <= 0.005:
                    time.sleep(0)
                else:
                    time.sleep(until_beat * 0.50)
    return threading.Thread(target=tick)


# ****************************************
# Weirdly, with a 'high' latency (thus should be more stable?) I see clock goes back in time, every ~13 blocks...
# audio_stream = sd.Stream(samplerate=sr, channels=(2,2), callback=stream_callback, blocksize=1024,
#                          device=(thru_in['index'], default_out['index']), latency='high')
# ****************************************

# Maybe stable / maybe accurate? Wish the block size didn't need to be so high (especially compared to DAW performance)
# audio_stream = sd.Stream(samplerate=sr, channels=(2,2), callback=stream_callback, blocksize=1024,
#                          device=(thru_in['index'], default_out['index']), latency='low')

audio_stream = sd.Stream(samplerate=sr, channels=(2,2), callback=stream_callback, blocksize=4096,
                         device=(thru_in['index'], default_out['index']), latency='low')
with audio_stream:
    block_size = audio_stream.blocksize
    print("Stream processing started, I+O latency secs, blocksize:\n", audio_stream.latency, audio_stream.blocksize)
    threads = [tempo_detect_thread(), metronome_click_thread()]
    for thread in threads:
        thread.start()
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("Exiting...")
        running = False

"""

Notes:
- BPM and beep length calculations are accurate when I change in DAW
- DAW has low buffer settings (64) and low perceivable latency (e.g. playing midi instrument along),
  so I don't think that's much of a factor?
- The metronome clicks sound uniformly spaced, plus do not drift, so I don't think there's threading + timing problem
- I get best results (I think?) with subtracting output latency + perceived DAW latency, 
- Are my assumptions about the cdata struct times all wrong?
    - inputBufferAdcTime: the stream.time when this block_size number of samples started conversion, thus was read from input,
      or "heard", and n-th sample in the buffer must have processed at n/sr seconds later,
      or it would've sounded glitchy / weird?
    - How could the inputBufferAdcTime *decrease* (implying earlier?) in the next block processed? Bug?
    - The currentTime is the time this block is being processed / handled / called? I would assume this would vary, but shouldn't
      the input time, since it's reading one same-sized block of samples after another, be uniformly spaced by those
      block_size/sr seconds every time, otherwise it would've sounded weird / xruns?

"""

# Tried a lot of combos, xruns, and unexpected results :(
# audio_stream = sd.Stream(samplerate=sr, channels=(2,2), callback=stream_callback, blocksize=128,
#                          device=(thru_in['index'], default_out['index']), latency=0)
# audio_stream = sd.Stream(samplerate=sr, channels=(2,2), callback=stream_callback, blocksize=256,
#                          device=(thru_in['index'], default_out['index']), latency=0)
# audio_stream = sd.Stream(samplerate=sr, channels=(2,2), callback=stream_callback, blocksize=1024,
#                          device=(thru_in['index'], default_out['index']), latency=0)
# audio_stream = sd.Stream(samplerate=sr, channels=(2,2), callback=stream_callback, blocksize=64,
#                          device=(thru_in['index'], default_out['index']), latency='low')
# audio_stream = sd.Stream(samplerate=sr, channels=(2,2), callback=stream_callback, blocksize=128,
#                          device=(thru_in['index'], default_out['index']), latency='high')
# audio_stream = sd.Stream(samplerate=sr, channels=(2,2), callback=stream_callback, blocksize=512,
#                          device=(thru_in['index'], default_out['index']), latency='low')
# audio_stream = sd.Stream(samplerate=sr, channels=(2,2), callback=stream_callback, blocksize=64,
#                          device=(thru_in['index'], default_out['index']), latency='high')