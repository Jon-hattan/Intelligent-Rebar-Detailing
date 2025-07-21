import cv2
import numpy as np
import fitz  # PyMuPDF
from collections import defaultdict
import math
import merging_lines as merge
import bounding_boxes as bb
import dotted_lines_check as dotted


# FIND BOUNDING BOXES! -----------------------------------------------------------------------------

# -------- STEP 1: Save Image --------
pdf_path = r"C:\Users\CHEWJ1\Downloads\SFL15.6 Switchroom Slab Reinforcements Clean.pdf"
doc = fitz.open(pdf_path)

# Get the first page and render as image
page = doc[0]
pix = page.get_pixmap(dpi=300)  # can adjust dpi

# Save as PNG
pix.save("page1.png")


# -------- STEP 2: Read Image --------
img = cv2.imread("page1.png")
# cv2.imwrite("page1.png", img)


# -------- STEP 3: Mask for Grey Boxes --------
# Split B, G, R channels
b, g, r = cv2.split(img)

# Check where R, G, B are close to each other (grey condition)
diff_rg = cv2.absdiff(r, g)
diff_gb = cv2.absdiff(g, b)
diff_br = cv2.absdiff(b, r)

# Set a threshold for how "close" they should be (tune this!)
tolerance = 10
grey_mask = (diff_rg < tolerance) & (diff_gb < tolerance) & (diff_br < tolerance)

# Check brightness is between mid-range (to avoid black or white)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
brightness_mask = (gray > 50) & (gray < 200)

# Combine both masks
final_mask = (grey_mask & brightness_mask).astype(np.uint8) * 255

# -------- STEP 4: Morphological Filtering --------
# Optional cleanup to remove small noise
kernel = np.ones((4, 4), np.uint8)
cleaned = cv2.morphologyEx(final_mask, cv2.MORPH_OPEN, kernel, iterations=1)


merge_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 30))  # adjust this size
cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, merge_kernel)

kernel = np.ones((5, 5), np.uint8)
dilated = cv2.dilate(cleaned, kernel, iterations=2)
closed = cv2.erode(dilated, kernel, iterations=2)

cleaned = closed

# -------- STEP 5: Find Contours (Grey Box Outlines) --------
contours, _ = cv2.findContours(cleaned, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# -------- STEP 6: Output Box Coordinates --------
min_area = 100  # adjust this threshold as needed (e.g. 1000–3000)
min_width = 10
min_height = 10

filtered_contours = []
for cnt in contours:
    area = cv2.contourArea(cnt)
    x, y, w, h = cv2.boundingRect(cnt)


    if area > min_area and  w > min_width and h > min_height:
        # epsilon = 0.0001 * cv2.arcLength(cnt, True)
        # approx = cv2.approxPolyDP(cnt, epsilon, True)
        # filtered_contours.append(approx)
        filtered_contours.append(cnt)
    

print(f"Detected grey boxes: found {len(filtered_contours)}")

# Draw only large enough contours
contour_img = img.copy()


for i, cnt in enumerate(filtered_contours):

    # Get minimum area rect
    rect = cv2.minAreaRect(cnt)

    # force axis-aligned rectangles
    (cx, cy), (w, h), angle = rect
    if abs(angle) < 10 or abs(angle - 90) < 10:
        angle = 0 if abs(angle) < 10 else 90
        rect = ((cx, cy), (w, h), angle)
        box = cv2.boxPoints(rect)
        box = np.round(box).astype(int)
        box = box.reshape((4,2))
        filtered_contours[i] = box

cv2.drawContours(contour_img, filtered_contours, -1, (255, 0, 0), thickness=2)
cv2.imwrite("contours.png", contour_img)









#------------------------------------------------------------------------------------

# FIND VOID BOXES -- DOTTED LINE BOXES WITH DOTTED CROSS DIAGONALS

# -------- STEP 1: Load Image and Initialize Parameters --------
# Load the image
anglethresh = 1.5
regularity_threshold = 10
transition_threshold = 2
length_threshold_high = 150  # adjust this as needed
length_threshold_low = 10

hough_threshold = 60


img = cv2.imread('page1.png')
output = img.copy()


# -------- STEP 1: Image Processing --------
# Convert to grayscale, and get a binary image, and erode
imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, binary = cv2.threshold(imgGray, 130, 255, cv2.THRESH_BINARY_INV)
binary = cv2.erode(binary, (15,15), iterations = 1) #erode it heavily to ensure lines are distinct
#cv2.imwrite("eroded.png", binary)


# -------- STEP 3: Finding Contours --------
# Filter out long contours before HoughLines --> ONLY TAKE IN DOTTED LINES
contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
filtered_edges = np.zeros_like(binary)
for cnt in contours:
    arc_len = cv2.arcLength(cnt, False)
    if length_threshold_low < arc_len < length_threshold_high:
        cv2.drawContours(filtered_edges, [cnt], -1, 255, thickness=1)
#cv2.imwrite("filtered_edges.png", filtered_edges)


# -------- STEP 4: Finding Dotted Lines --------
# HoughLinesP to detect all remaining dotted lines
imgLines = cv2.HoughLinesP(filtered_edges, 1, np.pi / 1440, threshold=hough_threshold, minLineLength=45, maxLineGap=30)

# Loop through all lines detected, and only take in proper lines
dotted_lines = []
for line in imgLines:
    x1, y1, x2, y2 = line[0]
    theta = dotted.calculate_angle(x1,y1,x2,y2)
    result = dotted.is_dotted(imgGray, line[0], transition_threshold, regularity_threshold)
    if result == "Is Dotted Line" and abs(theta-0) > anglethresh and abs(180-theta) > anglethresh and abs(theta-90)>anglethresh:  # Check if the line is dotted
        dotted_lines.append((x1, y1, x2, y2))
        cv2.line(output, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Draw red lines for dotted
    elif result == "Lines too Irregular":
        cv2.line(output, (x1, y1), (x2, y2), (0,255 , 0), 2)  # Draw green lines for too irregular lines
    elif result == "Not Enough Transitions":
        cv2.line(output, (x1, y1), (x2, y2), (255,0 , 0), 2)  # Draw blue lines for not enough transitions
    else:
        cv2.line(output, (x1, y1), (x2, y2), (255,255 , 0), 2)

# Save the result
cv2.imwrite("proper_lines.png", output)


# -------- STEP 5: Joining the Disjointed Dotted Lines --------

# Create a blank mask for dotted lines
dotted_mask = np.zeros_like(imgGray)

for x1, y1, x2, y2 in dotted_lines: #filtering out only the angled lines
    theta = dotted.calculate_angle(x1,y1,x2,y2)
    if abs(theta-0) > anglethresh and abs(180-theta) > anglethresh and abs(theta-90)>anglethresh:
        cv2.line(dotted_mask, (x1, y1), (x2, y2), 255, 2)

# Second pass: Hough line on the mask of dotted-only lines, joining the disjoint lines together
dotted_mask = cv2.erode(dotted_mask, (21, 21), iterations = 1)
lines = cv2.HoughLinesP(dotted_mask, 1, np.pi/360, threshold=150, minLineLength=40, maxLineGap=150)

# Merge lines that are similar or collinear:
merged_lines = merge.efficient_merge_lines(lines)
merged_lines = merge.merge_all_colinear_lines(merged_lines)

#Show lines on joinedlines.png
mask = np.zeros_like(imgGray)

for line in merged_lines:
    x1, y1, x2, y2 = line
    cv2.line(mask, (x1, y1), (x2, y2), (255, 0, 255), 2)  # Use purple to distinguish
#cv2.imwrite("joinedlines.png", mask)





# -------- STEP 5: Drawing Bounding Boxes for Voids --------

bound = cv2.imread('page1.png').copy()

# Function to find intersections and generate bounding rectangles
rectangles = bb.get_intersection_bounding_boxes(merged_lines)
#print(f"Detected void boxes: found {len(rectangles)}")


for rect in rectangles:
    cv2.rectangle(bound, rect[0], rect[1], (0,0,255), 2)
#cv2.imwrite("voids.png", bound)


# Merge rectangles using morphology
merged_image = bb.merge_rectangles_with_morphology(rectangles, img)

# Save the result
cv2.imwrite('merged_voids.png', merged_image)