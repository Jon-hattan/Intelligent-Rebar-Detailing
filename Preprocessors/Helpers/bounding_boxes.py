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

    