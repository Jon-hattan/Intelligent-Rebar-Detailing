
from collections import defaultdict
import numpy as np


# Helper functions

def box_bounds(box):
    if isinstance(box, np.ndarray):
        x_coords = box[:, 0]
        y_coords = box[:, 1]
    elif isinstance(box, list) and all(isinstance(pt, tuple) and len(pt) == 2 for pt in box):
        x_coords = [pt[0] for pt in box]
        y_coords = [pt[1] for pt in box]
    elif isinstance(box, tuple) and len(box) == 4:
        return box  # Already in (x1, y1, x2, y2) format
    else:
        raise ValueError(f"Unsupported box format: {box}")
    
    return min(x_coords), min(y_coords), max(x_coords), max(y_coords)


def overlaps_vertically(box1, box2, threshold=30):
    _, y1_min, _, y1_max = box_bounds(box1)
    _, y2_min, _, y2_max = box_bounds(box2)
    return abs(y1_min - y2_min) <= threshold and abs(y1_max - y2_max) <= threshold

def overlaps_horizontally(box1, box2, threshold=30):
    x1_min, y1_min, x1_max, y1_max = box_bounds(box1)
    x2_min, y2_min, x2_max, y2_max = box_bounds(box2)
    is_vertically_adjacent = abs(max(y1_min, y1_max)-min(y2_min,y2_max)) <= threshold or abs(min(y1_min, y1_max)-max(y2_min,y2_max)) <= threshold
    return abs(x1_min - x2_min) <= threshold and abs(x1_max - x2_max) <= threshold and is_vertically_adjacent

def is_void_between(box1, box2, void_boxes, direction='right', overlap_threshold=20):
    def compute_overlap(a_min, a_max, b_min, b_max):
        return max(0, min(a_max, b_max) - max(a_min, b_min))

    x1_min, y1_min, x1_max, y1_max = box_bounds(box1)
    x2_min, y2_min, x2_max, y2_max = box_bounds(box2)

    # Determine horizontal gap between boxes
    gap_left = min(x1_max, x2_max)
    gap_right = max(x1_min, x2_min)

    for vb in void_boxes:
        vx_min, vy_min, vx_max, vy_max = vb
        vx_min, vx_max = min(vx_min, vx_max), max(vx_min, vx_max)
        vy_min, vy_max = min(vy_min, vy_max), max(vy_min, vy_max)

        if direction == 'right':
            # Check if void is within horizontal gap
            if vx_min >= gap_left - overlap_threshold and vx_max <= gap_right + overlap_threshold:
                # Check vertical overlap
                vertical_overlap = compute_overlap(y1_min, y1_max, vy_min, vy_max)
                if vertical_overlap > 0:
                    return True

        elif direction == 'below':
            # Determine vertical gap between boxes
            gap_top = min(y1_max, y2_max)
            gap_bottom = max(y1_min, y2_min)

            # Check if void is within vertical gap
            if vy_min >= gap_top - overlap_threshold and vy_max <= gap_bottom + overlap_threshold:
                # Check horizontal overlap
                horizontal_overlap = compute_overlap(x1_min, x1_max, vx_min, vx_max)
                if horizontal_overlap > 0:
                    return True

    return False


def group_boxes(bounding_boxes, void_boxes, min_lone_box_size = 6000):
    
    void_boxes.sort(key=lambda vb: (vb[1], vb[0]))  # Sort by top y, then left x

    # Grouping logic
    groups = defaultdict(list)
    visited = set()
    group_id = 0

    for i, box in enumerate(bounding_boxes):
        if i in visited:
            continue
        current_group = [(i, box)]
        visited.add(i)
 

        # Check rightward boxes
        for j in range(len(bounding_boxes)):
            if j in visited:
                continue
            right_box = bounding_boxes[j]
            if overlaps_vertically(box, right_box) and not is_void_between(box, right_box, void_boxes, direction='right'):
                current_group.append((j, right_box))
                visited.add(j)
                box = right_box
            else:
                break

        # # If no horizontal grouping, check downward
        # if len(current_group) == 1:
        #     for j in range(len(bounding_boxes)):
        #         if j in visited:
        #             continue
        #         below_box = bounding_boxes[j]
        #         if overlaps_horizontally(box, below_box) and not is_void_between(box, below_box, void_boxes, direction='below'):
        #             current_group.append((j, below_box))
        #             visited.add(j)
        #             box = below_box
        #         else:
        #             break
        
        #filter out small single member groups
        if len(current_group) == 1:
            lone_box = current_group[0][1]
            x1_min, y1_min, x1_max, y1_max = box_bounds(lone_box)
            area = (x1_max - x1_min) * (y1_max - y1_min)
            if area < min_lone_box_size:
                continue

        groups[group_id] = current_group
        group_id += 1
    return groups