import cv2
import numpy as np
import yaml
import os

def load_yaml_metadata(yaml_filename,params):
    metadata = {
        'resolution': params.get("DEFAULT_RESOLUTION"), 'negate': params.get("DEFAULT_NEGATE"), 'origin': params.get("DEFAULT_ORIGIN"),
        'occupied_thresh': 0.65, 'free_thresh': 0.196, 'image': None
    }
    try:
        with open(yaml_filename, 'r') as f: yaml_data = yaml.safe_load(f)
        if not yaml_data: return metadata # Empty YAML

        metadata['resolution'] = float(yaml_data.get('resolution', metadata['resolution']))
        metadata['negate'] = int(yaml_data.get('negate', metadata['negate']))
        origin_yaml = yaml_data.get('origin', metadata['origin'])
        if isinstance(origin_yaml, list) and len(origin_yaml) >= 2:
             metadata['origin'] = [float(origin_yaml[0]), float(origin_yaml[1]), float(origin_yaml[2]) if len(origin_yaml) > 2 else 0.0]
        metadata['occupied_thresh'] = float(yaml_data.get('occupied_thresh', metadata['occupied_thresh']))
        metadata['free_thresh'] = float(yaml_data.get('free_thresh', metadata['free_thresh']))
        metadata['image'] = yaml_data.get('image', metadata['image'])
        print(f"Loaded YAML: Res={metadata['resolution']}, Negate={metadata['negate']}, Origin={metadata['origin']}, Image={metadata['image']}")

        if metadata['image'] and not os.path.isabs(metadata['image']):
             yaml_dir = os.path.dirname(os.path.abspath(yaml_filename))
             metadata['image'] = os.path.join(yaml_dir, metadata['image'])
             metadata['image'] = os.path.normpath(metadata['image'])
             print(f"  Resolved Image Path: {metadata['image']}")
    except FileNotFoundError: print(f"Warning: YAML file not found: {yaml_filename}. Using defaults.")
    except Exception as e: print(f"Warning: Error loading YAML {yaml_filename}: {e}. Using defaults.")
    return metadata

def load_map(filename):
    if not filename or not os.path.exists(filename): return None
    try:
        img = cv2.imread(filename, cv2.IMREAD_UNCHANGED)
        if img is None: print(f"Error: OpenCV could not load image: {filename}"); return None
        print(f"Loaded map: {filename}, shape: {img.shape}, dtype: {img.dtype}")
        return img
    except Exception as e: print(f"Error loading map {filename}: {e}"); return None

# --- Drawing and Saving Functions ---

def draw_debug_lines(map_shape, lines, color, output_path, params, background_map=None):
    """Draws lines on a white or provided background image for debugging."""
    if background_map is None:
        debug_img = np.full((map_shape[0], map_shape[1], 3), params.get("BACKGROUND_COLOR_BGR"), dtype=np.uint8)
    else:
        if len(background_map.shape) == 2: # If grayscale background
            debug_img = cv2.cvtColor(background_map, cv2.COLOR_GRAY2BGR)
        else:
            debug_img = background_map.copy() # Assume BGR

    num_drawn = 0
    if lines is not None and len(lines) > 0:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(debug_img, (x1, y1), (x2, y2), color, 1) # Draw thin lines
            num_drawn += 1
    print(f"Drawing {num_drawn} lines for debug image {output_path}")
    try: cv2.imwrite(output_path, debug_img)
    except Exception as e: print(f"Error saving debug image {output_path}: {e}")

def draw_raster_floorplan(map_shape, wall_lines, output_path,params):
    """Draws the final raster floor plan with merged walls and saves it."""
    output_img = np.full((map_shape[0], map_shape[1], 3), params.get("BACKGROUND_COLOR_BGR"), dtype=np.uint8)
    num_drawn_walls = 0
    if wall_lines is not None and len(wall_lines) > 0:
        for line in wall_lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(output_img, (x1, y1), (x2, y2), params.get("WALL_COLOR_BGR"), params.get("WALL_THICKNESS_PX"))
            num_drawn_walls += 1
    print(f"Drawing final raster floorplan with {num_drawn_walls} wall segments.")

    try:
        cv2.imwrite(output_path, output_img)
        print(f"--- Raster floor plan saved successfully to {output_path} ---")
        return True
    except Exception as e:
        print(f"Error saving raster output image {output_path}: {e}")
        return False

def save_svg_floorplan(map_shape, wall_lines, output_path):
    """Saves the final floor plan walls as an SVG vector file."""
    print(f"Saving vector floorplan to {output_path}...")
    width, height = map_shape[1], map_shape[0] # SVG uses width, height

    try:
        with open(output_path, 'w') as f:
            # SVG Header
            f.write(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n')

            # SVG Lines for walls
            num_lines_saved = 0
            if wall_lines is not None and len(wall_lines) > 0:
                f.write('  <g stroke="{SVG_WALL_COLOR}" stroke-width="{SVG_STROKE_WIDTH}">\n')
                for line in wall_lines:
                    x1, y1, x2, y2 = line[0]
                    f.write(f'    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" />\n')
                    num_lines_saved += 1
                f.write('  </g>\n')

            # SVG Footer
            f.write('</svg>\n')
        print(f"--- Vector floor plan saved successfully with {num_lines_saved} lines to {output_path} ---")
        return True
    except Exception as e:
        print(f"Error saving SVG output file {output_path}: {e}")
        return False