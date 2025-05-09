import os
import cv2
import numpy as np
from glob import glob
import argparse
import time

THRESH = int(0.8 * 255)  # 80% gray

timing_info = {'start_time': None, 'file_times': [], 'total_files': 0}

def format_hms(seconds):
    seconds = int(round(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def calculate_timing(idx, total_files, file_time):
    global timing_info
    if timing_info['start_time'] is None:
        timing_info['start_time'] = time.time()
    timing_info['file_times'].append(file_time)
    timing_info['total_files'] = total_files
    elapsed = time.time() - timing_info['start_time']
    mean_time = sum(timing_info['file_times']) / len(timing_info['file_times']) if timing_info['file_times'] else 0
    files_left = total_files - (idx + 1)
    est_time_left = files_left * mean_time
    return {
        'current_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'elapsed': elapsed,
        'mean_time': mean_time,
        'files_left': files_left,
        'est_time_left': est_time_left,
        'current_idx': idx + 1,
        'total_files': total_files
    }

def log_timing(timing):
    log_line = (f"File {timing['current_idx']}/{timing['total_files']} | "
                f"Timing {timing['current_time']} | Elapsed: {format_hms(timing['elapsed'])} | "
                f"Mean/file: {timing['mean_time']:.1f}s | Files left: {timing['files_left']} | "
                f"Est. time left: {format_hms(timing['est_time_left'])}")
    print(log_line)

def whiten_folder(png_dir):
    png_files = sorted(glob(os.path.join(png_dir, '*.png')))
    total_files = len(png_files)
    global timing_info
    timing_info['start_time'] = time.time()
    timing_info['file_times'] = []
    timing_info['total_files'] = total_files

    for idx, fname in enumerate(png_files):
        file_start = time.time()
        img = cv2.imread(fname)
        if img is None:
            print(f"Could not read {fname}")
            continue
        # Create mask for 'almost white' pixels (all channels >= THRESH)
        mask = np.all(img >= THRESH, axis=2)
        n_whitened = np.sum(mask)
        img[mask] = [255, 255, 255]
        cv2.imwrite(fname, img)
        print(f"[{idx+1}/{total_files}] {fname}: whitened {n_whitened} pixels")
        file_time = time.time() - file_start
        timing = calculate_timing(idx, total_files, file_time)
        log_timing(timing)

    # Print summary at the end
    total_elapsed = time.time() - timing_info['start_time']
    print(f"\nAll done! Total elapsed time: {format_hms(total_elapsed)}")

def main():
    parser = argparse.ArgumentParser(description='Whiten nearly-white pixels in all PNGs in a folder')
    parser.add_argument('input', help='PNG folder to process (required)')
    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print(f"Input {args.input} is not a valid directory.")
        return

    whiten_folder(args.input)

if __name__ == '__main__':
    main() 