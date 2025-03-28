import cv2
import numpy as np
import math

def detect_raw_lines(cleaned_binary_img, hough_min_line_length_px, hough_max_line_gap_px,params):
    if cleaned_binary_img is None: return None
    inverted_cleaned_img = cv2.bitwise_not(cleaned_binary_img)
    print("Detecting raw line segments using Hough Transform...")
    lines = cv2.HoughLinesP(inverted_cleaned_img, params.get("HOUGH_RHO"), (np.pi / 180)*params.get("HOUGH_THETA"), params.get("HOUGH_THRESHOLD"),
                            minLineLength=hough_min_line_length_px, maxLineGap=hough_max_line_gap_px)
    if lines is None: print("  Hough Transform detected no lines."); return []
    print(f"  Hough Transform detected {len(lines)} raw line segments.")
    return lines # List [[x1, y1, x2, y2], ...]

# --- Line Merging ---

def get_line_properties(line):
    """Calculate angle (degrees) and midpoint for a line segment."""
    x1, y1, x2, y2 = line[0]
    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    # Normalize angle to [0, 180)
    if angle < 0: angle += 180
    # Handle edge case where angle is exactly 180 -> set to 0
    if angle >= 179.999: angle = 0.0
    midpoint = ((x1 + x2) / 2, (y1 + y2) / 2)
    length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return angle, midpoint, length

def point_distance(p1, p2):
    """Calculate Euclidean distance between two points (x, y)."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def point_segment_distance(p, a, b):
    """Calculate the perpendicular distance from point p to line segment ab."""
    px, py = p
    ax, ay = a
    bx, by = b
    seg_len_sq = (bx - ax)**2 + (by - ay)**2
    if seg_len_sq == 0: return math.sqrt((px - ax)**2 + (py - ay)**2) # Segment is a point
    t = ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / seg_len_sq
    t = max(0, min(1, t)) # Clamp projection parameter to segment bounds
    closest_x = ax + t * (bx - ax)
    closest_y = ay + t * (by - ay)
    return math.sqrt((px - closest_x)**2 + (py - closest_y)**2)

def merge_lines(lines, angle_thresh_deg, dist_thresh_px):
    """Merges collinear and close/overlapping line segments."""
    if not len(lines): return []
    print(f"Merging {len(lines)} raw lines...")

    num_lines = len(lines)
    line_props = [get_line_properties(l) for l in lines] # (angle, midpoint, length)
    # Keep track of which lines have been merged into a group
    merged_mask = [False] * num_lines
    merged_lines_final = []

    for i in range(num_lines):
        if merged_mask[i]: continue 

        current_group_indices = [i]
        current_group_points = list(lines[i][0]) # [x1, y1, x2, y2]

        angle_i, mid_i, len_i = line_props[i]
        p1_i, p2_i = (lines[i][0][0], lines[i][0][1]), (lines[i][0][2], lines[i][0][3])

        # Check against subsequent lines
        for j in range(i + 1, num_lines):
            if merged_mask[j]: continue

            angle_j, mid_j, len_j = line_props[j]
            p1_j, p2_j = (lines[j][0][0], lines[j][0][1]), (lines[j][0][2], lines[j][0][3])

            # 1. Check angle similarity
            angle_diff = abs(angle_i - angle_j)
            angle_diff = min(angle_diff, 180 - angle_diff) # Handle wrap around 0/180
            if angle_diff < angle_thresh_deg:
                # 2. Check spatial proximity: check if endpoints are close OR if midpoints are close relative to lengths
                # Check distance between endpoints: is any endpoint of j close to any endpoint of i?
                d11 = point_distance(p1_i, p1_j)
                d12 = point_distance(p1_i, p2_j)
                d21 = point_distance(p2_i, p1_j)
                d22 = point_distance(p2_i, p2_j)
                min_endpoint_dist = min(d11, d12, d21, d22)

                # More robust check: Perpendicular distance from endpoints of j to line segment i
                dist_p1j_i = point_segment_distance(p1_j, p1_i, p2_i)
                dist_p2j_i = point_segment_distance(p2_j, p1_i, p2_i)

                # Heuristic: merge if angles are similar AND (endpoints are close OR segments are laterally close)
                if min_endpoint_dist < dist_thresh_px or (dist_p1j_i < dist_thresh_px and dist_p2j_i < dist_thresh_px) :
                    current_group_indices.append(j)
                    current_group_points.extend(lines[j][0]) # Add x1, y1, x2, y2

        # If a group was formed (more than just the initial line)
        if len(current_group_indices) > 0:
             # Mark all lines in the group as merged
            for index in current_group_indices:
                merged_mask[index] = True

            # Find the maximal extent of the merged line
            points_array = np.array(current_group_points).reshape(-1, 2) # Shape (N*2, 2)

            # --- Method 1: Farthest pair of points ---
            max_dist_sq = -1
            pt1, pt2 = points_array[0], points_array[1]
            for p_a in points_array:
                for p_b in points_array:
                    dist_sq = (p_a[0] - p_b[0])**2 + (p_a[1] - p_b[1])**2
                    if dist_sq > max_dist_sq:
                        max_dist_sq = dist_sq
                        pt1, pt2 = p_a, p_b
            merged_lines_final.append([[int(pt1[0]), int(pt1[1]), int(pt2[0]), int(pt2[1])]])

            # --- Method 2 (Alternative): Fit line with PCA, project points, find min/max projection ---
            # Requires more complex implementation, potentially more robust for noisy points
            # Placeholder: Use Method 1 for now.

    print(f"  Merged into {len(merged_lines_final)} final line segments.")
    return merged_lines_final