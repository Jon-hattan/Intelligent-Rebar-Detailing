import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from collections import defaultdict



def rectangle_subtraction(bounding_boxes, void_boxes, min_width, min_height, min_area, direction = "horizontal"):

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
    if direction == "horizontal":
        for poly in remaining_polys:
            resulting_rectangles.extend(vertical_band_decomposition(poly))
        merged_rectangles = merge_vertical_rectangles(resulting_rectangles)
        
        #split boxes
        bounding_lines = generate_split_lines(merged_rectangles, void_boxes, direction = "horizontal")
        void_lines = generate_split_lines(void_boxes, void_boxes, direction="horizontal")
        split_lines_horizontal = void_lines + bounding_lines
        split_lines_horizontal = merge_similar_lines(split_lines_horizontal)
        merged_rectangles = split_boxes_by_lines(merged_rectangles, split_lines_horizontal, direction="horizontal")

    elif direction == "vertical":
        for poly in remaining_polys:
            resulting_rectangles.extend(horizontal_band_decomposition(poly))
        merged_rectangles = merge_horizontal_rectangles(resulting_rectangles)

        #split boxes
        bounding_lines = generate_split_lines(merged_rectangles, void_boxes, direction = "vertical")
        void_lines = generate_split_lines(void_boxes, void_boxes, direction="vertical")
        split_lines_vertical = void_lines + bounding_lines
        split_lines_vertical = merge_similar_lines(split_lines_vertical)
        merged_rectangles = split_boxes_by_lines(merged_rectangles, split_lines_vertical, direction="vertical")


    
    
    #Filter out small rectangles
    filtered_boxes = [
        rect for rect in merged_rectangles
        if (rect[2] - rect[0]) >= min_width and (rect[3] - rect[1]) >= min_height and (rect[2] - rect[0])*(rect[3] - rect[1]) >= min_area
    ]

    

    print(f"Merged, filtered and resplit rectangles. Found {len(filtered_boxes)}")

    

    # # Visualization
    # fig, ax = plt.subplots()
    # for rect in bounding_boxes:
    #     ax.add_patch(Rectangle((rect[0], rect[1]), rect[2]-rect[0], rect[3]-rect[1],
    #                         edgecolor='green', facecolor='none', linewidth=2))
    # for rect in void_boxes:
    #     ax.add_patch(Rectangle((rect[0], rect[1]), rect[2]-rect[0], rect[3]-rect[1],
    #                         edgecolor='red', facecolor='red', alpha=0.5))
    # for i, rect in enumerate(filtered_boxes):
    #     x1, y1, x2, y2 = rect
    #     ax.add_patch(Rectangle((x1, y1), x2-x1, y2-y1,
    #                         edgecolor='blue', facecolor='blue', alpha=0.3))
    #     ax.text(x1, y1, f'F{i}', color='white', fontsize=10, verticalalignment='top')

    # ax.set_xlim(0, 15000)
    # ax.set_ylim(0, 15000)
    # ax.set_aspect('equal')
    # plt.title("Decomposition of Outer Rectangles after Subtracting Overlapping Inner Rectangle")
    # plt.gca().invert_yaxis()  
    # plt.show()


    return filtered_boxes


    # Output the resulting rectangles
    # print("Decomposed and Merged Rectangles:")
    # for rect in merged_rectangles:
    #     print(rect)


def rectangle_subtraction2(bounding_boxes, void_boxes, min_width, min_height, min_area, direction = "horizontal"):

    print("\nUndergoing rectangle subtraction...")

    # Apply decomposition and merging
    decomposed = []
    if direction == "horizontal":
        for enclosure in bounding_boxes:
            decomposed.extend(subtract_bounding_boxes_horizontal(enclosure, void_boxes))
        merged_rectangles = merge_vertical_rectangles(decomposed)
        


    elif direction == "vertical":
        for enclosure in bounding_boxes:
            decomposed.extend(subtract_bounding_boxes_vertical(enclosure, void_boxes))
        merged_rectangles = merge_horizontal_rectangles(decomposed)
    
    
    #Filter out small rectangles
    filtered_boxes = [
        rect for rect in merged_rectangles
        if (rect[2] - rect[0]) >= min_width and (rect[3] - rect[1]) >= min_height and (rect[2] - rect[0])*(rect[3] - rect[1]) >= min_area
    ]

    

    print(f"Merged, filtered and resplit rectangles. Found {len(filtered_boxes)}")

    return filtered_boxes


def subtract_bounding_boxes_horizontal(enclosure, bounding_boxes):
    x1, y1, x2, y2 = enclosure
    # Collect all unique y-coordinates from white boxes and black box
    y_coords = {y1, y2}
    for wx1, wy1, wx2, wy2 in bounding_boxes:
        y_coords.update([wy1, wy2])
    y_levels = sorted(y_coords)

    result_rects = []

    # Process each horizontal strip
    for i in range(len(y_levels) - 1):
        y_start = y_levels[i]
        y_end = y_levels[i + 1]
        # Start with the full horizontal span
        spans = [(x1, x2)]

        # Subtract white boxes that intersect this horizontal strip
        for wx1, wy1, wx2, wy2 in bounding_boxes:
            if wy1 <= y_start and wy2 >= y_end:
                new_spans = []
                for sx1, sx2 in spans:
                    if wx2 <= sx1 or wx1 >= sx2:
                        new_spans.append((sx1, sx2))
                    else:
                        if wx1 > sx1:
                            new_spans.append((sx1, wx1))
                        if wx2 < sx2:
                            new_spans.append((wx2, sx2))
                spans = new_spans

        # Create rectangles from remaining spans
        for sx1, sx2 in spans:
            result_rects.append((sx1, y_start, sx2, y_end))

    return result_rects


def subtract_bounding_boxes_vertical(enclosure, bounding_boxes):
    x1, y1, x2, y2 = enclosure
    # Collect all unique x-coordinates from bounding boxes and enclosure
    x_coords = {x1, x2}
    for wx1, wy1, wx2, wy2 in bounding_boxes:
        x_coords.update([wx1, wx2])
    x_levels = sorted(x_coords)

    result_rects = []

    # Process each vertical strip
    for i in range(len(x_levels) - 1):
        x_start = x_levels[i]
        x_end = x_levels[i + 1]
        # Start with the full vertical span
        spans = [(y1, y2)]

        # Subtract bounding boxes that intersect this vertical strip
        for wx1, wy1, wx2, wy2 in bounding_boxes:
            if wx1 <= x_start and wx2 >= x_end:
                new_spans = []
                for sy1, sy2 in spans:
                    if wy2 <= sy1 or wy1 >= sy2:
                        new_spans.append((sy1, sy2))
                    else:
                        if wy1 > sy1:
                            new_spans.append((sy1, wy1))
                        if wy2 < sy2:
                            new_spans.append((wy2, sy2))
                spans = new_spans

        # Create rectangles from remaining spans
        for sy1, sy2 in spans:
            result_rects.append((x_start, sy1, x_end, sy2))

    return result_rects



def rectangle_subtraction_beams(enclosing_box, bounding_boxes, min_width, min_height, min_area, direction = "horizontal"):

    print("\nUndergoing rectangle subtraction for beams...")

    # Apply decomposition and merging
    if direction == "horizontal":
        decomposed = subtract_bounding_boxes_horizontal(enclosing_box, bounding_boxes)
        merged_rectangles = merge_vertical_rectangles(decomposed)
        
    elif direction == "vertical":

         #split boxes
        decomposed = subtract_bounding_boxes_vertical(enclosing_box, bounding_boxes)
        merged_rectangles = merge_horizontal_rectangles(decomposed)

    
    
    #Filter out small rectangles
    filtered_boxes = [
        rect for rect in merged_rectangles
        if (rect[2] - rect[0]) >= min_width and (rect[3] - rect[1]) >= min_height and (rect[2] - rect[0])*(rect[3] - rect[1]) >= min_area
    ]

    

    print(f"Merged, filtered and resplit rectangles. Found {len(filtered_boxes)}")

    

    # # Visualization
    # fig, ax = plt.subplots()

    # for i, rect in enumerate(filtered_boxes):
    #     x1, y1, x2, y2 = rect
    #     ax.add_patch(Rectangle((x1, y1), x2-x1, y2-y1,
    #                         edgecolor='blue', facecolor='blue', alpha=0.3))
    #     ax.text(x1, y1, f'F{i}', color='white', fontsize=10, verticalalignment='top')

    # ax.set_xlim(0, 15000)
    # ax.set_ylim(0, 15000)
    # ax.set_aspect('equal')
    # plt.title("Decomposition of Outer Rectangles after Subtracting Overlapping Inner Rectangle")
    # plt.gca().invert_yaxis()  
    # plt.show()


    return filtered_boxes



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



def horizontal_band_decomposition(poly):
    rectangles = []
    if poly.is_empty:
        return rectangles
    polys = [poly] if poly.geom_type == 'Polygon' else list(poly.geoms)
    for p in polys:
        minx, miny, maxx, maxy = p.bounds
        x = int(minx)
        while x < int(maxx):
            band = box(x, miny, x + 1, maxy)
            intersection = p.intersection(band)
            if intersection.is_empty:
                x += 1
                continue
            if intersection.geom_type == 'Polygon':
                rectangles.append(intersection.bounds)
            elif intersection.geom_type == 'MultiPolygon':
                for part in intersection.geoms:
                    rectangles.append(part.bounds)
            x += 1
    return rectangles


# Merge adjacent rectangles with same x1, x2 and y continuity
def merge_vertical_rectangles(rects, epsilon=10):
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

# Merge adjacent rectangles with same y1, y2 and x continuity
def merge_horizontal_rectangles(rects, epsilon=10):
    grouped = defaultdict(list)
    for x1, y1, x2, y2 in rects:
        grouped[(y1, y2)].append((x1, x2))
    merged = []
    for (y1, y2), x_ranges in grouped.items():
        x_ranges.sort()
        start_x, end_x = x_ranges[0]
        for x1, x2 in x_ranges[1:]:
            if abs(x1 - end_x) < epsilon:
                end_x = x2
            else:
                merged.append((start_x, y1, end_x, y2))
                start_x, end_x = x1, x2
        merged.append((start_x, y1, end_x, y2))
    return merged


def split_boxes_by_lines(boxes, lines, direction):
    result = []
    if direction == "horizontal":
        for box in boxes:
            x_min, y_min, x_max, y_max = box
            splits = [y_min, y_max]
            for y, x_start, x_end in lines:
                if y_min < y < y_max and x_start < x_max and x_end > x_min:
                    splits.append(y)
            splits = sorted(set(splits))
            for i in range(len(splits) - 1):
                result.append((x_min, splits[i], x_max, splits[i+1]))
            
    if direction == "vertical":
        for box in boxes:
            x_min, y_min, x_max, y_max = box
            splits = [x_min, x_max]
            for x, y_start, y_end in lines:
                if x_min < x < x_max and y_start < y_max and y_end > y_min:
                    splits.append(x)
            splits = sorted(set(splits))
            for i in range(len(splits) - 1):
                result.append((splits[i], y_min, splits[i+1], y_max))

        
    return result


# Define a function to generate split lines from void boxes
def generate_split_lines(boxes, void_boxes, direction):
    split_lines = []

    if direction == "horizontal":
        for box in boxes:
            x_min, y_min, x_max, y_max = box

            for y in [y_min, y_max]:  # top and bottom edges
                # Extend left
                x_left = x_min
                blocking = [b for b in void_boxes if b[1] < y < b[3] and b[2] <= x_left]
                if not blocking:
                    x_start = float('-inf')
                else:
                    x_block = max(b[2] for b in blocking)
                    x_start = min(x_block, x_left)

                # Extend right
                x_right = x_max
                blocking = [b for b in void_boxes if b[1] < y < b[3] and b[0] >= x_right]
                if not blocking:
                    x_end = float('inf')
                else:
                    x_block = min(b[0] for b in blocking)
                    x_end = max(x_block, x_right)
                

                split_lines.append((y, x_start, x_end))
    
    if direction == "vertical":
        
        for box in boxes:
            x_min, y_min, x_max, y_max = box

            for x in [x_min, x_max]:  # left and right edges
                # Extend upward
                y_top = y_min
                blocking = [b for b in void_boxes if b[0] < x < b[2] and b[1] < y_top]
                if not blocking:
                    y_start = float('-inf')
                else:
                    y_block = max(b[3] for b in blocking)
                    y_start = min(y_block, y_top)


                # Extend downward
                y_bottom = y_max
                blocking = [b for b in void_boxes if b[0] < x < b[2] and b[3] >= y_bottom]
                if not blocking:
                    y_end = float('inf')
                else:
                    y_block = min(b[1] for b in blocking)
                    y_end = max(y_bottom, y_block)

                split_lines.append((x, y_start, y_end))

    return split_lines


def merge_similar_lines(lines, threshold=20):

    lines.sort()
    merged_lines = []
    current_group = []

    for line in lines:
        key = line[0]  # y for horizontal, x for vertical
        if not current_group:
            current_group.append(line)
        else:
            last_key = current_group[-1][0]
            if abs(key - last_key) <= threshold:
                current_group.append(line)
            else:
                # Merge current group
                avg_key = sum(l[0] for l in current_group) / len(current_group)
                min_range = min(l[1] for l in current_group)
                max_range = max(l[2] for l in current_group)
                merged_lines.append((avg_key, min_range, max_range))
                current_group = [line]

    # Merge the last group
    if current_group:
        avg_key = sum(l[0] for l in current_group) / len(current_group)
        min_range = min(l[1] for l in current_group)
        max_range = max(l[2] for l in current_group)
        merged_lines.append((avg_key, min_range, max_range))

    return merged_lines


def contours_cut_vertically(contours, epsilon=10):
    # Convert contours to shapely polygons
    polygons = []
    for contour in contours:
        points = contour.reshape(-1, 2)
        if len(points) >= 3:
            poly = Polygon(points)
            if poly.is_valid:
                polygons.append(poly)

    # Perform vertical band decomposition and merge
    all_rects = []
    for poly in polygons:
        rects = vertical_band_decomposition(poly)
        all_rects.extend(rects)

    merged_rects = merge_vertical_rectangles(all_rects, epsilon=epsilon)
    return merged_rects


def visualize_cv2_contours(contours):
    import numpy as np
    # Create a blank figure
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    
    # Plot each contour
    for i, contour in enumerate(contours):
        # Reshape and extract x, y coordinates
        points = contour.reshape(-1, 2)
        color = 'red' if i % 2 == 0 else 'green'
        polygon = plt.Polygon(points, fill=None, edgecolor=color, linewidth=1.5)
        ax.add_patch(polygon)
    
    # Set limits and invert Y-axis to match image coordinates
    all_points = np.vstack([c.reshape(-1, 2) for c in contours])
    ax.set_xlim(all_points[:, 0].min() - 10, all_points[:, 0].max() + 10)
    ax.set_ylim(all_points[:, 1].max() + 10, all_points[:, 1].min() - 10)
    ax.invert_yaxis()
    
    plt.title("Visualization of OpenCV Contours")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.grid(True)
    plt.show()



def contours_cut_horizontally(contours, epsilon=10):

    # visualize_cv2_contours(contours)
    # Convert contours to shapely polygons
    polygons = []
    for contour in contours:
        points = contour.reshape(-1, 2)
        if len(points) >= 3:
            poly = Polygon(points)
            if poly.is_valid:
                polygons.append(poly)

    # Perform vertical band decomposition and merge
    all_rects = []
    for poly in polygons:
        rects = vertical_band_decomposition(poly)
        all_rects.extend(rects)

    merged_rects = merge_vertical_rectangles(all_rects, epsilon=epsilon)

    return merged_rects





#rectangle_subtraction(bounding_boxes, void_boxes)