import sounddevice as sd, numpy as np, scipy.io.wavfile as wav
import librosa, time, threading, math, rtmidi2
from typing import NamedTuple
from collections import deque

class Result(NamedTuple): data: np.ndarray; time: float
class Block(NamedTuple): index: int; size: int; wall_time: float; stream_time: float; driver_time: any;
#class Samples(NamedTuple): samples: np.ndarray; ts: float; time: float; wall: float; duration: float; stream_time: float; block: Block
class Samples(NamedTuple): samples: np.ndarray; time: float; duration: float; block: Block
class BeatMatch(NamedTuple): beats: np.ndarray; avg_tempo: float; reported_tempo: float; time: float
class TempoPrediction(NamedTuple): samples: Samples; beats: BeatMatch; reported_tempo: float; time: float

# todo make these look ups
speakers = 2 # Core Audio speakers device, only plays out thru speaker
bh_in = 0 # if thru is played into, this input receives what's being played
thru = 3 # audio written to this device is forwarded (thus audible) to speakers, and looped back to black hole input

# Read from BH in (thus audio being played), and add to speakers
REQUEST_BLOCK_SIZE = 64
# we'll keep ring buff N blocks, to do numpy optimized
LOOK_BACK_BUFFER_SIZE = 1024 * 1024
BLOCK_BUFFER_SIZE = 1024 * 1024
HOP_LENGTH = 256
PREDICTION_INTERVAL = LOOK_BACK_SECONDS = PREDICT_FORWARD_SECONDS = 5
sr = 48000

look_back_rb = [0.0] * LOOK_BACK_BUFFER_SIZE
look_back_rb_idx = 0
block_buffer = [None] * BLOCK_BUFFER_SIZE
block_buffer_idx = 0
block_size = -1
blocks = 0
last_predict_wall = 0
audio_stream = None
first_wall_time = first_driver_currentTime = first_stream_time = None
detected_seconds_per_beat = -1
next_beat = None
# next_beats = deque([])

midi_out = rtmidi2.MidiOut()
midi_out.open_port(0)

def setInterval(callback, millis):
    def wrapper():
        setInterval(callback, millis)
        callback()
    t = threading.Timer(millis / 1_000.0, wrapper)
    t.start()
    return t

def first_block(indata, outdata, num_frames, block_time, status):
    global block_size, first_wall_time, first_driver_currentTime, first_stream_time
    first_stream_time = now()
    first_wall_time = time.time()
    first_driver_currentTime = block_time.currentTime
    print("stream processing started, block size", num_frames, audio_stream, now())
    block_size = num_frames
    setInterval(predict_beats, PREDICTION_INTERVAL * 1_000)

def onset_envelopes(samples):
    start = time.time()
    onset_env = librosa.onset.onset_strength_multi(y=samples, sr=sr,
                                            hop_length=HOP_LENGTH,
                                            aggregate=np.median, # default is mean
                                            lag=1, # default, unit? "time lag for computing differences"
                                            max_size=1, # default, do not filter freq bins
                                            detrend=False, # default, do not "filter onset strength to remove DC component"
                                            center=True, # Centered frame analysis in STFT, by hop length
                                            )
    onset_env = onset_env[..., 0, :]
    return Result(onset_env, time.time() - start)

def detect_tempo_from_onsets(onsets):
    start = time.time()
    t, beats = librosa.beat.beat_track(onset_envelope=onsets, sr=sr, units='time',
                                       hop_length=HOP_LENGTH,
                                       tightness=1000, # yikers island, what does this do... good? 800 1000, bad 400 600 1600
                                        # start_bpm=126,
                                        # trim=False,
                                       )
    avg_tempo = 60 / np.average(np.diff(beats))
    return BeatMatch(beats=beats, reported_tempo=t, avg_tempo=avg_tempo, time=time.time() - start)


def get_samples(block: Block):
    start = time.time()

    sample_end = (block.index + 1) * block.size
    sample_start = (block.index - math.ceil(LOOK_BACK_SECONDS * sr / block.size)) * block.size
    num_samples = sample_end - sample_start
    samples = np.ndarray((num_samples, ))
    samples.fill(0)
    
    for i in range(sample_start, sample_end):
        samples[i - sample_start] = look_back_rb[i % LOOK_BACK_BUFFER_SIZE]
    max = np.max(np.abs(samples))
    if max != 0:
        samples /= max
    # print("Samples rms:", sample_start, sample_end, np.sqrt(np.mean(samples**2)))
    return Samples(samples=samples, duration=num_samples / sr, block=block, time=time.time() - start)


def predict_beats():
    global detected_seconds_per_beat, next_beat, blocks

    start = time.time()
    latest_block = block_buffer[(blocks - 1) % BLOCK_BUFFER_SIZE]
    print("Running prediction, from last block", latest_block.index, ", from secs ago:", start - latest_block.wall_time)
    samples = get_samples(latest_block)
    onsets = onset_envelopes(samples.samples)
    tempo = detect_tempo_from_onsets(onsets.data)
    if tempo.reported_tempo and len(tempo.beats) >= 3:
        spb = 60 / tempo.reported_tempo
        secs_since_last_beat = samples.duration - tempo.beats[-1]
        # beat_time = (first_wall_time + (block_time - first_driver_currentTime)) - secs_since_last_beat
        # beat_time = samples.block.stream_time - secs_since_last_beat
        beat_time = samples.block.driver_time.inputBufferAdcTime - secs_since_last_beat

        while beat_time < now():
            beat_time = beat_time + spb
        
        detected_seconds_per_beat = spb
        next_beat = beat_time
    print("Predicted {} bpm, in {} secs, avg tempo {} # beats {}".format(tempo.reported_tempo, time.time() - start,
                                                                         tempo.avg_tempo, len(tempo.beats)))
    return 

def stream():
    global audio_stream
    def callback(indata, outdata, num_frames, block_time, status):
        global blocks, block_size, audio_stream
        stream_time = now()
        wall_time = time.time()

        if blocks == 0:
            first_block(indata, outdata, num_frames, block_time, status)

        # should try latency zero, and make sure constant, then take this out?
        if block_size != num_frames:
            raise Exception("Block size isn't constant?")
        
        # fill the listened audio look back buffer, mix to mono
        outdata.fill(0)
        sample_start = blocks * num_frames
        for i in range(num_frames):
            look_back_rb[(sample_start + i) % LOOK_BACK_BUFFER_SIZE] = (indata[i, 0] + indata[i, 1]) * 0.50

        # print("audio data!", blocks, np.sqrt(np.mean(indata ** 2)), np.sqrt(np.mean(outdata ** 2)), num_frames,
        #       block_time.inputBufferAdcTime, status)
        if status:
            print("**** STATUS", status)

        block_buffer[blocks % BLOCK_BUFFER_SIZE] = Block(index=blocks, size=num_frames, wall_time=wall_time,
                                                         stream_time=stream_time, driver_time=block_time)
        blocks = blocks + 1

    # could play with latency vs specifying blocksize? also is this "with" block right?
    audio_stream = sd.Stream(channels=2, callback=callback, blocksize=REQUEST_BLOCK_SIZE,
                             device=(bh_in, speakers), latency=None)
    audio_stream.start()
    print("Stream processing started...", now())
        

# todo: get rid of None check
def now():
    return None if audio_stream is None else audio_stream.time


def click_tick():
    global midi_out, next_beat, detected_seconds_per_beat
    
    while True:
        if next_beat is None:
            # time.sleep(0.200)
            time.sleep(0.005)
        elif now() > next_beat:
            midi_out.send_noteon(11, 37, 127)
            midi_out.send_noteoff(11, 37)
            next_beat = next_beat + detected_seconds_per_beat
            # time.sleep(detected_seconds_per_beat - 0.050)
            time.sleep(0.005)
        else:
            time.sleep(0.005)

def debug_listen(path, time, num, size, keep_first=True, anchor='closestDiff', play_matched=False,
                 play_full=True, keep_first_tempo=False):
    # load music segment, make n predictions
    print("loading and splitting into {} music segments of {} seconds".format(num + 1, size))
    full_duration = (num + 1) * size
    full, _ = librosa.load(path, sr=sr, offset=time - size, duration=full_duration)
    split = np.split(full, num + 1)
    predictions = []
    print("Making {} predictions".format(num))
    for i in range(num):
        samples = Samples(samples=split[i], duration=None, block=None, time=None)
        onsets = onset_envelopes(samples.samples)
        tempo = detect_tempo_from_onsets(onsets.data)
        # print("Detected tempo:", tempo.reported_tempo, tempo.avg_tempo)
        print("Beat separations", list(map(lambda d: "{:.4f}".format(d), np.diff(tempo.beats))))
        print("Beat absolute times", list(map(lambda d: "{:.4f}".format(d), tempo.beats + (time + (i - 1) * size))))
        predictions.append(tempo)
    print("Reported bpms:", list(map(lambda p: p.reported_tempo, predictions)))
    print("Average  bpms:", list(map(lambda p: p.avg_tempo, predictions)))
    print("# beats:", list(map(lambda p: len(p.beats), predictions)))

    # add click track and overlay
    print("Appending clicks per predictions")
    clicks = []
    if play_matched and play_full:
        clicks = list(predictions[0].beats)
    for i in range(num):
        tempo = predictions[i]
        prediction_start = i * size
        if i == 0 or not keep_first_tempo:
            spb = 60 / tempo.reported_tempo
        if i == 0 or not keep_first:
            if anchor == 'last':
                beat = tempo.beats[-1]
            # choose any beat with closest separation to predicted tempo
            elif anchor == 'closestDiff':
                diffs = np.abs(np.diff(tempo.beats) - spb)
                beat = tempo.beats[np.argmin(diffs)]
            
        while beat < prediction_start + 2 * size:
            if beat > prediction_start + size:
                clicks.append(beat)
            beat = beat + spb
    print("Building click track")
    print("Click times", list(map(lambda d: "{:.4f}".format(d), tempo.beats + (time + (i - 1) * size))))
    click_track = librosa.clicks(times=np.array(clicks), sr=sr, length=len(full))
    merged = full + click_track
    if not play_full:
        merged = merged[int(sr * size):]
    print("Playing")
    sd.play(merged, sr, device=speakers)
    sd.wait()

def debug_predictions():
    path = '/Users/inquesoemergency/Documents/tmp/Monolink (live) - Mayan Warrior - Burning Man 2022 [AQURf3JqnJY].mp3'
    # Always choosing a beat from last sounds jittery
    # debug_listen(path=path, time=42 * 60, num=5, size=5, keep_first=False)
    # debug_listen(path=path, time=42 * 60 + 4 * 5, num=1, size=5, keep_first=False)

    # Keeping first beat happens to work, on the off-beat sound
    # debug_listen(path=path, time=42 * 60, num=5, size=5, keep_first=True)

    # Later point in same window, same problem, all kinds of weird offsets
    # debug_listen(path=path, time=42 * 60 + 15, num=5, size=5, keep_first=False)

    # Again better to keep, happens to be on the down beat / near perfect enough
    # debug_listen(path=path, time=42 * 60 + 15, num=5, size=5, keep_first=True)

    # Use above best case, that was 5 predictions, make one big one instead
    # debug_listen(path=path, time=42 * 60 + 15, num=1, size=25, keep_first=True, play_matched=True)
    
    path = './jupyter/audio/Ed Sheeran - Bad Habits [Official Video] [orJSJGHjBLI].mp3'
    # listening to 5th prediction of 5 vs alone should sound the same, but I hear a lot of drift in former
    # last 5 seconds i'm talking about are "habits lead to you -- wooo ooh ooh"
    # abs. beat times look the same, bug in my code? time to sample drift in rendering?
    # debug_listen(path=path, time=60, num=5, size=5, keep_first=False)
    # debug_listen(path=path, time=60 + 4 * 5, num=1, size=5, keep_first=False)
    
    # lots of jitter in this example
    # debug_listen(path=path, time=93, num=5, size=5, keep_first=False)
    # keeping first prediction throughout is better but still drifts
    # debug_listen(path=path, time=93, num=5, size=5, keep_first=True, keep_first_tempo=True)
    # even worse
    # debug_listen(path=path, time=93, num=5, size=5, keep_first=True, keep_first_tempo=False)
    

debug_predictions()
    
# click_thread = threading.Thread(target=click_tick)
# click_thread.start()
# stream()
# # todo: remove this sleep!!!
# time.sleep(8 * 24 * 60 * 60)