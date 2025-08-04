
import cv2
import numpy as np

def detect_direction_guides(ref_full_img, ref_half_img, target_img):

    print("\nFinding direction guides....")
    ## Load images in color (default), then convert to grayscale
    # ref_full_img = cv2.imread('reference_full.png')
    # ref_half_img = cv2.imread('reference_half.png')
    # #target_img = cv2.imread('target.png')
    # target_img = cv2.imread('page1.png')

    # Convert to HSV color space
    hsv = cv2.cvtColor(target_img, cv2.COLOR_BGR2HSV)

    # Define red color range in HSV
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])

    # Create masks for red
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)



    # Convert to grayscale
    ref_full_gray = cv2.cvtColor(ref_full_img, cv2.COLOR_BGR2GRAY)
    ref_half_gray = cv2.cvtColor(ref_half_img, cv2.COLOR_BGR2GRAY)


    # Apply binary threshold
    _, ref_full_thresh = cv2.threshold(ref_full_gray, 200, 255, cv2.THRESH_BINARY_INV)
    _, ref_half_thresh = cv2.threshold(ref_half_gray, 200, 255, cv2.THRESH_BINARY_INV)


    # Now find contours
    contours_full_ref, _ = cv2.findContours(ref_full_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_half_ref, _ = cv2.findContours(ref_half_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # plt.imshow(red_mask)
    # plt.show()
    contours_target, _ = cv2.findContours(red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)


    # Draw matches on color version of target image
    output_img = target_img.copy()  # No need to convert

    two_way = []
    one_way = []

    for cnt in contours_target:
        ##Find two way loading direction
        cont_diff = cv2.matchShapes(contours_full_ref[0], cnt, cv2.CONTOURS_MATCH_I3, 0)
        if cont_diff< 10:  # Adjust threshold as needed
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(output_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            two_way.append((x, y, x+w, y+h)) #x1, y1, x2, y2 form
        # # Draw the cont_diff value as text
        #     text = f"{cont_diff:.2f}"
        #     cv2.putText(output_img, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 
        #                 1, (0, 0, 255), 2, cv2.LINE_AA)
            continue

    
            

        ##Find one way loading direction
        cont_diff = cv2.matchShapes(contours_half_ref[0], cnt, cv2.CONTOURS_MATCH_I3, 0)
        if cont_diff< 1:  # Adjust threshold as needed
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(output_img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            one_way.append((x, y, x+w, y+h))
        # # Draw the cont_diff value as text
        #     text = f"{cont_diff:.2f}"
        #     cv2.putText(output_img, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 
        #                 1, (0, 0, 255), 2, cv2.LINE_AA)
            
            
    cv2.imwrite("./resources/direction_guides.png", output_img)

    return two_way, one_way


