import numpy as np
from scipy.io import wavfile

def chat_gpt_beep():
    # Set the sample rate and duration of the beep
    sample_rate = 48000
    # duration = 1  # seconds
    # duration = .25  # seconds
    duration = .050
    # duration = .025

    # Set the frequency of the beep (A4 note)
    frequency = 440  # Hz

    # Compute the time axis of the signal
    t = np.linspace(0, duration, int(duration * sample_rate), endpoint=False)

    # Create a sine wave with the specified frequency and duration
    signal = np.sin(2 * np.pi * frequency * t)

    # Apply a Hann window to the signal to make it fade out quickly
    window = np.hanning(len(signal))
    signal *= window

    # Scale the signal to the range [-1, 1]
    signal /= np.max(np.abs(signal))

    # Save the signal as a WAV file
    wav.write("jupyter/audio/beep.wav", sample_rate, signal)
    
def inspect_devices():
    i = 0
    for device in sd.query_devices():
        print("Device #", i, device)
        i = i + 1
    
def test_play_file():
    filename = 'jupyter/audio/test.wav'
    # Extract data and sampling rate from file
    data, sr = sf.read(filename, dtype='float32')
    sd.play(data, sr, device=speakers)
    # status = sd.wait()

def test_play_generated_tone():
    sr = 48000
    tone = np.sin(2 * np.pi * 440 * np.arange(0, 1, 1/sr))  # generate the tone
    sd.play(tone, sr, device=speakers)  # play it
    sd.wait()  # wait for the tone to finish

def cgpt_square_wav():
    # Set the parameters
    frequency = 440  # Frequency of the square wave in Hz
    duration = 0.2  # Duration of the square wave in seconds
    sampling_rate = 48000  # Number of samples per second
    amplitude = 0.3  # Amplitude of the square wave

    # Generate the time axis
    t = np.linspace(0, duration, int(duration * sampling_rate), endpoint=False)

    # Generate the square wave
    square_wave = amplitude * np.sign(np.sin(2 * np.pi * frequency * t))

    # Scale the square wave to 16-bit integer range
    scaled_wave = np.int16(square_wave * 32767)

    # Save the square wave as a WAV file
    output_file = "/tmp/square_wave.wav"
    wavfile.write(output_file, sampling_rate, scaled_wave)

cgpt_square_wav()
