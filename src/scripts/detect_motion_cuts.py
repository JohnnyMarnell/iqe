#!/usr/bin/env python3
"""
Simplified motion-based scene detection
Focus on grayscale motion jumps to detect hard cuts
"""

import cv2
import numpy as np
import json
import argparse
from pathlib import Path
from typing import List, Tuple
import warnings
warnings.filterwarnings('ignore')

class MotionCutDetector:
    def __init__(self, video_path: str, debug: bool = False):
        self.video_path = video_path
        self.debug = debug
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Process at lower resolution for speed
        self.process_width = min(320, self.width)
        scale = self.process_width / self.width
        self.process_height = int(self.height * scale)
        
        print(f"Video: {Path(video_path).name}")
        print(f"Resolution: {self.width}x{self.height}")
        print(f"Processing at: {self.process_width}x{self.process_height}")
        print(f"FPS: {self.fps:.2f}")
        print(f"Total frames: {self.total_frames}")
        print(f"Duration: {self.total_frames/self.fps:.2f}s")
        print("-" * 50)
    
    def compute_frame_signature(self, gray_frame):
        """Compute a motion-sensitive signature for a frame"""
        # Compute gradients (edges/motion)
        grad_x = cv2.Sobel(gray_frame, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray_frame, cv2.CV_32F, 0, 1, ksize=3)
        gradient_mag = np.sqrt(grad_x**2 + grad_y**2)
        
        # Divide frame into regions for spatial information
        h, w = gray_frame.shape
        regions = []
        for i in range(2):  # 2x2 grid
            for j in range(2):
                region = gray_frame[i*h//2:(i+1)*h//2, j*w//2:(j+1)*w//2]
                regions.append({
                    'mean': np.mean(region),
                    'std': np.std(region),
                    'gradient': np.mean(gradient_mag[i*h//2:(i+1)*h//2, j*w//2:(j+1)*w//2])
                })
        
        return {
            'global_mean': np.mean(gray_frame),
            'global_std': np.std(gray_frame),
            'gradient_mean': np.mean(gradient_mag),
            'gradient_std': np.std(gradient_mag),
            'regions': regions,
            'histogram': cv2.calcHist([gray_frame], [0], None, [32], [0, 256]).flatten()
        }
    
    def detect_cuts(self, threshold_multiplier: float = 3.0) -> List[int]:
        """
        Detect hard cuts based on motion/structure jumps
        """
        print("\n🎬 Detecting scene cuts (grayscale motion-based)...")
        
        cuts = []
        prev_gray = None
        prev_signature = None
        motion_scores = []
        frame_idx = 0
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Convert to grayscale and resize
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_small = cv2.resize(gray, (self.process_width, self.process_height))
            
            if prev_gray is not None:
                # Compute optical flow magnitude
                flow = cv2.calcOpticalFlowFarneback(
                    prev_gray, gray_small, None,
                    0.5, 3, 15, 3, 5, 1.2, 0
                )
                flow_mag = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
                avg_motion = np.mean(flow_mag)
                max_motion = np.max(flow_mag)
                
                # Compute frame difference
                frame_diff = cv2.absdiff(prev_gray, gray_small)
                avg_diff = np.mean(frame_diff)
                
                # Compute signature changes
                signature = self.compute_frame_signature(gray_small)
                
                # Compare histograms
                hist_corr = cv2.compareHist(
                    signature['histogram'], 
                    prev_signature['histogram'],
                    cv2.HISTCMP_CORREL
                )
                
                # Compare regional changes
                region_changes = []
                for i, (r1, r2) in enumerate(zip(signature['regions'], prev_signature['regions'])):
                    change = abs(r1['mean'] - r2['mean']) + abs(r1['gradient'] - r2['gradient'])
                    region_changes.append(change)
                max_region_change = max(region_changes)
                
                # Combine metrics - emphasize sudden changes
                motion_jump = abs(avg_motion - motion_scores[-1]['avg_motion']) if motion_scores else 0
                
                score = {
                    'frame': frame_idx,
                    'avg_motion': avg_motion,
                    'max_motion': max_motion,
                    'motion_jump': motion_jump,
                    'frame_diff': avg_diff,
                    'hist_corr': 1 - hist_corr,  # Convert to distance
                    'region_change': max_region_change,
                    'gradient_change': abs(signature['gradient_mean'] - prev_signature['gradient_mean'])
                }
                
                # Combined cut score
                score['cut_score'] = (
                    motion_jump * 5.0 +  # Sudden motion changes
                    score['frame_diff'] * 0.03 +  # Pixel differences
                    score['hist_corr'] * 2.0 +  # Histogram changes
                    score['region_change'] * 0.02 +  # Regional changes
                    score['gradient_change'] * 0.05  # Edge changes
                )
                
                motion_scores.append(score)
                prev_signature = signature
            else:
                prev_signature = self.compute_frame_signature(gray_small)
            
            prev_gray = gray_small
            frame_idx += 1
            
            if frame_idx % 100 == 0:
                print(f"  Analyzed {frame_idx}/{self.total_frames} frames...")
        
        # Find cuts based on peaks in cut score
        if motion_scores:
            cut_scores = [s['cut_score'] for s in motion_scores]
            mean_score = np.mean(cut_scores)
            std_score = np.std(cut_scores)
            threshold = mean_score + threshold_multiplier * std_score
            
            if self.debug:
                print(f"\nCut detection stats:")
                print(f"  Mean score: {mean_score:.3f}")
                print(f"  Std score: {std_score:.3f}")
                print(f"  Threshold: {threshold:.3f}")
            
            # Find peaks above threshold
            for i in range(1, len(motion_scores) - 1):
                score = motion_scores[i]['cut_score']
                if score > threshold:
                    # Local maximum check
                    if (score > motion_scores[i-1]['cut_score'] and 
                        score > motion_scores[i+1]['cut_score']):
                        
                        # Minimum distance from previous cut
                        if not cuts or motion_scores[i]['frame'] - cuts[-1] > self.fps * 0.5:
                            cuts.append(motion_scores[i]['frame'])
                            
                            if self.debug:
                                print(f"  Cut at frame {motion_scores[i]['frame']} "
                                      f"(t={motion_scores[i]['frame']/self.fps:.2f}s), "
                                      f"score={score:.3f}")
        
        # Always include frame 0
        cuts = [0] + cuts
        
        print(f"✅ Found {len(cuts)} scenes")
        return cuts
    
    def export_results(self, cuts: List[int], output_path: str):
        """Export results in same format as other detector"""
        scenes = []
        for i in range(len(cuts)):
            start = cuts[i]
            end = cuts[i + 1] if i + 1 < len(cuts) else self.total_frames
            
            scenes.append({
                'index': i,
                'start_frame': start,
                'end_frame': end,
                'duration_frames': end - start,
                'duration_sec': (end - start) / self.fps,
                'start_time': start / self.fps,
                'end_time': end / self.fps
            })
        
        results = {
            'video_info': {
                'path': self.video_path,
                'width': self.width,
                'height': self.height,
                'fps': self.fps,
                'total_frames': self.total_frames,
                'duration_sec': self.total_frames / self.fps
            },
            'transitions': cuts,
            'scenes': scenes,
            'summary': {
                'num_scenes': len(scenes),
                'avg_scene_duration': np.mean([s['duration_sec'] for s in scenes]) if scenes else 0
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to: {output_path}")
    
    def close(self):
        self.cap.release()


def main():
    parser = argparse.ArgumentParser(description='Detect scene cuts using grayscale motion analysis')
    parser.add_argument('video_path', help='Path to video file')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--threshold', '-t', type=float, default=3.0,
                       help='Cut detection threshold multiplier (default: 3.0)')
    parser.add_argument('--debug', '-d', action='store_true',
                       help='Enable debug output')
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        video_name = Path(args.video_path).stem
        output_path = f"{video_name}_motion_cuts.json"
    
    # Detect cuts
    detector = MotionCutDetector(args.video_path, debug=args.debug)
    
    try:
        cuts = detector.detect_cuts(args.threshold)
        detector.export_results(cuts, output_path)
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 SUMMARY")
        print("=" * 50)
        print(f"Total scenes: {len(cuts)}")
        
        if len(cuts) > 1:
            print(f"\nScene transitions at:")
            for i, cut in enumerate(cuts[1:], 1):  # Skip frame 0
                print(f"  {i}. Frame {cut} (t={cut/detector.fps:.2f}s)")
        
    finally:
        detector.close()
    
    print(f"\n✨ Analysis complete!")


if __name__ == "__main__":
    main()