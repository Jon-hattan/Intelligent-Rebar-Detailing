import cv2
import numpy as np
import fitz  # PyMuPDF
from collections import defaultdict
import math


def get_enclosing_bounding_box(contours):
    # Flatten all contour points into a single array
    all_points = np.vstack(contours)

    # Get the bounding rectangle of all points
    x, y, w, h = cv2.boundingRect(all_points)

    # Return the top-left and bottom-right corners
    return (x, y), (x + w, y + h)

def find_white_boxes_within_region(image, region_top_left, region_bottom_right):
    x1, y1 = region_top_left
    x2, y2 = region_bottom_right

    # Crop the region of interest
    roi = image[y1:y2, x1:x2]

    # Convert to grayscale and threshold for white
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

    # Optional cleanup to remove small noise
    kernel = np.ones((4, 4), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)


    merge_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 30))  # adjust this size
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, merge_kernel)

    # Find contours in the thresholded image
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    white_boxes = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Filter small boxes if needed
        if w > 10 and h > 10:
            # Adjust coordinates back to original image
            white_boxes.append((x + x1, y + y1, x + x1 + w, y + y1 + h))

    return white_boxes



def is_rectangle_like(contour, epsilon_factor=0.02, min_area=100):
    # Approximate the contour
    epsilon = epsilon_factor * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)

    # Check if it's a quadrilateral and convex
    if 4 <= len(approx) <= 6:
        area = cv2.contourArea(approx)
        if area > min_area:
            return True
    return False


def find_grey_contours(img):
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
    brightness_mask = (gray > 50) & (gray <= 200)

    # Combine both masks
    final_mask = (grey_mask & brightness_mask).astype(np.uint8) * 255

    # -------- STEP 4: Morphological Filtering --------
    # Optional cleanup to remove small noise
    kernel = np.ones((4, 4), np.uint8)
    cleaned = cv2.morphologyEx(final_mask, cv2.MORPH_OPEN, kernel, iterations=1)


    merge_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 30))  # adjust this size
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, merge_kernel)

    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(cleaned, kernel, iterations=1)
    closed = cv2.erode(dilated, kernel, iterations=2)

    cleaned = cv2.GaussianBlur(closed, (5,5), 0)

    # -------- STEP 5: Find Contours (Grey Box Outlines) --------
    contours, _ = cv2.findContours(cleaned, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)


    return contours




def find_black_boxes(img, enclosing_box, solidity_thresh=0.95, fill_ratio_thresh=0.95):
    x0, y0 = enclosing_box[0]
    x1, y1 = enclosing_box[1]

    # Crop the region of interest
    roi = img[y0:y1, x0:x1]

    # Convert to grayscale and apply fixed thresholding
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, binary_mask = cv2.threshold(gray_roi, 50, 255, cv2.THRESH_BINARY_INV)
    
    # Morphological operations to clean up noise
    kernel = np.ones((3, 3), np.uint8)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel, iterations=1)


    # # Save the binary mask for debugging
    # cv2.imwrite("black_box_processing_fixed_threshold.png", binary_mask)

    # Find contours in the binary mask
    black_contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # black_cont = roi.copy()
    # cv2.drawContours(black_cont, black_contours, -1, (255, 0, 0), thickness=2)
    # cv2.imwrite("black_contours.png", black_cont)

    # Filter and map contours back to original image coordinates
    black_boxes = []
    for cnt in black_contours:
        area = cv2.contourArea(cnt)

        # Solidity
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area > 0 else 0

        # Fill ratio
        x, y, w, h = cv2.boundingRect(cnt)
        roi_box = binary_mask[y:y+h, x:x+w]
        bounding_box_area = w * h
        fill_ratio = cv2.countNonZero(roi_box) / bounding_box_area if bounding_box_area > 0 else 0

        if area > 500 and solidity > solidity_thresh and fill_ratio > fill_ratio_thresh:
            cnt[:, 0, 0] += x0  # shift x
            cnt[:, 0, 1] += y0  # shift y
            black_boxes.append(cnt)

    # Convert contours to axis-aligned rectangles
    final_boxes = []
    for cnt in black_boxes:
        rect = cv2.minAreaRect(cnt)
        (cx, cy), (w, h), angle = rect
        if abs(angle) < 10 or abs(angle - 90) < 10:
            angle = 0 if abs(angle) < 10 else 90
            rect = ((cx, cy), (w, h), angle)
            box = cv2.boxPoints(rect)
            box = np.round(box).astype(int)
            final_boxes.append(box)

    return final_boxes



def filter_contours(contours, min_area, min_width, min_height, rectangle_check = False):
    filtered_contours = []
    rejected = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        x, y, w, h = cv2.boundingRect(cnt)
        is_rect = is_rectangle_like(cnt) if rectangle_check else True


        if area > min_area and  w > min_width and h > min_height and is_rect:
            # epsilon = 0.0001 * cv2.arcLength(cnt, True)
            # approx = cv2.approxPolyDP(cnt, epsilon, True)
            # filtered_contours.append(approx)
            filtered_contours.append(cnt)
        elif not is_rectangle_like(cnt):
            rejected.append(cnt)
    return filtered_contours, rejected


def whiten_black_pixels(img, tolerance = 150, brightness_threshold = 150):
    # Convert to grayscale to simplify brightness analysis
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Define a mask for "remotely grey" pixels
    # These are pixels where R ≈ G ≈ B and brightness is low (dark grey)

    b, g, r = cv2.split(img)
    diff_rg = cv2.absdiff(r, g)
    diff_gb = cv2.absdiff(g, b)
    diff_br = cv2.absdiff(b, r)

    grey_mask = (diff_rg < tolerance) & (diff_gb < tolerance) & (diff_br < tolerance)
    dark_mask = gray < brightness_threshold

    # Combine masks
    remotely_grey_mask = grey_mask & dark_mask

    # Apply the mask to set those pixels to white
    img[remotely_grey_mask] = [255, 255, 255]




def cut_side_boxes(enclosing_box, boxes):
    xa, ya = enclosing_box[0]
    xb, yb = enclosing_box[1]
    x_min = min(xa, xb)
    x_max = max(xa, xb)
    y_min = min(ya, yb)
    y_max = max(ya, yb)

    res = []
    for x1,y1,x2,y2 in boxes:
        if abs(x1 - x_min) > 5 and abs(x2 - x_max) > 5 and abs(y1 - y_max) > 5 and abs(y2 - y_min) > 5:
            res.append((x1,y1,x2,y2))
    
    return res












def find_bounding_boxes(pdf_path):

    # FIND BOUNDING BOXES! -----------------------------------------------------------------------------
    print("\nFinding bounding boxes...")

    # -------- STEP 1: Save Image --------
    doc = fitz.open(pdf_path)

    # Get the first page and render as image
    page = doc[0]
    pix = page.get_pixmap(dpi=300)  # can adjust dpi

    # Save as PNG
    pix.save("page1.png")


    # -------- STEP 2: Read Image and Find Grey Contours --------
    img = cv2.imread("page1.png")
    # cv2.imwrite("page1.png", img)

    #find grey contours in the image
    print("Finding grey boxes...")
    grey_contours = find_grey_contours(img)
    
    # Draw contours
    grey_imgs = img.copy()
    cv2.drawContours(grey_imgs, grey_contours, -1, (0, 0, 255), 2)  # -1 means draw all contours
    #cv2.imwrite("grey_boxes.png", grey_imgs)

    # -------- STEP 3: Filter the small Contours and find the enclosing box --------
    min_area = 400  # adjust this threshold as needed (e.g. 1000–3000)
    min_width = 20
    min_height = 20

    filtered_grey_boxes, _ = filter_contours(grey_contours, min_area, min_width, min_height)
    enclosing_box = get_enclosing_bounding_box(filtered_grey_boxes)
    cont = img.copy()
    cv2.drawContours(cont, filtered_grey_boxes, -1, (255, 0, 0), thickness=2)
    #cv2.imwrite("contours.png", cont)

    # -------- STEP 4: Detect Black Boxes Within Enclosing Box --------
    print("Finding black boxes...")
    black_boxes = find_black_boxes(img, enclosing_box)


    min_area = 400  # adjust this threshold as needed (e.g. 1000–3000)
    min_width = 20
    min_height = 20
    
    filtered_black_boxes, _ = filter_contours(black_boxes, min_area, min_width, min_height, rectangle_check = True)


    # Draw black boxes on the image
    contour_img = img.copy()
    whiten_black_pixels(contour_img)

    cv2.drawContours(contour_img, filtered_grey_boxes, -1, (0, 0, 0), thickness=-1)
    cv2.drawContours(contour_img, filtered_black_boxes, -1, (0, 0, 0), thickness=-1)
    cv2.drawContours(contour_img, filtered_black_boxes, -1, (0, 0, 0), thickness=20)
    cv2.rectangle(contour_img, enclosing_box[0], enclosing_box[1], (0,255,0), 2)

    print("Finding white boxes...")
    boxes = find_white_boxes_within_region(contour_img, enclosing_box[0], enclosing_box[1])

    boxes = cut_side_boxes(enclosing_box, boxes)

    for x1, y1, x2, y2 in boxes:
            cv2.rectangle(contour_img, (x1, y1), (x2, y2), (0,255,0), 2)

    #cv2.imwrite("whiteboxes.png", contour_img)


    print(f"Detected bounding boxes: found {len(boxes)}")

    cv2.imwrite("boundingboxes.png", contour_img)

    return boxes



#find_bounding_boxes(r"C:\Users\CHEWJ1\Downloads\131101-WIP12-DR-S-5123 & 5124_commented_20250414 1 (1).pdf")

