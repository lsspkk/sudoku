import cv2
import numpy as np
import pytesseract
from collections import Counter
import sys
import yaml

cell1_path = 'tests/cell_1.png'
cell4_path = 'tests/cell_4.png'

img1 = cv2.imread(cell1_path, cv2.IMREAD_GRAYSCALE)
img4 = cv2.imread(cell4_path, cv2.IMREAD_GRAYSCALE)

stats_path = 'tests/statistics.txt'
with open(stats_path, 'w') as stats:
    def bothprint(*args, **kwargs):
        print(*args, **kwargs)
        print(*args, **kwargs, file=stats)

    right_answers = {'cell_1': '1', 'cell_4': '4'}

    if img1.shape != img4.shape:
        bothprint(f"Image shapes differ: {img1.shape} vs {img4.shape}")
    else:
        diff = cv2.absdiff(img1, img4)
        bothprint(f"Pixel-by-pixel comparison:")
        bothprint(f"  Mean abs diff: {np.mean(diff):.2f}")
        bothprint(f"  Std abs diff: {np.std(diff):.2f}")
        bothprint(f"  Min diff: {np.min(diff)}")
        bothprint(f"  Max diff: {np.max(diff)}")
        bothprint(f"  Identical pixels: {np.sum(diff==0)} / {diff.size}")
        bothprint(f"  Pixels with diff > 32: {np.sum(diff>32)}")
        cv2.imwrite('tests/cell_diff.png', diff)
        bothprint("  Diff image saved as tests/cell_diff.png")

    psms = [6, 7, 8, 10, 11, 13]
    oems = [1, 3]
    thresholds = [None, 127, 180, 200]
    results = {'cell_1': [], 'cell_4': []}
    all_texts = {'cell_1': [], 'cell_4': []}
    configs_used = {'cell_1': [], 'cell_4': []}

    for cell_name, img in [('cell_1', img1), ('cell_4', img4)]:
        bothprint(f"\nOCR results for {cell_name}:")
        right = right_answers[cell_name]
        for oem in oems:
            for psm in psms:
                for thresh in thresholds:
                    if thresh is not None:
                        _, proc = cv2.threshold(img, thresh, 255, cv2.THRESH_BINARY_INV)
                    else:
                        proc = img
                    config = f'--psm {psm} --oem {oem} -c tessedit_char_whitelist=123456789'
                    text = pytesseract.image_to_string(proc, config=config).strip()
                    results[cell_name].append((config, thresh, text, psm, oem))
                    all_texts[cell_name].append(text)
                    correct = (text == right)
                    bothprint(f"  oem={oem} psm={psm} thresh={thresh}: '{text}' (expected: '{right}'){'  <==' if correct else ''}")
                    if correct:
                        configs_used[cell_name].append({'psm': psm, 'oem': oem, 'thresh': thresh})

    # For reliability, count occurrences in all_texts
    for cell_name in ['cell_1', 'cell_4']:
        bothprint(f"\nReliability for {cell_name}:")
        counts = Counter(all_texts[cell_name])
        right = right_answers[cell_name]
        for idx, (config, thresh, text, psm, oem) in enumerate(results[cell_name]):
            count = counts[text]
            if count >= 5:
                reliability = 'high'
            elif count >= 3:
                reliability = 'medium'
            elif count >= 1:
                reliability = 'low'
            else:
                reliability = 'none'
            thresh_str = str(thresh) if thresh is not None else 'None'
            correct = (text == right)
            bothprint(f"  Config: {config} thresh={thresh_str:>4} | result: '{text}' | count: {count} | reliability: {reliability} | expected: '{right}'{'  <==' if correct else ''}")

    # Summarize which settings gave which results
    bothprint("\nSummary table:")
    for idx, (config, thresh, t1, psm, oem) in enumerate(results['cell_1']):
        t4 = results['cell_4'][idx][2]
        count1 = Counter(all_texts['cell_1'])[t1]
        count4 = Counter(all_texts['cell_4'])[t4]
        rel1 = 'high' if count1 >= 5 else 'medium' if count1 >= 3 else 'low' if count1 >= 1 else 'none'
        rel4 = 'high' if count4 >= 5 else 'medium' if count4 >= 3 else 'low' if count4 >= 1 else 'none'
        thresh_str = str(thresh) if thresh is not None else 'None'
        bothprint(f"Config: {config} thresh={thresh_str:>4} | cell_1: '{t1}' ({rel1}, {count1}) | cell_4: '{t4}' ({rel4}, {count4}) | expected_1: '1' | expected_4: '4'")

    # Find most reliable settings
    cell1_counts = Counter([r[2] for r in results['cell_1']])
    cell4_counts = Counter([r[2] for r in results['cell_4']])
    bothprint("\nMost common OCR results:")
    bothprint(f"  cell_1: {cell1_counts.most_common()}")
    bothprint(f"  cell_4: {cell4_counts.most_common()}")

    # Print YAML configs for settings that produced the right answer for each cell
    def yaml_dump_configs(configs):
        # Remove duplicates
        seen = set()
        unique = []
        for c in configs:
            key = (c['psm'], c['oem'], c['thresh'])
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return yaml.dump({'tesseract_configs': unique}, sort_keys=False)

    bothprint("\nYAML configs that produced the right answer for cell_1:")
    bothprint(yaml_dump_configs(configs_used['cell_1']))
    bothprint("YAML configs that produced the right answer for cell_4:")
    bothprint(yaml_dump_configs(configs_used['cell_4'])) 