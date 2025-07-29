import numpy as np
import cv2

def get_intersection_bounding_boxes(lines):
    def segment_intersection(p1, p2, p3, p4):
    #Returns intersection point if line segments (p1, p2) and (p3, p4) intersect.
        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

        # Check if segments intersect using CCW method
        if ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4):
            # Segments intersect; find the point using line-line intersection
            def det(a, b):
                return float(a[0]) * float(b[1]) - float(a[1]) * float(b[0])

            xdiff = (p1[0] - p2[0], p3[0] - p4[0])
            ydiff = (p1[1] - p2[1], p3[1] - p4[1])

            div = det(xdiff, ydiff)
            if div == 0:
                return None  # Lines are parallel

            d = (det(p1, p2), det(p3, p4))
            x = det(d, xdiff) / div
            y = det(d, ydiff) / div
            return int(x), int(y)

        return None  # Segments don't intersect

    rectangles = []

    for i in range(len(lines)):
        for j in range(i+1, len(lines)):
            l1 = lines[i]
            l2 = lines[j]
            p1, p2 = (l1[0], l1[1]), (l1[2], l1[3])
            p3, p4 = (l2[0], l2[1]), (l2[2], l2[3])
            pt = segment_intersection(p1, p2, p3, p4)
            if pt is None:
                continue

            xs = [p1[0], p2[0], p3[0], p4[0]]
            ys = [p1[1], p2[1], p3[1], p4[1]]

            cx, cy = pt

            # Get max horizontal and vertical distance from intersection to endpoints
            half_width = max(abs(cx - x) for x in xs)
            half_height = max(abs(cy - y) for y in ys)

            # Build rectangle centered at intersection
            x1, y1 = int(cx - half_width), int(cy - half_height)
            x2, y2 = int(cx + half_width), int(cy + half_height)

            rectangles.append(((x1, y1), (x2, y2)))

    return rectangles


def merge_rectangles_with_morphology(rectangles, image, filter = True):
    """
    Merges bounding rectangles using morphological operations.
    
    :param rectangles: List of bounding boxes [(x1, y1, x2, y2), ...]
    :param image: The image on which the rectangles will be drawn
    :return: The merged rectangles drawn on the image
    """
    
    # Step 1: Create a black canvas of the same size as the image
    binary_image = np.zeros_like(image, dtype=np.uint8)
    
    # Step 2: Draw the rectangles on the binary image (white)
    for rect in rectangles:
        cv2.rectangle(binary_image, rect[0], rect[1], (255), thickness=cv2.FILLED)
    
    # Step 3: Apply morphological closing to merge nearby rectangles
    kernel_size = 30 if filter else 1
    kernel = np.ones((kernel_size, kernel_size), np.uint8)  # Adjust the kernel size to merge closely spaced rectangles
    closed_image = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)
    closed_image = cv2.cvtColor(closed_image, cv2.COLOR_BGR2GRAY)


    # Step 4: Find contours in the closed image (merged areas)
    contours, _ = cv2.findContours(closed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    
    print(f"Detected merged boxes: found {len(contours)}")

    # Step 5: Draw the final merged rectangles
    filtered_contours = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if not filter or (w > 10 and h > 10):  # Filter out very small rectangles, only if filter is True
            filtered_contours.append(((x, y), (x + w, y + h)))
    
    return filtered_contours

    


def compute_overlap(a_min, a_max, b_min, b_max):
    return max(0, min(a_max, b_max) - max(a_min, b_min))



def snap_rectangles_to_lines(rectangles, lines, threshold=50):
    """
    Symmetrically adjusts rectangle edges to snap to the closest nearby horizontal or vertical lines,
    preserving the original center of the rectangle.

    Parameters:
    - rectangles: List of rectangles in ((x1, y1), (x2, y2)) format
    - lines: List of lines in (x1, y1, x2, y2) format
    - threshold: Max distance to consider a line "nearby"

    Returns:
    - List of adjusted rectangles
    """
    adjusted_rects = []

    for (rx1, ry1), (rx2, ry2) in rectangles:
        top, bottom = min(ry1, ry2), max(ry1, ry2)
        left, right = min(rx1, rx2), max(rx1, rx2)

        center_y = (top + bottom) // 2
        center_x = (left + right) // 2

        # Initialize distances
        min_top_dist = min_bottom_dist = threshold + 1
        min_left_dist = min_right_dist = threshold + 1

        closest_top = top
        closest_bottom = bottom
        closest_left = left
        closest_right = right

        for x1, y1, x2, y2 in lines:
            if abs(y1 - y2) < 5:  # Horizontal line
                line_y = y1
                line_xmin, line_xmax = min(x1, x2), max(x1, x2)
                if compute_overlap(line_xmin, line_xmax, left, right) > 0:
                    dist_top = abs(line_y - top)
                    dist_bottom = abs(line_y - bottom)
                    if dist_top < min_top_dist:
                        min_top_dist = dist_top
                        closest_top = line_y
                    if dist_bottom < min_bottom_dist:
                        min_bottom_dist = dist_bottom
                        closest_bottom = line_y

            elif abs(x1 - x2) < 5:  # Vertical line
                line_x = x1
                line_ymin, line_ymax = min(y1, y2), max(y1, y2)
                if compute_overlap(line_ymin, line_ymax, top, bottom) > 0:
                    dist_left = abs(line_x - left)
                    dist_right = abs(line_x - right)
                    if dist_left < min_left_dist:
                        min_left_dist = dist_left
                        closest_left = line_x
                    if dist_right < min_right_dist:
                        min_right_dist = dist_right
                        closest_right = line_x

        # Snap vertically to the closest of top or bottom
        if min_top_dist <= threshold or min_bottom_dist <= threshold:
            if min_top_dist <= min_bottom_dist:
                new_top = closest_top
                new_bottom = 2 * center_y - new_top
            else:
                new_bottom = closest_bottom
                new_top = 2 * center_y - new_bottom
        else:
            new_top, new_bottom = top, bottom

        # Snap horizontally to the closest of left or right
        if min_left_dist <= threshold or min_right_dist <= threshold:
            if min_left_dist <= min_right_dist:
                new_left = closest_left
                new_right = 2 * center_x - new_left
            else:
                new_right = closest_right
                new_left = 2 * center_x - new_right
        else:
            new_left, new_right = left, right

        adjusted_rects.append(((new_left, new_top), (new_right, new_bottom)))

    return adjusted_rects


