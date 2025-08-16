#!/usr/bin/env python3
"""
Video trimmer using ffmpeg to remove frames from start and/or end of a video.

Usage:
    python trim_video.py input_video.mp4 [-s START_FRAMES] [-e END_FRAMES]
    
Example:
    python trim_video.py video.mp4 -s 30 -e 60
    This removes 30 frames from the beginning and 60 frames from the end
"""

import argparse
import subprocess
import os
import sys
from pathlib import Path


def get_video_info(input_file):
    """Get video duration and frame rate using ffprobe."""
    try:
        # Get frame rate
        cmd_fps = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=r_frame_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            input_file
        ]
        result_fps = subprocess.run(cmd_fps, capture_output=True, text=True, check=True)
        fps_str = result_fps.stdout.strip()
        
        # Parse frame rate (could be like "30/1" or "30000/1001")
        if '/' in fps_str:
            num, den = map(float, fps_str.split('/'))
            fps = num / den
        else:
            fps = float(fps_str)
        
        # Get total number of frames
        cmd_frames = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-count_packets',
            '-show_entries', 'stream=nb_read_packets',
            '-of', 'csv=p=0',
            input_file
        ]
        result_frames = subprocess.run(cmd_frames, capture_output=True, text=True, check=True)
        total_frames = int(result_frames.stdout.strip())
        
        return fps, total_frames
    
    except subprocess.CalledProcessError as e:
        print(f"Error getting video info: {e}")
        sys.exit(1)
    except (ValueError, ZeroDivisionError) as e:
        print(f"Error parsing video info: {e}")
        sys.exit(1)


def trim_video(input_file, start_frames=0, end_frames=0):
    """Trim video by removing specified frames from start and/or end."""
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    # Get video info
    fps, total_frames = get_video_info(input_file)
    print(f"Video info: {fps:.2f} fps, {total_frames} total frames")
    
    # Validate trim parameters
    frames_to_keep = total_frames - start_frames - end_frames
    if frames_to_keep <= 0:
        print(f"Error: Trimming {start_frames} from start and {end_frames} from end "
              f"would remove all {total_frames} frames!")
        sys.exit(1)
    
    # Calculate time positions
    start_time = start_frames / fps if start_frames > 0 else 0
    duration = frames_to_keep / fps
    
    # Generate output filename
    input_path = Path(input_file)
    output_file = input_path.parent / f"{input_path.stem}-trimmed{input_path.suffix}"
    
    # Build ffmpeg command
    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-y',  # Overwrite output file if it exists
    ]
    
    # Add seek and duration parameters
    if start_frames > 0:
        # Use -ss for seeking (more accurate when placed after -i)
        cmd.extend(['-ss', str(start_time)])
    
    # Set duration to keep only the frames we want
    cmd.extend(['-t', str(duration)])
    
    # Re-encode for frame-accurate trimming
    # This ensures we don't get black frames from cutting between keyframes
    cmd.extend([
        '-c:v', 'libx264',      # Re-encode video with H.264
        '-crf', '18',           # Quality (lower = better, 18 is visually lossless)
        '-preset', 'medium',    # Encoding speed/quality tradeoff
        '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
        '-c:a', 'aac',          # Re-encode audio to AAC
        '-b:a', '192k',         # Audio bitrate
    ])
    
    # Alternative: If you want faster processing but less accurate frame cutting,
    # you can try codec copy, but it may result in black frames:
    # cmd.extend([
    #     '-c:v', 'copy',  # Copy video codec
    #     '-c:a', 'copy',  # Copy audio codec
    # ])
    
    # Output file
    cmd.append(str(output_file))
    
    # Print the command for debugging
    print(f"\nTrimming video:")
    print(f"  Removing {start_frames} frames from start ({start_time:.2f}s)")
    print(f"  Removing {end_frames} frames from end")
    print(f"  Keeping {frames_to_keep} frames ({duration:.2f}s)")
    print(f"  Output: {output_file}")
    print(f"\nRunning command:")
    print(' '.join(cmd))
    print()
    
    try:
        # Run ffmpeg
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✓ Successfully created: {output_file}")
        
        # Verify the output
        out_fps, out_frames = get_video_info(str(output_file))
        print(f"✓ Output video: {out_frames} frames (expected ~{frames_to_keep} frames)")
        
        # Note: Frame count should be very close when re-encoding
        if abs(out_frames - frames_to_keep) > 2:
            print(f"⚠ Note: Output has {out_frames} frames (expected {frames_to_keep}).")
            print(f"  Difference of {abs(out_frames - frames_to_keep)} frames is likely due to encoding settings.")
    
    except subprocess.CalledProcessError as e:
        print(f"Error running ffmpeg: {e}")
        if e.stderr:
            print(f"ffmpeg error output:\n{e.stderr}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Trim video by removing frames from start and/or end',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s video.mp4 -s 30          # Remove 30 frames from start
  %(prog)s video.mp4 -e 60          # Remove 60 frames from end  
  %(prog)s video.mp4 -s 30 -e 60    # Remove 30 from start, 60 from end
        '''
    )
    
    parser.add_argument('input_file', help='Input video file')
    parser.add_argument('-s', '--start-frames', type=int, default=0,
                        help='Number of frames to remove from the beginning (default: 0)')
    parser.add_argument('-e', '--end-frames', type=int, default=0,
                        help='Number of frames to remove from the end (default: 0)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.start_frames < 0:
        print("Error: Start frames must be >= 0")
        sys.exit(1)
    if args.end_frames < 0:
        print("Error: End frames must be >= 0")
        sys.exit(1)
    if args.start_frames == 0 and args.end_frames == 0:
        print("Warning: No trimming specified (both -s and -e are 0)")
        print("The output will be a copy of the input.")
    
    # Run the trimming
    trim_video(args.input_file, args.start_frames, args.end_frames)


if __name__ == '__main__':
    main()