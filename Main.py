import fitz  # PyMuPDF
import numpy as np
from collections import defaultdict
import Grey_box_detector
import Void_box_detector

# Load rectangles and void boxes
rectangles = Grey_box_detector.filtered_contours
void_boxes = Void_box_detector.find_voids()

# Sort rectangles by top-left position
def top_left_sort_key(box):
    top_y = min(point[1] for point in box)
    left_x = min(point[0] for point in box)
    row_band = round(top_y / 20)
    return (row_band, left_x)

rectangles.sort(key=top_left_sort_key)

# Group threshold for similar top y positions
Y_THRESHOLD = 10
boxes = rectangles[1:]

groups = defaultdict(list)
for idx, box in enumerate(boxes):
    top_y = min(point[1] for point in box)
    key = round(top_y / Y_THRESHOLD)
    groups[key].append((idx + 1, box))

# Use the 0-th box as horizontal span
zero_box = rectangles[0]
x_min = min(pt[0] for pt in zero_box)
x_max = max(pt[0] for pt in zero_box)

# Load the image to get dimensions
import cv2
image = cv2.imread("contours.png")
img_height, img_width = image.shape[:2]

# Open the PDF and get page dimensions
pdf_path = r"C:\Users\CHEWJ1\Downloads\SFL15.6 Switchroom Slab Reinforcements Clean - Copy.pdf"
output_pdf_path = "annotated.pdf"
doc = fitz.open(pdf_path)
page = doc[0]
pdf_width, pdf_height = page.rect.width, page.rect.height

# Coordinate scaling function
def scale_coords(x, y):
    return (x / img_width) * pdf_width, (y / img_height) * pdf_height

# Draw lines on PDF
MAX_LEN = 2000
Y_OFFSET = 8
OVERLAP = 80

for group in groups.values():
    y_positions = []
    for _, box in group:
        center = np.mean(box.reshape(4, 2), axis=0)
        y_positions.append(center[1])
    avg_y = int(np.mean(y_positions))

    total_length = x_max - x_min

    if total_length > MAX_LEN:
        n_splits = int(np.ceil(total_length / MAX_LEN))
        segment_length = total_length / n_splits

        for i in range(n_splits):
            x1 = int(x_min + i * segment_length)
            x2 = int(x1 + segment_length + OVERLAP)
            if x2 > x_max:
                x2 = int(x_max)
            y = int(avg_y + ((-1) ** i) * Y_OFFSET)
            sx1, sy1 = scale_coords(x1, y)
            sx2, sy2 = scale_coords(x2, y)
            line = page.add_line_annot((sx1, sy1), (sx2, sy2))
            line.set_colors(stroke=(1, 0, 0))
            line.set_border(width=2)
            line.update()
    else:
        sx1, sy1 = scale_coords(x_min, avg_y)
        sx2, sy2 = scale_coords(x_max, avg_y)
        line = page.add_line_annot((sx1, sy1), (sx2, sy2))
        line.set_colors(stroke=(1, 0, 0))
        line.set_border(width=2)
        line.update()

# # Label box indices
# for idx, box in enumerate(rectangles):
#     M = np.mean(box.reshape(4, 2), axis=0)
#     center_x, center_y = int(M[0]), int(M[1])
#     sx, sy = scale_coords(center_x, center_y)
#     note = page.add_text_annot((sx, sy), str(idx))
#     note.set_colors(stroke=(1, 0, 0), fill=(1, 1, 0.8))
#     note.update()

# Save the annotated PDF
doc.save(output_pdf_path)
doc.close()

print(f"Annotated PDF saved as {output_pdf_path}")
