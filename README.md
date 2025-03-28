# Floorplan Generation from SLAM outputs

This project generates vector (SVG) and raster (PNG) floorplans from the SLAM outputs in PGM (Portable Graymap) format, typically used in robotics and mapping applications. It first processes the maps, cleans any noise, detects walls using Hough Line Transform, merges collinear lines, and outputs the result.

## Features

* **PGM Input:** Reads PGM map files.
* **YAML Configuration:** Uses a YAML file (`config.yaml`) to manage parameters, making it easy to adjust processing settings.
* **Preprocessing:** Performs image preprocessing, including binarization and morphological operations, to clean the input map.
* **Hough Line Detection:** Detects line segments representing walls using the Hough Line Transform.
* **Line Merging:** Merges collinear and close line segments for a cleaner floorplan representation.
* **Raster (PNG) Output:** Generates a PNG image of the floorplan.
* **Vector (SVG) Output:** Creates an SVG vector graphic of the floorplan.
* **Debug Outputs:** Provides debug images to visualize intermediate steps (preprocessed, cleaned, raw lines, merged lines).

## Requirements

* Python 3.x
* OpenCV (`cv2`)
* NumPy
* PyYAML

Install the required packages using pip:

```bash
pip install opencv-python numpy pyyaml
```

## Usage

1. **Prepare your PGM map:** Place your PGM map file in a location accessible to the script.
2. **Create a config.yaml file:** Create a `config.yaml` file. See the example `config.yaml` below for the available parameters.
3. **Run the script:** Execute the Python script from your terminal:

```bash
python main.py
```

To use a custom configuration file:

```bash
python main.py --config my_custom_config.yaml
```

4. **View the output:** The generated PNG and SVG floorplans, along with any debug images, will be saved in a new directory inside the `output/` folder, named after the input yaml file.

## config.yaml Example

```yaml
INPUT_YAML_FILE: "metadata/room3.yaml" # Path to your YAML file containing PGM path and metadata
OUTPUT_RASTER_FLOORPLAN_FILE: "floorplan_raster_room3.png"
OUTPUT_VECTOR_FLOORPLAN_FILE: "floorplan_vector_room3.svg"
OUTPUT_PREPROCESSED_FILE: "debug_preprocessed_room3.png"
OUTPUT_CLEANED_FILE: "debug_cleaned_room3.png"
OUTPUT_RAW_LINES_FILE: "debug_raw_lines_room3.png"
OUTPUT_MERGED_LINES_FILE: "debug_merged_lines_room3.png"
DEFAULT_RESOLUTION: 0.01 # meters/pixel
DEFAULT_NEGATE: 0
DEFAULT_ORIGIN: [-8.98, -10.5, 0.0]
MIN_LINE_LENGTH_METERS: 0.15
MAX_LINE_GAP_METERS: 0.1
UNKNOWN_PGM_VAL: 205
OCCUPIED_PGM_VAL: 0
FREE_PGM_VAL: 254
OCCUPIED_VAL: 0
FREE_VAL: 255
MORPH_OPEN_KERNEL_SIZE: [3, 3]
MORPH_CLOSE_KERNEL_SIZE: [5, 5]
HOUGH_RHO: 1
HOUGH_THETA: 3.14159265 / 180 # pi/180
HOUGH_THRESHOLD: 30
MERGE_ANGLE_THRESHOLD_DEG: 5.0
MERGE_DISTANCE_THRESHOLD_PX: 15
WALL_COLOR_BGR: [255, 255, 255]
BACKGROUND_COLOR_BGR: [66, 55, 20]
WALL_THICKNESS_PX: 2
SVG_WALL_COLOR: "black"
SVG_STROKE_WIDTH: "2"
```

## Parameters Explained

### File Paths:
- `INPUT_YAML_FILE`: Path to the YAML file containing the PGM file path and metadata.
- `OUTPUT_RASTER_FLOORPLAN_FILE`: Path for the output PNG floorplan.
- `OUTPUT_VECTOR_FLOORPLAN_FILE`: Path for the output SVG floorplan.
- `OUTPUT_PREPROCESSED_FILE`, `OUTPUT_CLEANED_FILE`, `OUTPUT_RAW_LINES_FILE`, `OUTPUT_MERGED_LINES_FILE`: Paths for optional debug images.

### PGM Metadata:
- `DEFAULT_RESOLUTION`: Resolution of the PGM map (meters per pixel).
- `DEFAULT_NEGATE`: Negation flag (0 or 1).
- `DEFAULT_ORIGIN`: Origin of the map in meters.

### Processing Parameters:
- `MIN_LINE_LENGTH_METERS`, `MAX_LINE_GAP_METERS`: Parameters for Hough Line Transform (in meters).
- `UNKNOWN_PGM_VAL`, `OCCUPIED_PGM_VAL`, `FREE_PGM_VAL`: Pixel values in the input PGM.
- `OCCUPIED_VAL`, `FREE_VAL`: Target pixel values after preprocessing.
- `MORPH_OPEN_KERNEL_SIZE`, `MORPH_CLOSE_KERNEL_SIZE`: Kernel sizes for morphological operations.
- `HOUGH_RHO`, `HOUGH_THETA`, `HOUGH_THRESHOLD`: Parameters for Hough Line Transform.
- `MERGE_ANGLE_THRESHOLD_DEG`, `MERGE_DISTANCE_THRESHOLD_PX`: Parameters for line merging.

### Output Styling:
- `WALL_COLOR_BGR`, `BACKGROUND_COLOR_BGR`, `WALL_THICKNESS_PX`: Styling for the raster output.
- `SVG_WALL_COLOR`, `SVG_STROKE_WIDTH`: Styling for the vector output.


## License

This project is licensed under the Apache 2.0 License.

