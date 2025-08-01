import cv2
import numpy as np
from collections import defaultdict
import math
from Preprocessors.Helpers import merging_lines as merge
from Preprocessors.Helpers import bounding_boxes as bb
from Preprocessors.Helpers import dotted_lines_check as dotted

def find_void_boxes_withSize(img, roi=None, size_upper=150, size_lower=10):

    size_limit = 30
    size = "large" if size_upper > size_limit else "medium"
    print(f"\nFinding {size} void boxes....\n")

    anglethresh = 2
    regularity_threshold = 10
    transition_threshold = 2
    length_threshold_high = size_upper
    length_threshold_low = size_lower
    hough_threshold = 30 if size_upper > size_limit else 20

    output = img.copy()

    # Apply ROI cropping if specified
    if roi:
        (x1, y1), (x2, y2) = roi
        img = img[y1:y2, x1:x2]
        roi_offset = (x1, y1)
    else:
        roi_offset = (0, 0)

     # -------- STEP 1: Image Processing --------
    # Convert to grayscale, and get a binary image, and erode
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(imgGray, 130, 255, cv2.THRESH_BINARY_INV)
    if size_upper > size_limit:
        binary = cv2.erode(binary, (20,20), iterations = 1) #erode it heavily to ensure lines are distinct
    #cv2.imwrite("eroded.png", binary)


    # -------- STEP 3: Finding Contours --------
    # Filter out long contours before HoughLines --> ONLY TAKE IN DOTTED LINES
    contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if contours is None:
        return []
    
    filtered_edges = np.zeros_like(binary)
    for cnt in contours:
        arc_len = cv2.arcLength(cnt, False)
        if length_threshold_low < arc_len < length_threshold_high:
            cv2.drawContours(filtered_edges, [cnt], -1, 255, thickness=1)
    # cv2.imwrite("filtered_edges.png", filtered_edges)


    # -------- STEP 4: Finding Dotted Lines --------
    # HoughLinesP to detect all remaining dotted lines
    smallest_line_length = 45 if size_upper > size_limit else 20
    max_line_gap = 30 if size_upper > size_limit else 5
    resolution = 1440
    # if size_upper < size_limit: #dilate if lines are too small
    #     #filtered_edges = cv2.dilate(filtered_edges, (3,3), iterations = 3)
    #     #cv2.imwrite("filtered_edges.png", filtered_edges)
    imgLines = cv2.HoughLinesP(filtered_edges, 1, np.pi / resolution, threshold=hough_threshold, minLineLength=smallest_line_length, maxLineGap=max_line_gap)
    if imgLines is None:
        return []
    # Loop through all lines detected, and only take in proper lines
    dotted_lines = []
    potential_snap_lines = []
    for line in imgLines:
        x1, y1, x2, y2 = line[0]
        theta = dotted.calculate_angle(x1,y1,x2,y2)
        result = dotted.is_dotted(imgGray, line[0], transition_threshold, regularity_threshold)
        
        if result == "Lines too Irregular":
            cv2.line(output, (x1, y1), (x2, y2), (0,255 , 0), 2)  # Draw green lines for too irregular lines

        elif result == "Not Enough Transitions":
            cv2.line(output, (x1, y1), (x2, y2), (255,0 , 0), 2)  # Draw blue lines for not enough transitions
            potential_snap_lines.append((x1, y1, x2, y2))
        elif result == "Is Dotted Line" and abs(theta-0) > anglethresh and abs(180-theta) > anglethresh and abs(theta-90)>anglethresh:  # Check if the line is dotted
            dotted_lines.append((x1, y1, x2, y2))
            cv2.line(output, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Draw red lines for dotted
        else:
            cv2.line(output, (x1, y1), (x2, y2), (255,255 , 0), 2)
            potential_snap_lines.append((x1, y1, x2, y2))
    
    if not dotted_lines:
        return []

    # Save the result
    cv2.imwrite("./resources/lines_detected.png", output)


    # -------- STEP 5: Joining the Disjointed Dotted Lines --------

    # Create a blank mask for dotted lines
    dotted_mask = np.zeros_like(imgGray)

    for x1, y1, x2, y2 in dotted_lines: #filtering out only the angled lines
        theta = dotted.calculate_angle(x1,y1,x2,y2)
        if abs(theta-0) > anglethresh and abs(180-theta) > anglethresh and abs(theta-90)>anglethresh:
            cv2.line(dotted_mask, (x1, y1), (x2, y2), 255, 2)

    # Second pass: Hough line on the mask of dotted-only lines, joining the disjoint lines together
    if size_upper > size_limit:
        dotted_mask = cv2.erode(dotted_mask, (21, 21), iterations = 1)
    
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))  # You can adjust size
    dotted_mask = cv2.morphologyEx(dotted_mask, cv2.MORPH_CLOSE, kernel)


    smallest_line_length = 40 if size_upper > size_limit else 20
    max_line_gap = 180 if size_upper > size_limit else 5
    resolution = 360
    h_threshold = 150 if size_upper > size_limit else 100

    lines = cv2.HoughLinesP(dotted_mask, 1, np.pi/360, threshold=h_threshold, minLineLength=smallest_line_length, maxLineGap=max_line_gap)
    if lines is None:
        return []

    # Merge lines that are similar or collinear.
    merged_lines = merge.efficient_merge_lines(lines)
    merged_lines = merge.merge_all_colinear_lines(merged_lines)
    print(f"Merged lines: from {len(lines)} to {len(merged_lines)}")


    #Show lines on joinedlines.png
    mask = np.zeros_like(imgGray)

    for line in merged_lines:
        x1, y1, x2, y2 = line
        cv2.line(mask, (x1, y1), (x2, y2), (255, 0, 255), 2)  # Use purple to distinguish
    # cv2.imwrite("joinedlines.png", mask)





    # -------- STEP 5: Drawing Bounding Boxes for Voids --------

    bound = cv2.imread('./resources/page1.png').copy()

    # Function to find intersections and generate bounding rectangles
    rectangles = bb.get_intersection_bounding_boxes(merged_lines)


    for rect in rectangles:
        cv2.rectangle(bound, rect[0], rect[1], (0,0,255), 2)
    # cv2.imwrite("voids.png", bound)
    

    #POST-PROCESSING

    # Merge rectangles using morphology
    merged_rectangles = bb.merge_rectangles_with_morphology(rectangles, img, size_upper > size_limit)


    #Snap rectangles into nearest horizontal or vertical lines
    snap_threshold = 50 if size_upper > size_limit else 5
    snapped_rectangles = bb.snap_rectangles_to_lines(merged_rectangles, potential_snap_lines, snap_threshold)

    


    
    # Draw Merged Rectangles
    output_image = img.copy()
    for (a, b) in merged_rectangles:
        cv2.rectangle(output_image, a, b, (0, 0, 255), 2)

    # Save the result
    #cv2.imwrite('./resources/merged_voids.png', output_image)


    # Offset merged lines back to original image coordinates
    offset_lines = []
    for (x1_, y1_), (x2_, y2_) in snapped_rectangles:
        offset_lines.append((
            x1_ + roi_offset[0], 
            y1_ + roi_offset[1],
            x2_ + roi_offset[0], 
            y2_ + roi_offset[1]
        ))

    return offset_lines



def find_voids(img, roi = None, detect_mediums = True):
    if detect_mediums:
        void_boxes = find_void_boxes_withSize(img, roi, 20, 0) #Medium size
    else:
        void_boxes = []
    void_boxes.extend(find_void_boxes_withSize(img, roi)) #Big size boxes

    output = img.copy()
    for x1, y1, x2, y2 in void_boxes:
        cv2.rectangle(output, (x1,y1), (x2,y2), (0,0,255), 2)
    cv2.imwrite('./resources/merged_voids.png', output)

    return void_boxes



#Example usage
# img = cv2.imread("./resources/page1.png")

# # #should only find void boxes within the part where the floor plan lies in.
# # void_boxes = find_voids(img)