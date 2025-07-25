import numpy as np
from collections import defaultdict


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


def is_horizontally_aligned(box1, box2, threshold=30):
    _, y1_min, _, y1_max = box_bounds(box1)
    _, y2_min, _, y2_max = box_bounds(box2)
    return abs(y1_min - y2_min) <= threshold and abs(y1_max - y2_max) <= threshold

def is_vertically_adjacent(box1, box2, threshold=30):
    x1_min, y1_min, x1_max, y1_max = box_bounds(box1)
    x2_min, y2_min, x2_max, y2_max = box_bounds(box2)

    vertical_alignment = abs(x1_min - x2_min) <= threshold and abs(x1_max - x2_max) <= threshold
    vertical_gap = min(abs(y2_min - y1_max), abs(y1_min - y2_max))

    return vertical_alignment and vertical_gap <= threshold


def compute_overlap(a_min, a_max, b_min, b_max):
        return max(0, min(a_max, b_max) - max(a_min, b_min))

def is_void_between(box1, box2, void_boxes, direction='right', overlap_threshold=20):
    

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


def group_boxes(bounding_boxes, void_boxes, min_lone_box_size=6000):
    sorted_boxes = sorted(enumerate(bounding_boxes), key=lambda x: box_bounds(x[1])[0])
    visited = set()
    groups = {}
    group_id = 0

    for i, box in sorted_boxes:
        if i in visited:
            continue
        current_group = [(i, box)]
        visited.add(i)
        current_box = box

        for j, candidate_box in sorted_boxes:
            if j in visited or j == i:
                continue

            # Check horizontal alignment and no void
            if is_horizontally_aligned(current_box, candidate_box) and not is_void_between(current_box, candidate_box, void_boxes, direction='right'):
                # Check for intervening boxes
                x1, y1, x2, y2 = box_bounds(current_box)
                cx1, cy1, cx2, cy2 = box_bounds(candidate_box)
                left, right = min(x2, cx2), max(x1, cx1)

                has_intervening_box = False
                for k, other_box in sorted_boxes:
                    if k in visited or k == i or k == j:
                        continue
                    ox1, oy1, ox2, oy2 = box_bounds(other_box)
                    if left <= ox1 <= right and compute_overlap(oy1, oy2, cy1, cy2) > 0 and compute_overlap(y1, y2, oy1, oy2) > 0:
                        has_intervening_box = True
                        break

                if not has_intervening_box:
                    current_group.append((j, candidate_box))
                    visited.add(j)
                    current_box = candidate_box
                else:
                    break  # Stop grouping if blocked by another box
            else:
                break

        # Filter out small lone boxes
        if len(current_group) == 1:
            x1, y1, x2, y2 = box_bounds(current_group[0][1])
            area = (x2 - x1) * (y2 - y1)
            if area < min_lone_box_size:
                continue

        groups[group_id] = current_group
        group_id += 1

    return groups


