import cv2
import numpy as np

def find_voids(image):

    if image is None:
        raise ValueError("Image not found or unable to load.")

    # Convert to HSV color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define red color range in HSV
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])

    # Create masks for red color
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)

    # Find contours in the mask
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    red_boxes = []
    for contour in contours:
        # Approximate contour to polygon and check if it's a rectangle
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) == 4 and cv2.isContourConvex(approx):
            x, y, w, h = cv2.boundingRect(approx)
            if w>15 and h>15:
                red_boxes.append((x, y, x + w, y + h))

    return red_boxes

# # Example usage:
# boxes = find_red_boxes("./resources/page1.png")
# print(boxes)
