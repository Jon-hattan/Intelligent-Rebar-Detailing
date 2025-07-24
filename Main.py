import cv2
import fitz  # PyMuPDF
import numpy as np
import math
from collections import defaultdict
import Preprocessors.Grey_box_detector as Grey_box_detector
import Preprocessors.Void_box_detector as Void_box_detector
import optimal_lines as OL
import Preprocessors.Rectangle_subtraction as RS
import Box_grouper as  BG

# Load rectangles and void boxes
rectangles = Grey_box_detector.filtered_contours
void_boxes = Void_box_detector.find_voids()

#convert rectangles to corner points
bounding_rects = []
for box in rectangles[1:]:
    x_coords = box[:, 0]
    y_coords = box[:, 1]
    x1, y1 = x_coords.min(), y_coords.min()
    x2, y2 = x_coords.max(), y_coords.max()
    bounding_rects.append((x1, y1, x2, y2))

void_rects = [(min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])) for (a, b) in void_boxes]



# Sort rectangles by top-left position
def sortingkey(banded = True):
    def top_left_sort_key(box):
        top_y = min(point[1] for point in box)
        left_x = min(point[0] for point in box)
        row_band = round(top_y / 10) if banded else top_y
        return (row_band, left_x)
    return top_left_sort_key

rectangles.sort(key=sortingkey())
void_boxes.sort(key=sortingkey())

# Do rectangular substraction
remaining_rects = RS.rectangle_subtraction(bounding_rects, void_rects, 20, 20)
remaining_rects.sort(key = sortingkey())

# Group threshold for similar top y positions
Y_THRESHOLD = 20
boxes = remaining_rects

# groups = defaultdict(list) #maps the groups to the (box index, box)
# for idx, box in enumerate(boxes):
#     top_y = min(point[1] for point in box)
#     key = round(top_y / Y_THRESHOLD)
#     groups[key].append((idx + 1, box)) #box index, box
groups = BG.group_boxes(remaining_rects, void_rects)

# Use the 0-th box as horizontal span
zero_box = rectangles[0]
x_leftbound = min(pt[0] for pt in zero_box)
x_rightbound = max(pt[0] for pt in zero_box)

# Load the image to get dimensions

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
MAX_LEN = 2500
Y_OFFSET = 8
X_OVERLAP = 80

def get_rect_x_range(rects): #find the lowest and highest x values for the boxes
    x_values = [x for rect in rects for x in (rect[0], rect[2])]
    return min(x_values), max(x_values)

x_min, x_max = get_rect_x_range(bounding_rects) #the minimum x and max x for the rectangles



print("Annotating diagram....")
for key, group in groups.items():
    lines = OL.find_optimal_lines(group, Y_OFFSET, X_OVERLAP, x_rightbound, x_leftbound, x_min, x_max, MAX_LEN)
    for line in lines:
        (x1, y), (x2, y) = line
        sx1, sy1 = scale_coords(x1, y)
        sx2, sy2 = scale_coords(x2, y)
        line = page.add_line_annot((sx1, sy1), (sx2, sy2))
        line.set_colors(stroke=(0, 0, 1))
        line.set_border(width=1)
        line.update()
        note = page.insert_text((0.5*(sx1 + sx2), 0.5*(sy1+sy2)), str(key), fontsize = 6, color = (0, 0 ,1))

    
    # # Label box indices
    # for idx, box in group:
    #     box = np.array(box)  # Ensure it's a NumPy array
    #     M = np.mean(box, axis=0)  # Compute center point
    #     center_x, center_y = int(M[0]), int(M[1])
    #     sx, sy = scale_coords(center_x, center_y)
    #     note = page.insert_text((sx, sy), str(idx) + "," + str(key), fontsize = 8, color = (1, 0 ,0))
    #     #writes the idx and group key

        
    # # Draw rectangle
    #     x1, y1 = box.min(axis=0)
    #     x2, y2 = box.max(axis=0)
    #     sx1, sy1 = scale_coords(x1, y1)
    #     sx2, sy2 = scale_coords(x2, y2)
    #     rect = fitz.Rect(sx1, sy1, sx2, sy2)
    #     shape = page.new_shape()
    #     shape.draw_rect(rect)
    #     shape.finish(color=(0, 0, 1), fill=None, width=0.5)
    #     shape.commit()






# Save the annotated PDF
doc.save(output_pdf_path)
doc.close()

print(f"\nAnnotated PDF saved as {output_pdf_path}")
