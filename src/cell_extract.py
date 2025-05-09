import cv2
import numpy as np
import pytesseract
from collections import Counter
import yaml
import threading

DEBUG = False

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def preprocess_cell(cell_img):
    gray = cv2.cvtColor(cell_img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    gray = cv2.resize(gray, (64, 64), interpolation=cv2.INTER_LINEAR)
    return gray

def load_ocr_configs(yaml_path='src/ocr_config.yaml'):
    if not hasattr(load_ocr_configs, "_cache"):
        load_ocr_configs._cache = {}
        load_ocr_configs._lock = threading.Lock()
    with load_ocr_configs._lock:
        if yaml_path in load_ocr_configs._cache:
            return load_ocr_configs._cache[yaml_path]
        with open(yaml_path, 'r') as f:
            cfg = yaml.safe_load(f)
        configs = []
        for c in cfg['tesseract_configs']:
            psm = c['psm']
            oem = c['oem']
            thresh = c.get('thresh', None)
            configs.append({'psm': psm, 'oem': oem, 'thresh': thresh})
        load_ocr_configs._cache[yaml_path] = configs
        return configs

def template_match_cell(cell_img, templates):
    best_digit, best_score = None, -1
    for digit, tmpl in (templates or {}).items():
        cell_resized = cv2.resize(cell_img, tmpl.shape[::-1], interpolation=cv2.INTER_LINEAR)
        res = cv2.matchTemplate(cell_resized, tmpl, cv2.TM_CCOEFF_NORMED)
        score = res.max()
        if score > best_score:
            best_score = score
            best_digit = digit
    if best_score > 0.4:
        return best_digit, True
    return None, False

def extract_and_recognize_cell(image, x, y, w, h, templates=None):
    cell_img = image[y:y+h, x:x+w]
    gray = preprocess_cell(cell_img)
    debug_print(f"[DEBUG] Processing cell at ({x},{y},{w},{h}), gray shape: {gray.shape}, min: {gray.min()}, max: {gray.max()}, mean: {gray.mean():.2f}")
    if not np.any(gray == 0):
        debug_print("[DEBUG] No black pixels found in cell, returning '-' (empty)")
        return '-', 'none', 0
    ocr_configs = load_ocr_configs()
    debug_print(f"[DEBUG] Using {len(ocr_configs)} OCR configs from YAML")
    ocr_results = []
    for cfg in ocr_configs:
        psm = cfg['psm']
        oem = cfg['oem']
        thresh = cfg.get('thresh', None)
        if thresh is not None:
            _, proc = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY_INV)
        else:
            proc = gray
        config_str = f'--psm {psm} --oem {oem} -c tessedit_char_whitelist=123456789'
        text = pytesseract.image_to_string(proc, config=config_str).strip()
        debug_print(f"[DEBUG] OCR result for config (psm={psm}, oem={oem}, thresh={thresh}): '{text}'")
        if text.isdigit() and len(text) == 1:
            ocr_results.append(text)
            # Check for high reliability immediately
            most_common, count = Counter(ocr_results).most_common(1)[0]
            if count >= 5:
                debug_print(f"[DEBUG] Early exit: Decided value: {most_common}, reliability: high, count: {count}")
                return most_common, 'high', count
    debug_print(f"[DEBUG] OCR results collected: {ocr_results}")
    if ocr_results:
        most_common, count = Counter(ocr_results).most_common(1)[0]
        if count >= 5:
            reliability = 'high'
        elif count >= 3:
            reliability = 'medium'
        else:
            reliability = 'low'
        if count >= 3 or count > len(ocr_results) // 2:
            debug_print(f"[DEBUG] Decided value: {most_common}, reliability: {reliability}, count: {count}")
            return most_common, reliability, count
    tmpl_digit, tmpl_ok = template_match_cell(gray, templates) if templates else (None, False)
    if tmpl_ok:
        debug_print(f"[DEBUG] Template match fallback: {tmpl_digit}")
        return tmpl_digit, 'template', 0
    else:
        debug_print("[DEBUG] No digit recognized, returning '-' (none)")
        return '-', 'none', 0 