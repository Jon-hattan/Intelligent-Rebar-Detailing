import cv2
import numpy as np
import Grey_box_detector
import Void_box_detector
from collections import defaultdict


rectangles = Grey_box_detector.filtered_contours
void_boxes = Void_box_detector.find_voids()


# -------- STEP 1: Sort Boxes --------
#sort rectangles by approx top y-position, then x position
def top_left_sort_key(box):
    # Find top-most Y point (min Y)
    top_y = min(point[1] for point in box)
    # Find left-most X point (min X)
    left_x = min(point[0] for point in box)
    # Round Y to the nearest band (e.g. 20px) to group by row
    row_band = round(top_y / 20)
    return (row_band, left_x)

rectangles.sort(key=top_left_sort_key)


# -------- STEP 2: Process Boxes --------
contour_img = cv2.imread("contours.png")

# Group threshold for similar top y positions
Y_THRESHOLD = 10  # you can tune this

# Extract the boxes (skip index 0)
boxes = rectangles[1:]

# Group boxes by similar top y-values
groups = defaultdict(list)
for idx, box in enumerate(boxes):
    top_y = min(point[1] for point in box)
    # Round to nearest threshold bin
    key = round(top_y / Y_THRESHOLD)
    groups[key].append((idx + 1, box))  # store original index for debug

# Use the 0-th box as horizontal span
zero_box = rectangles[0]
x_min = min(pt[0] for pt in zero_box)
x_max = max(pt[0] for pt in zero_box)

#Initialize parameters for line drawing
MAX_LEN = 2000         # max allowed length for each segment
Y_OFFSET = 8           # pixel offset between each stacked line
OVERLAP = 80           # amount of overlap between segments (pixels)

for group in groups.values():
    y_positions = []
    for _, box in group:
        center = np.mean(box.reshape(4, 2), axis=0)
        y_positions.append(center[1])
    avg_y = int(np.mean(y_positions))

    total_length = x_max - x_min

    if total_length > MAX_LEN:
        # Calculate number of splits required
        n_splits = int(np.ceil(total_length / MAX_LEN))
        segment_length = total_length / n_splits
        segment_overlap = OVERLAP

        # Draw each split segment
        for i in range(n_splits):
            x1 = int(x_min + i * segment_length)
            x2 = int(x1 + segment_length + segment_overlap)

            # prevent overshooting final x_max
            if x2 > x_max:
                x2 = int(x_max)

            y = int(avg_y + ((-1)**i) * Y_OFFSET)  # vertical offset alternates
            cv2.line(contour_img, (x1, y), (x2, y), (0, 0, 255), 2)

    else:
        # Draw a single full-length line
        cv2.line(contour_img, (int(x_min), avg_y), (int(x_max), avg_y), (0, 0, 255), 2)



# -------- STEP OPTIONAL: Label Box Indices for clarity --------
for idx, box in enumerate(rectangles):

    # Compute center by averaging 4 points
    M = np.mean(box.reshape(4, 2), axis=0)
    center_x, center_y = int(M[0]), int(M[1])

    # Put index label at center
    cv2.putText(contour_img, str(idx), (center_x, center_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)

# cv2.arrowedLine(contour_img, (100, 200), (300, 200), (255, 0, 0), thickness=10, tipLength=0.05)
cv2.imwrite("contours.png", contour_img)