#!/usr/bin/env python3
"""
Video Scene Transition and Loop Detection

This script analyzes videos to:
1. Detect scene transitions (hard cuts and significant visual changes)
2. Identify loop points for repetitive scenes
"""

import cv2
import numpy as np
import json
import argparse
from typing import List, Tuple, Dict, Optional
from pathlib import Path
import hashlib
from collections import deque
import warnings
warnings.filterwarnings('ignore')

class VideoSceneAnalyzer:
    def __init__(self, video_path: str, debug: bool = False):
        self.video_path = video_path
        self.debug = debug
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Resize for analysis to speed up processing
        self.analysis_size = (160, 90)  # 16:9 at low res for speed
        
        print(f"Video: {Path(video_path).name}")
        print(f"Resolution: {self.width}x{self.height}")
        print(f"FPS: {self.fps:.2f}")
        print(f"Total frames: {self.total_frames}")
        print(f"Duration: {self.total_frames/self.fps:.2f}s")
        print(f"Analysis resolution: {self.analysis_size[0]}x{self.analysis_size[1]}")
        print("-" * 50)
    
    def compute_frame_histogram(self, frame):
        """Compute color histogram for a frame"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = []
        # Compute histogram for each channel
        for i in range(3):
            h = cv2.calcHist([hsv], [i], None, [32], [0, 256])
            h = cv2.normalize(h, h).flatten()
            hist.extend(h)
        return np.array(hist)
    
    def compute_frame_features(self, frame):
        """Extract multiple features from a frame - focus on structure not color"""
        # Resize for faster processing
        small = cv2.resize(frame, self.analysis_size)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        
        # Compute gradient magnitude (motion/structure indicator)
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_mag = np.sqrt(grad_x**2 + grad_y**2)
        
        # Compute corner features (structural elements)
        corners = cv2.goodFeaturesToTrack(gray, 100, 0.01, 10)
        corner_count = len(corners) if corners is not None else 0
        
        # Compute texture complexity using local binary patterns idea
        texture_complexity = np.std(gray) * np.mean(np.abs(np.diff(gray, axis=1)))
        
        features = {
            'histogram': self.compute_frame_histogram(small),
            'edges': self.compute_edge_density(small),
            'gradient_mag': np.mean(gradient_mag),
            'gradient_std': np.std(gradient_mag),
            'corners': corner_count,
            'texture': texture_complexity,
            'brightness': np.mean(gray),
            'contrast': np.std(gray),
            'hash': self.compute_frame_hash(small),
            'gray_frame': gray  # Store for optical flow
        }
        return features
    
    def compute_edge_density(self, frame):
        """Compute edge density in the frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return np.sum(edges > 0) / edges.size
    
    def get_dominant_color(self, frame):
        """Get dominant color in HSV"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        return np.argmax(hist)
    
    def compute_frame_hash(self, frame, hash_size=8):
        """Compute perceptual hash of frame for loop detection"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (hash_size+1, hash_size))
        
        # Compute difference between adjacent pixels
        diff = resized[:, 1:] > resized[:, :-1]
        
        # Convert to hash
        return sum([2**i for (i, v) in enumerate(diff.flatten()) if v])
    
    def detect_scene_transitions(self, threshold_multiplier: float = 2.5) -> List[int]:
        """
        Detect scene transitions using structural and motion-based metrics
        Returns list of frame numbers where scenes begin
        """
        print("\n🎬 Detecting scene transitions (motion & structure based)...")
        
        transitions = []
        prev_features = None
        prev_gray = None
        differences = []
        
        # First pass: collect frame differences with optical flow
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame_idx = 0
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            features = self.compute_frame_features(frame)
            
            if prev_features is not None and prev_gray is not None:
                # Compute optical flow for motion detection
                flow = cv2.calcOpticalFlowFarneback(
                    prev_gray, features['gray_frame'], 
                    None, 0.5, 3, 15, 3, 5, 1.2, 0
                )
                flow_magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
                motion_score = np.mean(flow_magnitude)
                
                # Structure-based differences (less weight on color)
                hist_diff = cv2.compareHist(
                    features['histogram'], 
                    prev_features['histogram'], 
                    cv2.HISTCMP_BHATTACHARYYA
                )
                edge_diff = abs(features['edges'] - prev_features['edges'])
                gradient_diff = abs(features['gradient_mag'] - prev_features['gradient_mag']) / 255.0
                gradient_std_diff = abs(features['gradient_std'] - prev_features['gradient_std']) / 255.0
                corner_diff = abs(features['corners'] - prev_features['corners']) / 100.0
                texture_diff = abs(features['texture'] - prev_features['texture']) / 1000.0
                
                # Motion discontinuity detection
                motion_change = abs(motion_score - prev_features.get('motion', motion_score))
                
                # Weighted combination - prioritize structure and motion over color
                total_diff = (
                    hist_diff * 0.5 +           # Reduced weight on color histogram
                    edge_diff * 3.0 +            # High weight on edges
                    gradient_diff * 2.5 +        # High weight on gradients
                    gradient_std_diff * 2.0 +    # Gradient variation
                    corner_diff * 2.0 +          # Structural corners
                    texture_diff * 1.5 +         # Texture complexity
                    motion_change * 4.0          # Highest weight on motion changes
                )
                
                differences.append((frame_idx, total_diff, motion_score))
                prev_features['motion'] = motion_score
            
            prev_features = features
            prev_gray = features['gray_frame']
            frame_idx += 1
            
            if frame_idx % 100 == 0:
                print(f"  Analyzed {frame_idx}/{self.total_frames} frames...")
        
        # Second pass: find peaks with better peak detection
        if differences:
            diff_values = [d[1] for d in differences]
            mean_diff = np.mean(diff_values)
            std_diff = np.std(diff_values)
            threshold = mean_diff + threshold_multiplier * std_diff
            
            # Smooth differences to reduce noise
            from scipy.ndimage import gaussian_filter1d
            smoothed_diffs = gaussian_filter1d([d[1] for d in differences], sigma=1)
            
            # Find peaks in smoothed signal
            for i in range(2, len(smoothed_diffs) - 2):
                if smoothed_diffs[i] > threshold:
                    # Check if local maximum (peak)
                    is_peak = (smoothed_diffs[i] > smoothed_diffs[i-1] and 
                              smoothed_diffs[i] > smoothed_diffs[i+1] and
                              smoothed_diffs[i] > smoothed_diffs[i-2] and
                              smoothed_diffs[i] > smoothed_diffs[i+2])
                    
                    if is_peak:
                        # Check minimum distance from previous transition
                        if not transitions or differences[i][0] - transitions[-1] > self.fps * 0.5:
                            # Find exact frame of maximum change
                            window_start = max(0, i - 3)
                            window_end = min(len(differences), i + 4)
                            window_slice = differences[window_start:window_end]
                            
                            # Get frame with max diff in window
                            max_idx = max(range(len(window_slice)), 
                                        key=lambda x: window_slice[x][1])
                            refined_frame = window_slice[max_idx][0]
                            
                            transitions.append(refined_frame)
                            if self.debug:
                                print(f"  Transition at frame {refined_frame} "
                                      f"(t={refined_frame/self.fps:.2f}s), "
                                      f"diff={window_slice[max_idx][1]:.3f}, "
                                      f"motion={window_slice[max_idx][2]:.3f}")
        
        # Always include frame 0 as first scene
        transitions = [0] + transitions
        
        print(f"✅ Found {len(transitions)} scenes")
        return transitions
    
    def detect_loops(self, min_loop_frames: int = 30, max_loop_frames: int = 300) -> List[Dict]:
        """
        Detect potential loop points in scenes
        Returns list of loop candidates with start/end frames
        """
        print("\n🔄 Detecting loops...")
        
        loops = []
        frame_hashes = []
        frame_features = []
        
        # Collect hashes and features for all frames
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame_idx = 0
        
        print("  Building frame fingerprints...")
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            small = cv2.resize(frame, self.analysis_size)
            frame_hash = self.compute_frame_hash(small)
            frame_hashes.append(frame_hash)
            
            # Store histogram for similarity comparison
            hist = self.compute_frame_histogram(small)
            frame_features.append(hist)
            
            frame_idx += 1
            if frame_idx % 100 == 0:
                print(f"    Processed {frame_idx}/{self.total_frames} frames...")
        
        # Find potential loops
        print("  Searching for loops...")
        hash_map = {}
        
        for i, h in enumerate(frame_hashes):
            if h not in hash_map:
                hash_map[h] = []
            hash_map[h].append(i)
        
        # Look for repeating patterns
        for hash_val, indices in hash_map.items():
            if len(indices) < 2:
                continue
            
            # Check pairs of matching hashes
            for i in range(len(indices) - 1):
                for j in range(i + 1, len(indices)):
                    start_frame = indices[i]
                    potential_end = indices[j]
                    loop_length = potential_end - start_frame
                    
                    if min_loop_frames <= loop_length <= max_loop_frames:
                        # Verify loop quality by checking similarity
                        similarity = self.verify_loop_quality(
                            frame_features, start_frame, potential_end, loop_length
                        )
                        
                        if similarity > 0.85:  # High similarity threshold
                            loop_info = {
                                'start': start_frame,
                                'end': potential_end,
                                'length': loop_length,
                                'duration_sec': loop_length / self.fps,
                                'similarity': similarity,
                                'start_time': start_frame / self.fps,
                                'end_time': potential_end / self.fps
                            }
                            
                            # Check if this overlaps with existing loops
                            is_duplicate = False
                            for existing in loops:
                                if (abs(existing['start'] - start_frame) < 10 and 
                                    abs(existing['end'] - potential_end) < 10):
                                    is_duplicate = True
                                    break
                            
                            if not is_duplicate:
                                loops.append(loop_info)
                                if self.debug:
                                    print(f"  Found loop: frames {start_frame}-{potential_end} "
                                          f"({loop_info['duration_sec']:.2f}s), "
                                          f"similarity={similarity:.3f}")
        
        # Sort by start frame
        loops.sort(key=lambda x: x['start'])
        
        print(f"✅ Found {len(loops)} potential loops")
        return loops
    
    def verify_loop_quality(self, features: List, start: int, end: int, length: int) -> float:
        """
        Verify loop quality by checking similarity across multiple points
        """
        if length <= 0:
            return 0.0
        
        # Sample several points to verify the loop
        sample_points = min(10, length // 3)
        if sample_points < 2:
            sample_points = 2
        
        similarities = []
        step = max(1, length // sample_points)
        
        for offset in range(0, min(length, sample_points * step), step):
            if start + offset < len(features) and end + offset < len(features):
                sim = 1 - cv2.compareHist(
                    features[start + offset],
                    features[end + offset],
                    cv2.HISTCMP_BHATTACHARYYA
                )
                similarities.append(sim)
        
        return np.mean(similarities) if similarities else 0.0
    
    def analyze_scenes_in_detail(self, transitions: List[int]) -> List[Dict]:
        """
        Analyze each scene for additional properties
        """
        scenes = []
        
        for i in range(len(transitions)):
            start = transitions[i]
            end = transitions[i + 1] if i + 1 < len(transitions) else self.total_frames
            
            scene = {
                'index': i,
                'start_frame': start,
                'end_frame': end,
                'duration_frames': end - start,
                'duration_sec': (end - start) / self.fps,
                'start_time': start / self.fps,
                'end_time': end / self.fps
            }
            
            # Sample a frame from the middle of the scene for characteristics
            middle_frame = (start + end) // 2
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
            ret, frame = self.cap.read()
            
            if ret:
                features = self.compute_frame_features(frame)
                scene['avg_brightness'] = float(features['brightness'])
                scene['avg_contrast'] = float(features['contrast'])
                scene['gradient_mag'] = float(features['gradient_mag'])
                scene['corners'] = int(features['corners'])
                scene['texture'] = float(features['texture'])
                scene['edge_density'] = float(features['edges'])
            
            scenes.append(scene)
        
        return scenes
    
    def export_results(self, output_path: str, transitions: List[int], 
                      loops: List[Dict], scenes: List[Dict]):
        """Export analysis results to JSON"""
        results = {
            'video_info': {
                'path': self.video_path,
                'width': self.width,
                'height': self.height,
                'fps': self.fps,
                'total_frames': self.total_frames,
                'duration_sec': self.total_frames / self.fps
            },
            'transitions': transitions,
            'scenes': scenes,
            'loops': loops,
            'summary': {
                'num_scenes': len(scenes),
                'num_loops': len(loops),
                'avg_scene_duration': np.mean([s['duration_sec'] for s in scenes]) if scenes else 0
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to: {output_path}")
    
    def close(self):
        """Clean up resources"""
        self.cap.release()


def main():
    parser = argparse.ArgumentParser(description='Detect scene transitions and loops in video')
    parser.add_argument('video_path', help='Path to video file')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--threshold', '-t', type=float, default=2.5,
                       help='Transition detection threshold multiplier (default: 2.5)')
    parser.add_argument('--min-loop', type=int, default=30,
                       help='Minimum loop length in frames (default: 30)')
    parser.add_argument('--max-loop', type=int, default=300,
                       help='Maximum loop length in frames (default: 300)')
    parser.add_argument('--debug', '-d', action='store_true',
                       help='Enable debug output')
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        video_name = Path(args.video_path).stem
        output_path = f"{video_name}_scenes.json"
    
    # Analyze video
    analyzer = VideoSceneAnalyzer(args.video_path, debug=args.debug)
    
    try:
        # Detect transitions
        transitions = analyzer.detect_scene_transitions(args.threshold)
        
        # Analyze scenes
        scenes = analyzer.analyze_scenes_in_detail(transitions)
        
        # Detect loops
        loops = analyzer.detect_loops(args.min_loop, args.max_loop)
        
        # Export results
        analyzer.export_results(output_path, transitions, loops, scenes)
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 SUMMARY")
        print("=" * 50)
        print(f"Total scenes: {len(scenes)}")
        print(f"Total loops: {len(loops)}")
        
        if scenes:
            print(f"\nScene durations:")
            for i, scene in enumerate(scenes[:10]):  # Show first 10
                print(f"  Scene {i}: {scene['start_time']:.2f}s - {scene['end_time']:.2f}s "
                      f"({scene['duration_sec']:.2f}s)")
            if len(scenes) > 10:
                print(f"  ... and {len(scenes) - 10} more scenes")
        
        if loops:
            print(f"\nLoop points:")
            for i, loop in enumerate(loops[:5]):  # Show first 5
                print(f"  Loop {i}: frames {loop['start']}-{loop['end']} "
                      f"({loop['start_time']:.2f}s - {loop['end_time']:.2f}s), "
                      f"duration={loop['duration_sec']:.2f}s, "
                      f"similarity={loop['similarity']:.1%}")
            if len(loops) > 5:
                print(f"  ... and {len(loops) - 5} more loops")
        
    finally:
        analyzer.close()
    
    print(f"\n✨ Analysis complete! Check {output_path} for detailed results.")


if __name__ == "__main__":
    main()