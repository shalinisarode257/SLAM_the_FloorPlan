import cv2
import numpy as np

def preprocess_map(img, negate,params):
    # outputs binary 0/255
    if img is None: return None
    processed_img = np.full_like(img, params.get("FREE_VAL"), dtype=np.uint8)
    pgm_occupied = params.get("OCCUPIED_PGM_VAL") if not negate else params.get("FREE_PGM_VAL")
    occupied_pixels = (img == pgm_occupied)
    processed_img[occupied_pixels] = params.get("OCCUPIED_VAL")
    print(f"Preprocessing done (negate={negate}). Output unique values: {np.unique(processed_img)}")
    return processed_img

def clean_map(binary_img,params):
    # morphological ops
    if binary_img is None: return None
    print("Applying morphological cleaning...")
    MORPH_OPEN_KERNEL_SIZE = tuple(params.get("MORPH_OPEN_KERNEL_SIZE"))
    MORPH_CLOSE_KERNEL_SIZE = tuple(params.get("MORPH_CLOSE_KERNEL_SIZE"))
    open_kernel = np.ones(MORPH_OPEN_KERNEL_SIZE, np.uint8)
    opened_img = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, open_kernel)
    close_kernel = np.ones(MORPH_CLOSE_KERNEL_SIZE, np.uint8)
    inverted_img = cv2.bitwise_not(opened_img)
    closed_inverted = cv2.morphologyEx(inverted_img, cv2.MORPH_CLOSE, close_kernel)
    cleaned_img = cv2.bitwise_not(closed_inverted)
    print(f"  Applied Opening {MORPH_OPEN_KERNEL_SIZE}, Closing {MORPH_CLOSE_KERNEL_SIZE}")
    return cleaned_img