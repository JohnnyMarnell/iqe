#!/usr/bin/env python3
"""
Manually adjust scene boundaries from detection results
Useful for fine-tuning the exact transition frames
"""

import json
import argparse
from pathlib import Path

def adjust_boundaries(scenes_json_path: str, adjustments: dict = None):
    """
    Apply manual adjustments to scene boundaries
    
    Args:
        scenes_json_path: Path to scenes JSON file
        adjustments: Dict of scene_index: frame_adjustment pairs
    """
    
    # Load scene data
    with open(scenes_json_path, 'r') as f:
        data = json.load(f)
    
    scenes = data['scenes']
    transitions = data['transitions']
    fps = data['video_info']['fps']
    total_frames = data['video_info']['total_frames']
    
    print(f"📊 Current scene boundaries:")
    for i, scene in enumerate(scenes):
        print(f"  Scene {i+1}: frames {scene['start_frame']}-{scene['end_frame']} "
              f"({scene['start_time']:.2f}s - {scene['end_time']:.2f}s)")
    
    if adjustments:
        print(f"\n🔧 Applying adjustments...")
        
        # Apply adjustments to transitions
        for scene_idx, adjustment in adjustments.items():
            if scene_idx < 0 or scene_idx >= len(transitions):
                print(f"  ⚠️  Scene {scene_idx} out of range")
                continue
            
            old_frame = transitions[scene_idx]
            new_frame = max(0, min(total_frames, transitions[scene_idx] + adjustment))
            transitions[scene_idx] = new_frame
            
            print(f"  Scene {scene_idx+1} start: {old_frame} -> {new_frame} "
                  f"(adjusted by {adjustment:+d} frames)")
        
        # Rebuild scenes from adjusted transitions
        new_scenes = []
        for i in range(len(transitions)):
            start = transitions[i]
            end = transitions[i + 1] if i + 1 < len(transitions) else total_frames
            
            scene = {
                'index': i,
                'start_frame': start,
                'end_frame': end,
                'duration_frames': end - start,
                'duration_sec': (end - start) / fps,
                'start_time': start / fps,
                'end_time': end / fps
            }
            
            # Copy over analysis data if it exists
            if i < len(scenes):
                for key in ['avg_brightness', 'avg_contrast', 'dominant_hue', 'edge_density']:
                    if key in scenes[i]:
                        scene[key] = scenes[i][key]
            
            new_scenes.append(scene)
        
        # Update data
        data['transitions'] = transitions
        data['scenes'] = new_scenes
        
        # Save adjusted file
        output_path = scenes_json_path.replace('.json', '_adjusted.json')
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✅ Adjusted boundaries saved to: {output_path}")
        print(f"\n📊 New scene boundaries:")
        for scene in new_scenes:
            print(f"  Scene {scene['index']+1}: frames {scene['start_frame']}-{scene['end_frame']} "
                  f"({scene['start_time']:.2f}s - {scene['end_time']:.2f}s)")
        
        return output_path
    
    return scenes_json_path


def main():
    parser = argparse.ArgumentParser(
        description='Adjust scene boundaries manually',
        epilog='Example: %(prog)s video_scenes.json --adjust 2:+5 4:-3 5:+2'
    )
    
    parser.add_argument('scenes_json', 
                       help='Path to scenes JSON file')
    parser.add_argument('--adjust', '-a', nargs='+',
                       help='Adjustments as scene:frames pairs (e.g., 2:+5 4:-3)')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive mode to adjust each scene')
    
    args = parser.parse_args()
    
    adjustments = {}
    
    if args.adjust:
        # Parse adjustment arguments
        for adj in args.adjust:
            try:
                scene_str, frames_str = adj.split(':')
                scene_idx = int(scene_str) - 1  # Convert to 0-based
                frames = int(frames_str)
                adjustments[scene_idx] = frames
            except ValueError:
                print(f"⚠️  Invalid adjustment format: {adj}")
                print("   Use format: scene:frames (e.g., 2:+5 or 4:-3)")
    
    elif args.interactive:
        # Interactive adjustment mode
        with open(args.scenes_json, 'r') as f:
            data = json.load(f)
        
        scenes = data['scenes']
        transitions = data['transitions']
        
        print("\n🎮 Interactive adjustment mode")
        print("   Enter frame adjustment for each scene (or press Enter to skip)")
        print("   Positive values move the start later, negative values earlier")
        print()
        
        for i in range(1, len(transitions)):  # Skip scene 0 (always starts at 0)
            scene = scenes[i]
            print(f"Scene {i+1} currently starts at frame {scene['start_frame']} "
                  f"({scene['start_time']:.2f}s)")
            
            adj_str = input(f"  Adjustment (e.g., +5 or -3): ").strip()
            if adj_str:
                try:
                    frames = int(adj_str)
                    adjustments[i] = frames
                except ValueError:
                    print(f"  ⚠️  Invalid input, skipping scene {i+1}")
    
    # Apply adjustments
    if adjustments:
        adjust_boundaries(args.scenes_json, adjustments)
    else:
        print("ℹ️  No adjustments specified")
        print("   Use --adjust or --interactive to modify boundaries")


if __name__ == "__main__":
    main()