import cv2
import fitz  # PyMuPDF
import numpy as np
from collections import defaultdict
import Preprocessors.Grey_box_detector as Grey_box_detector
import Preprocessors.Void_box_detector as Void_box_detector

# Load rectangles and void boxes
rectangles = Grey_box_detector.filtered_contours
void_boxes = Void_box_detector.find_voids()

# Sort rectangles by top-left position
def top_left_sort_key(box):
    top_y = min(point[1] for point in box)
    left_x = min(point[0] for point in box)
    row_band = round(top_y / 20)
    return (row_band, left_x)

def top_left_sort_key_void(box):
    (x0, y0), (x1, y1) = box
    row_band = round(y0 / 20)
    return (row_band, x0)

rectangles.sort(key=top_left_sort_key)
void_boxes.sort(key=top_left_sort_key_void)

# Group rectangles by similar Y positions
Y_THRESHOLD = 10
boxes = rectangles[1:]
groups = defaultdict(list)
for idx, box in enumerate(boxes):
    top_y = min(point[1] for point in box)
    key = round(top_y / Y_THRESHOLD)
    groups[key].append((idx + 1, box))

# Load image to get dimensions
image = cv2.imread("contours.png")
img_height, img_width = image.shape[:2]

# Open the PDF
pdf_path = r"C:\Users\CHEWJ1\Downloads\SFL15.6 Switchroom Slab Reinforcements Clean - Copy.pdf"
output_pdf_path = "annotated.pdf"
doc = fitz.open(pdf_path)
page = doc[0]
pdf_width, pdf_height = page.rect.width, page.rect.height

# Coordinate scaling
def scale_coords(x, y):
    return (x / img_width) * pdf_width, (y / img_height) * pdf_height

# Convert void boxes to PDF rectangles
void_rects_pdf = []
for (start, end) in void_boxes:
    x0, y0 = start
    x1, y1 = end
    sx0, sy0 = scale_coords(x0, y0)
    sx1, sy1 = scale_coords(x1, y1)
    void_rects_pdf.append(fitz.Rect(sx0, sy0, sx1, sy1))

# Constants
MAX_LEN = 2000
Y_OFFSET = 8

# Process each group
for group in groups.values():
    group_rectangles = [box for _, box in group]
    y_positions = [np.mean(box.reshape(4, 2), axis=0)[1] for box in group_rectangles]
    avg_y = int(np.mean(y_positions))

    centers = sorted([int(np.mean(box[:, 0])) for box in group_rectangles])
    x_min_group = min(pt[0] for box in group_rectangles for pt in box)
    x_max_group = max(pt[0] for box in group_rectangles for pt in box)
    split_candidates = [x_min_group] + centers + [x_max_group]

    # Generate valid segments
    segments = []
    for i in range(len(split_candidates) - 1):
        x1 = split_candidates[i]
        for j in range(i + 1, len(split_candidates)):
            x2 = split_candidates[j]
            if x2 - x1 <= MAX_LEN:
                segments.append((x1, x2))

    # Dynamic programming to find optimal path
    dp = defaultdict(lambda: (-1, []))
    dp[x_min_group] = (float('inf'), [x_min_group])

    for x1, x2 in segments:
        if x1 in dp:
            min_len, path = dp[x1]
            new_min = min(min_len, x2 - x1)
            if new_min > dp[x2][0]:
                dp[x2] = (new_min, path + [x2])

    if x_max_group not in dp:
        continue

    _, best_path = dp[x_max_group]

    # Draw segments
    for i in range(len(best_path) - 1):
        x1, x2 = best_path[i], best_path[i + 1]
        y = int(avg_y + ((-1) ** i) * Y_OFFSET)
        sx1, sy1 = scale_coords(x1, y)
        sx2, sy2 = scale_coords(x2, y)
        line_rect = fitz.Rect(sx1, sy1, sx2, sy2)

        if not any(line_rect.intersects(vr) for vr in void_rects_pdf):
            line = page.add_line_annot((sx1, sy1), (sx2, sy2))
            line.set_colors(stroke=(1, 0, 0))
            line.set_border(width=2)
            line.update()

# Save the annotated PDF
doc.save(output_pdf_path)
doc.close()
