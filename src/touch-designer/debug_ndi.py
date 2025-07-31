#!/usr/bin/env python3
"""Debug NDI receive"""

from cyndilib.wrapper.ndi_recv import RecvColorFormat, RecvBandwidth
from cyndilib.finder import Finder
from cyndilib.receiver import Receiver, ReceiveFrameType
import time

finder = Finder()
finder.open()
time.sleep(1)

source = next(finder.iter_sources())
print(f'Source: {source}')

receiver = Receiver(
    source=source,
    color_format=RecvColorFormat.RGBX_RGBA,
    bandwidth=RecvBandwidth.highest
)

time.sleep(1)
print(f'Connected: {receiver.is_connected()}')

# Try different receive types
print('\nTrying different receive types:')
for i in range(10):
    # Try recv_all
    result = receiver.receive(ReceiveFrameType.recv_all, 500)
    print(f'Attempt {i}: result={result}')
    
    if result > 0:
        print(f'  has_video: {receiver.has_video_frame()}')
        print(f'  has_audio: {receiver.has_audio_frame()}')
        print(f'  has_metadata: {receiver.has_metadata_frame()}')
        
        if receiver.has_video_frame():
            vf = receiver.video_frame
            if vf:
                print(f'  Video: {vf.width}x{vf.height}')
                break