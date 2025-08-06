#!/usr/bin/env python3
"""
Extract scenes from video using ffmpeg with copy codec (no re-encoding)
Uses the scene detection JSON output to quickly split video into scenes
"""

import json
import subprocess
import argparse
from pathlib import Path
import sys

def extract_scenes(video_path: str, scenes_json_path: str, output_dir: str = None, 
                   format: str = None, verbose: bool = False):
    """
    Extract scenes from video using ffmpeg copy codec
    
    Args:
        video_path: Path to input video
        scenes_json_path: Path to JSON file with scene data
        output_dir: Directory for output files (default: same as video)
        format: Output format (default: same as input)
        verbose: Print ffmpeg commands
    """
    
    # Load scene data
    with open(scenes_json_path, 'r') as f:
        data = json.load(f)
    
    scenes = data['scenes']
    fps = data['video_info']['fps']
    total_frames = data['video_info']['total_frames']
    
    # Setup paths
    video_path = Path(video_path)
    if not video_path.exists():
        print(f"❌ Video file not found: {video_path}")
        sys.exit(1)
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = video_path.parent
    
    # Determine output format
    if not format:
        format = video_path.suffix[1:]  # Remove the dot
    
    base_name = video_path.stem
    
    print(f"🎬 Extracting {len(scenes)} scenes from: {video_path.name}")
    print(f"📁 Output directory: {output_dir}")
    print(f"🎞️  Format: {format}")
    print("-" * 50)
    
    successful = 0
    failed = 0
    
    for i, scene in enumerate(scenes):
        scene_num = i + 1
        start_time = scene['start_time']
        end_time = scene['end_time']
        duration = scene['duration_sec']
        
        # Create output filename with scene info
        output_file = output_dir / f"{base_name}_scene{scene_num:02d}_{start_time:.1f}s-{end_time:.1f}s.{format}"
        
        # Build ffmpeg command
        # Using -ss before -i for faster seeking
        # -c copy for stream copy (no re-encoding)
        # -avoid_negative_ts make_zero to handle timestamp issues
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),  # Seek to start time (fast seek before input)
            '-i', str(video_path),   # Input file
            '-t', str(duration),     # Duration to extract
            '-c', 'copy',            # Copy codecs (no re-encoding)
            '-avoid_negative_ts', 'make_zero',  # Fix timestamp issues
            '-y',                    # Overwrite output files
            str(output_file)
        ]
        
        if verbose:
            print(f"\n🔧 Command: {' '.join(cmd)}")
        
        print(f"  Scene {scene_num}/{len(scenes)}: {start_time:.2f}s - {end_time:.2f}s ({duration:.2f}s) -> {output_file.name}")
        
        try:
            # Run ffmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            successful += 1
            
            # Check file was created and has size
            if output_file.exists():
                size_mb = output_file.stat().st_size / (1024 * 1024)
                print(f"    ✅ Created: {size_mb:.2f} MB")
            else:
                print(f"    ⚠️  File may not have been created properly")
                
        except subprocess.CalledProcessError as e:
            failed += 1
            print(f"    ❌ Failed: {e}")
            if verbose and e.stderr:
                print(f"    Error output: {e.stderr[:500]}")
    
    print("-" * 50)
    print(f"\n✨ Extraction complete!")
    print(f"   Successful: {successful}/{len(scenes)}")
    if failed > 0:
        print(f"   Failed: {failed}/{len(scenes)}")
    
    return successful, failed


def create_concat_file(scenes_json_path: str, output_dir: str, base_name: str, format: str):
    """
    Create a concat file for ffmpeg to rejoin scenes if needed
    """
    concat_file = Path(output_dir) / f"{base_name}_concat.txt"
    
    with open(scenes_json_path, 'r') as f:
        data = json.load(f)
    
    scenes = data['scenes']
    
    with open(concat_file, 'w') as f:
        for i, scene in enumerate(scenes):
            scene_num = i + 1
            start_time = scene['start_time']
            end_time = scene['end_time']
            filename = f"{base_name}_scene{scene_num:02d}_{start_time:.1f}s-{end_time:.1f}s.{format}"
            f.write(f"file '{filename}'\n")
    
    print(f"📝 Created concat file: {concat_file}")
    print(f"   To rejoin scenes: ffmpeg -f concat -safe 0 -i {concat_file.name} -c copy {base_name}_rejoined.{format}")
    
    return concat_file


def main():
    parser = argparse.ArgumentParser(
        description='Extract scenes from video using ffmpeg (no re-encoding)',
        epilog='Example: %(prog)s video.mp4 video_scenes.json -o scenes/'
    )
    
    parser.add_argument('video_path', 
                       help='Path to input video file')
    parser.add_argument('scenes_json', 
                       help='Path to scenes JSON file from detect_video_scenes.py')
    parser.add_argument('-o', '--output-dir', 
                       help='Output directory (default: same as video)')
    parser.add_argument('-f', '--format', 
                       help='Output format (default: same as input)')
    parser.add_argument('-c', '--concat', action='store_true',
                       help='Create concat file for rejoining scenes')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Print ffmpeg commands')
    parser.add_argument('--scene', type=int,
                       help='Extract only specific scene number (1-based)')
    
    args = parser.parse_args()
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg not found. Please install ffmpeg first.")
        print("   macOS: brew install ffmpeg")
        print("   Ubuntu: sudo apt-get install ffmpeg")
        sys.exit(1)
    
    # If specific scene requested, modify the JSON data
    if args.scene:
        with open(args.scenes_json, 'r') as f:
            data = json.load(f)
        
        if args.scene < 1 or args.scene > len(data['scenes']):
            print(f"❌ Scene {args.scene} not found. Available: 1-{len(data['scenes'])}")
            sys.exit(1)
        
        # Create temporary JSON with just the requested scene
        import tempfile
        temp_json = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        data['scenes'] = [data['scenes'][args.scene - 1]]
        json.dump(data, temp_json)
        temp_json.close()
        args.scenes_json = temp_json.name
        print(f"📌 Extracting only scene {args.scene}")
    
    # Extract scenes
    successful, failed = extract_scenes(
        args.video_path,
        args.scenes_json,
        args.output_dir,
        args.format,
        args.verbose
    )
    
    # Create concat file if requested
    if args.concat and successful > 0:
        video_path = Path(args.video_path)
        output_dir = args.output_dir or video_path.parent
        format = args.format or video_path.suffix[1:]
        create_concat_file(args.scenes_json, output_dir, video_path.stem, format)


if __name__ == "__main__":
    main()