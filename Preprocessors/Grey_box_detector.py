import cv2
import numpy as np
import fitz  # PyMuPDF
from collections import defaultdict
import math



# FIND BOUNDING BOXES! -----------------------------------------------------------------------------
print("\nFinding bounding boxes...")

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






