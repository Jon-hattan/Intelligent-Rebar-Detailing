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



def compute_overlap(a_min, a_max, b_min, b_max):
        return max(0, min(a_max, b_max) - max(a_min, b_min))

def is_horizontally_aligned(box1, box2, threshold=30): #two boxes are aligned approximately horizontally
    _, y1_min, _, y1_max = box_bounds(box1)
    _, y2_min, _, y2_max = box_bounds(box2)
    return abs(y1_min - y2_min) <= threshold and abs(y1_max - y2_max) <= threshold

def is_vertically_aligned(box1, box2, threshold=30): #two boxes are aligned approximately vertically
    x1_min, _, x1_max, _ = box_bounds(box1)
    x2_min, _, x2_max, _ = box_bounds(box2)
    return abs(x1_min - x2_min) <= threshold and abs(x1_max - x2_max) <= threshold
    
def check_void_between_horizontal(current_box, next_box, void_boxes): #ASSUME THAT VOID BOXES ARE ALREADY SORTED BY MIN X 
    curr_x1 = current_box[0]
    next_x2 = next_box[2]

    for void_box in void_boxes:
        void_x1, void_y1, void_x2, void_y2 = void_box

        # Skip void boxes that start before current box ends
        if void_x1 < curr_x1:
            continue
        # If void box ends after next box starts, it's not between
        if void_x2 > next_x2:
            continue

        # Check vertical overlap with current_box
        curr_y1, curr_y2 = min(current_box[1], current_box[3]), max(current_box[1], current_box[3])
        void_y_min, void_y_max = min(void_y1, void_y2), max(void_y1, void_y2)
        overlap_curr = compute_overlap(void_y_min, void_y_max, curr_y1, curr_y2)

        # Check vertical overlap with next_box
        next_y1, next_y2 = min(next_box[1], next_box[3]), max(next_box[1], next_box[3])
        overlap_next = compute_overlap(void_y_min, void_y_max, next_y1, next_y2)

        if overlap_curr > 0 and overlap_next > 0:
            return True

    return False


def check_void_between_vertical(current_box, next_box, void_boxes):
    curr_y1 = current_box[1]
    next_y2 = next_box[3]

    for void_box in void_boxes:
        void_x1, void_y1, void_x2, void_y2 = void_box

        # Skip void boxes that start before current box ends
        if void_y1 < curr_y1:
            continue
        # If void box ends after next box starts, it's not between
        if void_y2 > next_y2:
            continue

        # Check vertical overlap with current_box
        curr_x1, curr_x2 = min(current_box[0], current_box[2]), max(current_box[0], current_box[2])
        void_x_min, void_x_max = min(void_x1, void_x2), max(void_x1, void_x2)
        overlap_curr = compute_overlap(void_x_min, void_x_max, curr_x1, curr_x2)

        # Check vertical overlap with next_box
        next_x1, next_x2 = min(next_box[0], next_box[2]), max(next_box[0], next_box[2])
        overlap_next = compute_overlap(void_x_min, void_x_max, next_x1, next_x2)

        if overlap_curr > 0 and overlap_next > 0:
            return True

    return False


def is_vertically_adjacent(box1, box2, threshold=30):
    x1_min, y1_min, x1_max, y1_max = box_bounds(box1)
    x2_min, y2_min, x2_max, y2_max = box_bounds(box2)

    vertical_alignment = abs(x1_min - x2_min) <= threshold and abs(x1_max - x2_max) <= threshold
    vertical_gap = min(abs(y2_min - y1_max), abs(y1_min - y2_max))

    return vertical_alignment and vertical_gap <= threshold

def is_horizontally_adjacent(box1, box2, threshold=30):
    # Ensure proper min/max ordering
    x1_min, x1_max = min(box1[0], box1[2]), max(box1[0], box1[2])
    y1_min, y1_max = min(box1[1], box1[3]), max(box1[1], box1[3])
    
    x2_min, x2_max = min(box2[0], box2[2]), max(box2[0], box2[2])
    y2_min, y2_max = min(box2[1], box2[3]), max(box2[1], box2[3])

    horizontal_alignment = abs(y1_min - y2_min) <= threshold and abs(y1_max - y2_max) <= threshold
    horizontal_gap = min(abs(x2_min - x1_max), abs(x1_min - x2_max))

    return horizontal_alignment and horizontal_gap <= threshold



def group_boxes_horizontal(boxes, void_boxes, min_lone_box_size=4000):
    # Sort boxes by their leftmost x value
    boxes = sorted(boxes, key=lambda b: b[0])
    grouped = defaultdict(list)
    used = set()

    def box_bounds(box):
        x1, y1, x2, y2 = box
        return min(x1,x2), min(y1, y2), max(x1,x2), max(y1, y2)
    
    group_id = 0

    for i, box in enumerate(boxes):
        if i in used:
            continue

        group = [(i,box)]
        used.add(i)
        current_box = box

        for j in range(i + 1, len(boxes)):
            if j in used:
                continue

            next_box = boxes[j]
            x_next1, _, x_next2, _ = box_bounds(next_box)
            x_curr2 = box_bounds(current_box)[2]

            if x_next1 < x_curr2:
                continue

            y1_min, y1_max = box_bounds(current_box)[1], box_bounds(current_box)[3]
            y2_min, y2_max = box_bounds(next_box)[1], box_bounds(next_box)[3]

            if compute_overlap(y1_min, y1_max, y2_min, y2_max) == 0:
                continue

            if not is_horizontally_aligned(current_box, next_box):
                break

            # Placeholder for void check
            if check_void_between_horizontal(current_box, next_box, void_boxes):
                break

            group.append((j, next_box))
            used.add(j)
            current_box = next_box

        #filter out small single member groups
        if len(group) == 1:
            lone_box = group[0][1]
            x1_min, y1_min, x1_max, y1_max = box_bounds(lone_box)
            area = (x1_max - x1_min) * (y1_max - y1_min)
            if area < min_lone_box_size:
                continue

        grouped[group_id] = group
        group_id+=1

    return grouped


def group_boxes_vertical(boxes, void_boxes, min_lone_box_size=4000):
    # Sort boxes by their leftmost x value
    boxes = sorted(boxes, key=lambda b: b[1])
    grouped = defaultdict(list)
    used = set()

    def box_bounds(box):
        x1, y1, x2, y2 = box
        return min(x1,x2), min(y1, y2), max(x1,x2), max(y1, y2)
    
    group_id = 0

    for i, box in enumerate(boxes):
        if i in used:
            continue

        group = [(i,box)]
        used.add(i)
        current_box = box

        for j in range(i + 1, len(boxes)):
            if j in used:
                continue

            next_box = boxes[j]
            y_next1, _, y_next2, _ = box_bounds(next_box)
            y_curr2 = box_bounds(current_box)[3]

            if y_next1 < y_curr2:
                continue

            x1_min, x1_max = box_bounds(current_box)[0], box_bounds(current_box)[2]
            x2_min, x2_max = box_bounds(next_box)[0], box_bounds(next_box)[2]

            if compute_overlap(x1_min, x1_max, x2_min, x2_max) == 0:
                continue
            

            if not is_vertically_aligned(current_box, next_box):
                break

            # Placeholder for void check
            if check_void_between_vertical(current_box, next_box, void_boxes):
                break

            group.append((j, next_box))
            used.add(j)
            current_box = next_box

        #filter out small single member groups
        if len(group) == 1:
            lone_box = group[0][1]
            x1_min, y1_min, x1_max, y1_max = box_bounds(lone_box)
            area = (x1_max - x1_min) * (y1_max - y1_min)
            if area < min_lone_box_size:
                continue

        grouped[group_id] = group
        group_id+=1

    return grouped


# Helper function to compute bounding box of a group
def compute_group_bounds(group):
    x_min = min(box[0] for _, box in group)
    y_min = min(box[1] for _, box in group)
    x_max = max(box[2] for _, box in group)
    y_max = max(box[3] for _, box in group)
    return (x_min, y_min, x_max, y_max)

def merge_box_vertical(grouped): #merge the groups by vertical alignment
    group_bounds = {gid: compute_group_bounds(group) for gid, group in grouped.items()}
    merged = defaultdict(list)
    used = set()
    new_group_id = 0

    group_ids = sorted(grouped.keys(), key=lambda gid: group_bounds[gid][1])  # sort by y_min

    for i in group_ids:
        if i in used:
            continue
        merged_group = grouped[i]
        used.add(i)
        for j in group_ids:
            if j in used or i == j:
                continue
            if is_vertically_adjacent(group_bounds[i], group_bounds[j]):
                merged_group.extend(grouped[j])
                used.add(j)
        merged[new_group_id] = merged_group
        new_group_id += 1

    return merged

def merge_box_horizontal(grouped): #merge the groups by horizontal alignment
    group_bounds = {gid: compute_group_bounds(group) for gid, group in grouped.items()}
    merged = defaultdict(list)
    used = set()
    new_group_id = 0

    group_ids = sorted(grouped.keys(), key=lambda gid: group_bounds[gid][0])  # sort by x_min

    for i in group_ids:
        if i in used:
            continue
        merged_group = grouped[i]
        used.add(i)
        for j in group_ids:
            if j in used or i == j:
                continue
            if is_horizontally_adjacent(group_bounds[i], group_bounds[j]):
                merged_group.extend(grouped[j])
                used.add(j)
        merged[new_group_id] = merged_group
        new_group_id += 1

    return merged



def group_boxes(boxes, void_boxes, min_lone_box_size=4000, direction = "horizontal"):
    if direction == "horizontal":
        hor_grouped = group_boxes_horizontal(boxes, void_boxes, min_lone_box_size=4000)
        vert_merged = merge_box_vertical(hor_grouped)
        return vert_merged
    elif direction == "vertical":
        ver_grouped = group_boxes_vertical(boxes, void_boxes, min_lone_box_size=4000)
        hor_merged = merge_box_horizontal(ver_grouped)
        return hor_merged


