import cv2
import numpy as np
import argparse
import yaml
import os
from utils.utils import load_yaml_metadata, load_map, draw_debug_lines, draw_raster_floorplan, save_svg_floorplan
from utils.wall_detection import detect_raw_lines, merge_lines
from utils.preprocess import preprocess_map, clean_map

# --- Parameters ---
# --- Default values (used if YAML loading fails) ---
DEFAULT_RESOLUTION = 0.01 # meters/pixel
DEFAULT_NEGATE = 0
DEFAULT_ORIGIN = [-8.98, -10.5, 0.0] # Default origin

# --- Parameters defined in METERS (converted to pixels) ---
MIN_LINE_LENGTH_METERS = 0.14  # Allow shorter segments initially for merging
MAX_LINE_GAP_METERS = 0.1     # Allow slightly larger gaps if merging works well

# --- Parameters defined in PIXELS or independent of resolution ---
# PGM Input pixel values (Typical ROS map_server values)
UNKNOWN_PGM_VAL = 205
OCCUPIED_PGM_VAL = 0
FREE_PGM_VAL = 254

# Target values AFTER preprocessing
OCCUPIED_VAL = 0    # Black for occupied
FREE_VAL = 255      # White for free

# Morphological operations
MORPH_OPEN_KERNEL_SIZE = (3, 3) # Noise removal
MORPH_CLOSE_KERNEL_SIZE = (5, 5) # Gap closing

# Hough Line Transform Parameters 
HOUGH_RHO = 0.8
HOUGH_THETA = 1
HOUGH_THRESHOLD = 30 # Lower threshold might detect more segments for merging

MERGE_ANGLE_THRESHOLD_DEG = 10.0  # Max angle difference to consider lines collinear
# Max distance between endpoints of segments to consider merging (pixels)
MERGE_DISTANCE_THRESHOLD_PX = 18

# Output drawing colors (BGR) / SVG Styles
WALL_COLOR_BGR = (255,255,255)       
BACKGROUND_COLOR_BGR = (66, 55, 20)  
WALL_THICKNESS_PX = 2
SVG_WALL_COLOR = "black"
SVG_STROKE_WIDTH = "2"

def load_config(config_file):
    """Loads configuration parameters from a YAML file."""
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            return config
    except FileNotFoundError:
        print(f"Warning: Configuration file '{config_file}' not found. Using default values.")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file '{config_file}': {e}. Using default values.")
        return {}

def parse_arguments():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Process floorplan data.")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the configuration YAML file.",
    )
    args = parser.parse_args()
    return args

def get_parameters(config_file="config.yaml"):
    """
    Loads parameters from a configuration file and command line arguments.

    Args:
        config_file (str, optional): Path to the YAML configuration file.
                                     Defaults to "config.yaml".

    Returns:
        dict: A dictionary containing the loaded parameters.
    """
    args = parse_arguments()
    config_file = args.config
    config = load_config(config_file)

    params = {
        "INPUT_YAML_FILE": config.get("INPUT_YAML_FILE", "room3.yaml"),
        "OUTPUT_RASTER_FLOORPLAN_FILE": config.get("OUTPUT_RASTER_FLOORPLAN_FILE", "floorplan_raster_room3.png"),
        "OUTPUT_VECTOR_FLOORPLAN_FILE": config.get("OUTPUT_VECTOR_FLOORPLAN_FILE", "floorplan_vector_room3.svg"),
        "OUTPUT_PREPROCESSED_FILE": config.get("OUTPUT_PREPROCESSED_FILE", "debug_preprocessed_room3.png"),
        "OUTPUT_CLEANED_FILE": config.get("OUTPUT_CLEANED_FILE", "debug_cleaned_room3.png"),
        "OUTPUT_RAW_LINES_FILE": config.get("OUTPUT_RAW_LINES_FILE", "debug_raw_lines_room3.png"),
        "OUTPUT_MERGED_LINES_FILE": config.get("OUTPUT_MERGED_LINES_FILE", "debug_merged_lines_room3.png"),
        "DEFAULT_RESOLUTION": config.get("DEFAULT_RESOLUTION", DEFAULT_RESOLUTION),
        "DEFAULT_NEGATE": config.get("DEFAULT_NEGATE", DEFAULT_NEGATE),
        "DEFAULT_ORIGIN": config.get("DEFAULT_ORIGIN", DEFAULT_ORIGIN),
        "MIN_LINE_LENGTH_METERS": config.get("MIN_LINE_LENGTH_METERS", MIN_LINE_LENGTH_METERS),
        "MAX_LINE_GAP_METERS": config.get("MAX_LINE_GAP_METERS", MAX_LINE_GAP_METERS),
        "UNKNOWN_PGM_VAL": config.get("UNKNOWN_PGM_VAL", UNKNOWN_PGM_VAL),
        "OCCUPIED_PGM_VAL": config.get("OCCUPIED_PGM_VAL", OCCUPIED_PGM_VAL),
        "FREE_PGM_VAL": config.get("FREE_PGM_VAL", FREE_PGM_VAL),
        "OCCUPIED_VAL": config.get("OCCUPIED_VAL", OCCUPIED_VAL),
        "FREE_VAL": config.get("FREE_VAL", FREE_VAL),
        "MORPH_OPEN_KERNEL_SIZE": tuple(config.get("MORPH_OPEN_KERNEL_SIZE", MORPH_OPEN_KERNEL_SIZE)),
        "MORPH_CLOSE_KERNEL_SIZE": tuple(config.get("MORPH_CLOSE_KERNEL_SIZE", MORPH_CLOSE_KERNEL_SIZE)),
        "HOUGH_RHO": config.get("HOUGH_RHO", HOUGH_RHO),
        "HOUGH_THETA": config.get("HOUGH_THETA", HOUGH_THETA),
        "HOUGH_THRESHOLD": config.get("HOUGH_THRESHOLD", HOUGH_THRESHOLD),
        "MERGE_ANGLE_THRESHOLD_DEG": config.get("MERGE_ANGLE_THRESHOLD_DEG", MERGE_ANGLE_THRESHOLD_DEG),
        "MERGE_DISTANCE_THRESHOLD_PX": config.get("MERGE_DISTANCE_THRESHOLD_PX", MERGE_DISTANCE_THRESHOLD_PX),
        "WALL_COLOR_BGR": tuple(config.get("WALL_COLOR_BGR", WALL_COLOR_BGR)),
        "BACKGROUND_COLOR_BGR": tuple(config.get("BACKGROUND_COLOR_BGR", BACKGROUND_COLOR_BGR)),
        "WALL_THICKNESS_PX": config.get("WALL_THICKNESS_PX", WALL_THICKNESS_PX),
        "SVG_WALL_COLOR": config.get("SVG_WALL_COLOR", SVG_WALL_COLOR),
        "SVG_STROKE_WIDTH": config.get("SVG_STROKE_WIDTH", SVG_STROKE_WIDTH),
    }

    if config.get("INPUT_YAML_FILE"):
        params["INPUT_YAML_FILE"] = config["INPUT_YAML_FILE"]

    return params


# --- Main ---
if __name__ == "__main__":
    
    # Get the parameters using the function
    params = get_parameters()

    # Print the loaded parameters to verify
    # print("Loaded Parameters:")
    # for key, value in params.items():
    #     print(f"  {key}: {value}")
        
    # Load YAML Metadata
    metadata = load_yaml_metadata(params.get("INPUT_YAML_FILE"),params)
    if metadata['image'] is None: exit("Error: PGM image file path not found in YAML.")
    pgm_file, resolution, negate = metadata['image'], metadata['resolution'], metadata['negate']
    if resolution <= 0: exit(f"Error: Invalid resolution ({resolution})")

    # Calculate Pixel Parameters
    hough_min_line_length_px = max(1, int(MIN_LINE_LENGTH_METERS / resolution))
    hough_max_line_gap_px = max(1, int(MAX_LINE_GAP_METERS / resolution))
    # Merge distance threshold is in pixel value
    merge_dist_thresh_px = MERGE_DISTANCE_THRESHOLD_PX
    print("Pixel parameters calculated:")
    print(f"  Hough Min Line Length: {hough_min_line_length_px} px")
    print(f"  Hough Max Line Gap: {hough_max_line_gap_px} px")
    print(f"  Line Merge Angle Thresh: {MERGE_ANGLE_THRESHOLD_DEG} deg")
    print(f"  Line Merge Distance Thresh: {merge_dist_thresh_px} px")

    print("--- Starting Floor Plan Generation Pipeline ---")
    # Load PGM Map
    print(pgm_file)
    original_map = load_map(pgm_file)
    if original_map is None: exit()
    map_shape = original_map.shape

    # Preprocess Map -> Binary (0=Occupied, 255=Free)
    binary_map = preprocess_map(original_map, negate,params)
    if binary_map is None: exit("Preprocessing failed.")

    # Clean Binary Map (Morphological Ops)
    cleaned_map = clean_map(binary_map,params)
    if cleaned_map is None: exit("Cleaning failed.")

    # Detect Raw Line Segments (Hough)
    raw_lines = detect_raw_lines(cleaned_map, hough_min_line_length_px, hough_max_line_gap_px,params)

    # Merge Collinear/Close Line Segments
    merged_wall_lines = merge_lines(raw_lines, MERGE_ANGLE_THRESHOLD_DEG, merge_dist_thresh_px)

    # Create output directory
    config_filename = os.path.splitext(os.path.basename(params.get("INPUT_YAML_FILE")))[0]
    output_dir = os.path.join("output", config_filename)
    os.makedirs(output_dir, exist_ok=True)

    # Save images with output directory
    cv2.imwrite(os.path.join(output_dir, os.path.basename(params.get("OUTPUT_PREPROCESSED_FILE"))), binary_map)
    cv2.imwrite(os.path.join(output_dir, os.path.basename(params.get("OUTPUT_CLEANED_FILE"))), cleaned_map)
    draw_debug_lines(map_shape, raw_lines, (0,0,255), os.path.join(output_dir, os.path.basename(params.get("OUTPUT_RAW_LINES_FILE"))), params, background_map=cleaned_map) # Draw raw lines in red
    draw_debug_lines(map_shape, merged_wall_lines, (0,255,0), os.path.join(output_dir, os.path.basename(params.get("OUTPUT_MERGED_LINES_FILE"))), params, background_map=cleaned_map) # Draw merged lines in green
    draw_raster_floorplan(map_shape, merged_wall_lines, os.path.join(output_dir, os.path.basename(params.get("OUTPUT_RASTER_FLOORPLAN_FILE"))),params)
    save_svg_floorplan(map_shape, merged_wall_lines, os.path.join(output_dir, os.path.basename(params.get("OUTPUT_VECTOR_FLOORPLAN_FILE"))))

    print("--- Pipeline Finished ---")