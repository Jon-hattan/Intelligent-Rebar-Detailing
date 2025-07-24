import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from shapely.geometry import box
from shapely.ops import unary_union
from collections import defaultdict


def rectangle_subtraction(bounding_boxes, void_boxes, min_width, min_height):

    print("\nUndergoing rectangle subtraction...")

    # Convert to shapely boxes
    outer_polys = [box(*rect) for rect in bounding_boxes]
    inner_polys = [box(*rect) for rect in void_boxes]

    # Union of inner rectangles
    subtract_area = unary_union(inner_polys)

    # Subtract from each outer rectangle
    remaining_polys = [poly.difference(subtract_area) for poly in outer_polys]

    # Apply decomposition and merging
    resulting_rectangles = []
    for poly in remaining_polys:
        resulting_rectangles.extend(vertical_band_decomposition(poly))
    merged_rectangles = merge_vertical_rectangles(resulting_rectangles)
    
    #Split lines
    split_lines = generate_split_lines(void_boxes)
    split_lines = merge_similar_horizontal_lines(split_lines)
    split_boxes = split_boxes_by_lines(merged_rectangles, split_lines)
    
    #Filter out small rectangles
    filtered_boxes = [
        rect for rect in split_boxes
        if (rect[2] - rect[0]) >= min_width and (rect[3] - rect[1]) >= min_height
    ]

    

    print(f"Merged, filtered and resplit rectangles. Found {len(filtered_boxes)}")

    

    # Visualization
    fig, ax = plt.subplots()
    for rect in bounding_boxes:
        ax.add_patch(Rectangle((rect[0], rect[1]), rect[2]-rect[0], rect[3]-rect[1],
                            edgecolor='green', facecolor='none', linewidth=2))
    for rect in void_boxes:
        ax.add_patch(Rectangle((rect[0], rect[1]), rect[2]-rect[0], rect[3]-rect[1],
                            edgecolor='red', facecolor='red', alpha=0.5))
    for rect in filtered_boxes:
        x1, y1, x2, y2 = rect
        ax.add_patch(Rectangle((x1, y1), x2-x1, y2-y1,
                            edgecolor='blue', facecolor='blue', alpha=0.3))

    ax.set_xlim(0, 15000)
    ax.set_ylim(0, 15000)
    ax.set_aspect('equal')
    plt.title("Decomposition of Outer Rectangles after Subtracting Overlapping Inner Rectangle")
    plt.show()
    
    filtered_boxes = [
            [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            for x1, y1, x2, y2 in filtered_boxes
        ]


    return filtered_boxes


    # Output the resulting rectangles
    # print("Decomposed and Merged Rectangles:")
    # for rect in merged_rectangles:
    #     print(rect)




# Vertical band decomposition
def vertical_band_decomposition(poly):
    rectangles = []
    if poly.is_empty:
        return rectangles
    polys = [poly] if poly.geom_type == 'Polygon' else list(poly.geoms)
    for p in polys:
        minx, miny, maxx, maxy = p.bounds
        y = int(miny)
        while y < int(maxy):
            band = box(minx, y, maxx, y + 1)
            intersection = p.intersection(band)
            if intersection.is_empty:
                y += 1
                continue
            if intersection.geom_type == 'Polygon':
                rectangles.append(intersection.bounds)
            elif intersection.geom_type == 'MultiPolygon':
                for part in intersection.geoms:
                    rectangles.append(part.bounds)
            y += 1
    return rectangles

# Merge adjacent rectangles with same x1, x2 and y continuity
def merge_vertical_rectangles(rects, epsilon=10):
    from collections import defaultdict
    grouped = defaultdict(list)
    for x1, y1, x2, y2 in rects:
        grouped[(x1, x2)].append((y1, y2))
    merged = []
    for (x1, x2), y_ranges in grouped.items():
        y_ranges.sort()
        start_y, end_y = y_ranges[0]
        for y1, y2 in y_ranges[1:]:
            if abs(y1 - end_y) < epsilon:
                end_y = y2
            else:
                merged.append((x1, start_y, x2, end_y))
                start_y, end_y = y1, y2
        merged.append((x1, start_y, x2, end_y))
    return merged


def split_boxes_by_lines(boxes, lines):
    result = []
    for box in boxes:
        x_min, y_min, x_max, y_max = box
        splits = [y_min, y_max]
        for y, x_start, x_end in lines:
            if y_min < y < y_max and x_start < x_max and x_end > x_min:
                splits.append(y)
        splits = sorted(set(splits))
        for i in range(len(splits) - 1):
            result.append((x_min, splits[i], x_max, splits[i+1]))
    return result


# Define a function to generate split lines from void boxes
def generate_split_lines(void_boxes):
    split_lines = []

    for box in void_boxes:
        x_min, y_min, x_max, y_max = box

        for y in [y_min, y_max]:  # top and bottom edges
            # Extend left
            x_left = x_min
            while True:
                blocking = [b for b in void_boxes if b[1] < y < b[3] and b[2] <= x_left]
                if not blocking:
                    x_start = float('-inf')
                    break
                x_block = max(b[2] for b in blocking)
                if x_block < x_left:
                    x_start = x_block
                    break

            # Extend right
            x_right = x_max
            while True:
                blocking = [b for b in void_boxes if b[1] < y < b[3] and b[0] >= x_right]
                if not blocking:
                    x_end = float('inf')
                    break
                x_block = min(b[0] for b in blocking)
                if x_block > x_right:
                    x_end = x_block
                    break

            split_lines.append((y, x_start, x_end))

    return split_lines


def merge_similar_horizontal_lines(lines, threshold=10):
    """
    Merge horizontal lines that have similar y-values within a given threshold.
    Each line is a tuple: (y, x_start, x_end)
    Returns a list of merged lines with averaged y-values and combined x-ranges.
    """
    lines.sort()
    merged_lines = []
    current_group = []

    for line in lines:
        y, x_start, x_end = line
        if not current_group:
            current_group.append(line)
        else:
            last_y = current_group[-1][0]
            if abs(y - last_y) <= threshold:
                current_group.append(line)
            else:
                # Merge current group
                avg_y = sum(l[0] for l in current_group) / len(current_group)
                min_x = min(l[1] for l in current_group)
                max_x = max(l[2] for l in current_group)
                merged_lines.append((avg_y, min_x, max_x))
                current_group = [line]

    # Merge the last group
    if current_group:
        avg_y = sum(l[0] for l in current_group) / len(current_group)
        min_x = min(l[1] for l in current_group)
        max_x = max(l[2] for l in current_group)
        merged_lines.append((avg_y, min_x, max_x))

    return merged_lines

#rectangle_subtraction(bounding_boxes, void_boxes)