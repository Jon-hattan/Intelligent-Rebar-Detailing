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
    

    #Filter out small rectangles
    filtered_rectangles = [
        rect for rect in merged_rectangles
        if (rect[2] - rect[0]) >= min_width and (rect[3] - rect[1]) >= min_height
    ]

    print(f"Merged and filtered rectangles. Found {len(filtered_rectangles)}")

    

    # Visualization
    fig, ax = plt.subplots()
    for rect in bounding_boxes:
        ax.add_patch(Rectangle((rect[0], rect[1]), rect[2]-rect[0], rect[3]-rect[1],
                            edgecolor='green', facecolor='none', linewidth=2))
    for rect in void_boxes:
        ax.add_patch(Rectangle((rect[0], rect[1]), rect[2]-rect[0], rect[3]-rect[1],
                            edgecolor='red', facecolor='red', alpha=0.5))
    for rect in filtered_rectangles:
        x1, y1, x2, y2 = rect
        ax.add_patch(Rectangle((x1, y1), x2-x1, y2-y1,
                            edgecolor='blue', facecolor='blue', alpha=0.3))

    ax.set_xlim(0, 10000)
    ax.set_ylim(0, 10000)
    ax.set_aspect('equal')
    plt.title("Decomposition of Outer Rectangles after Subtracting Overlapping Inner Rectangle")
    plt.show()
    
    filtered_rectangles = [
            [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            for x1, y1, x2, y2 in filtered_rectangles
        ]


    return filtered_rectangles


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




#rectangle_subtraction(bounding_boxes, void_boxes)