import cv2
import fitz  # PyMuPDF
import numpy as np
import math
from collections import defaultdict
import Preprocessors.BoundingBox_detector2 as bounding_box_detector
import Preprocessors.Void_box_detector as Void_box_detector
import Preprocessors.Rectangle_subtraction as RS
import Processor.optimal_lines as OL
import Processor.Box_grouper2 as  BG
import Processor.draw_arrows as DA


def process_pdf(pdf_path = None, scale_factor =  0.005):

    # Load rectangles and void boxes
    rectangles, enclosure = bounding_box_detector.find_bounding_boxes(pdf_path)


    def get_enclosing_bounding_box(lines):
        points = np.array([[x, y] for line in lines for x, y in [(line[0], line[1]), (line[2], line[3])]])
        min_x, min_y = points.min(axis=0)
        max_x, max_y = points.max(axis=0)
        return (min_x, min_y), (max_x, max_y)



    roi = get_enclosing_bounding_box(rectangles)
    img = cv2.imread("./resources/page1.png")

    #should only find void boxes within the part where the floor plan lies in.
    void_boxes = Void_box_detector.find_voids(img, roi, detect_mediums=True)


    #convert rectangles to corner points
    bounding_rects = rectangles #in the form of 4 (x1, y1, x2, y2)
    void_rects = void_boxes #in the form of 4 (x1, y1, x2, y2)


    #convert beam contours into rectangles by cutting horizontally
    beams_horizontal = RS.rectangle_subtraction_beams(enclosure, bounding_rects, 20, 20, 500, direction = "horizontal")
    beams_vertical = RS.rectangle_subtraction_beams(enclosure, bounding_rects, 20, 20, 500, direction = "vertical")

    

    # Sort rectangles by top-left position
    def sortingkey(banded = True):
        def top_left_sort_key(box):
            x1, y1, x2, y2 = box
            top_y = min(y1, y2)
            left_x = min(x1, x2)
            row_band = round(top_y / 100) if banded else top_y
            return (row_band, left_x)
        return top_left_sort_key

    # rectangles.sort(key=sortingkey())
    void_boxes.sort(key=sortingkey(banded=False))

    # Do rectangular substraction
    remaining_rects_horizontal = RS.rectangle_subtraction(bounding_rects, void_rects, 20, 20, 500, direction = "horizontal")
    remaining_rects_vertical = RS.rectangle_subtraction(bounding_rects, void_rects, 20, 20, 500, direction = "vertical")

    


    # Group threshold for similar top y positions
    MAX_LEN = 12 // scale_factor #12 meters is the limit
    groups_horizontal = BG.group_boxes(remaining_rects_horizontal, void_rects, beams_vertical, MAX_LEN, direction = "horizontal")
    groups_vertical = BG.group_boxes(remaining_rects_vertical, void_rects, beams_horizontal, MAX_LEN, direction = "vertical")

    # Find horizontal and vertical span
    x_leftbound = min(min(x1, x2) for (x1, _, x2, _) in rectangles)
    x_rightbound = max(max(x1, x2) for (x1, _, x2, _) in rectangles)
    y_topbound = min(min(y1, y2) for (_, y1, _, y2) in rectangles)
    y_bottombound = max(max(y1, y2) for (_, y1, _, y2) in rectangles)




    # Load the image to get dimensions
    image = img
    img_height, img_width = image.shape[:2]

    # Open the PDF and get page dimensions

    doc = fitz.open(pdf_path)
    page = doc[0]
    pdf_width, pdf_height = page.rect.width, page.rect.height

    # Coordinate scaling function
    def scale_coords(x, y):
        return (x / img_width) * pdf_width, (y / img_height) * pdf_height

    # Draw lines on PDF
    MAX_LEN = 12 // scale_factor #12 meters is the limit
    Y_OFFSET = 6
    X_OVERLAP = 40
    X_OFFSET = 6
    Y_OVERLAP = 40

    def get_rect_x_range(rects): #find the lowest and highest x values for the boxes
        x_values = [x for rect in rects for x in (rect[0], rect[2])]
        return min(x_values), max(x_values)

    def get_rect_y_range(rects):  # find the lowest and highest y values for the boxes
        y_values = [y for rect in rects for y in (rect[1], rect[3])]
        return min(y_values), max(y_values)

    x_min, x_max = get_rect_x_range(bounding_rects) #the minimum x and max x for the rectangles
    y_min, y_max = get_rect_y_range(bounding_rects)  # the minimum y and max y for the rectangles

    print("\nAnnotating diagram....")
    last_percent = -1 #initialize variable for progress printing


    key_h = 0
    # #PROCESS HORIZONTAL AXIS FIRST
    horizontal_color = (0.4, 0.4, 0.8)
    for key_h, group in groups_horizontal.items():

        #percentage completion tracking
        percent = (100*key_h//(len(groups_horizontal)+len(groups_vertical)))
        if percent % 20 == 0 and percent != last_percent:
            print(f"Progress: {percent}% complete")
            last_percent = percent
        
        lines, arrows, circles = OL.find_optimal_lines_horizontal(group, Y_OFFSET, X_OVERLAP, x_rightbound, x_leftbound, x_min, x_max, MAX_LEN)

        for line in lines:
            (x1, y), (x2, y) = line
            sx1, sy1 = scale_coords(x1, y)
            sx2, sy2 = scale_coords(x2, y)
            line = page.add_line_annot((sx1, sy1), (sx2, sy2))
            line.set_colors(stroke=horizontal_color)
            line.set_border(width=1.5)
            line.update()
            # note = page.insert_text((0.5*(sx1 + sx2), 0.5*(sy1+sy2)), str(key_h), fontsize = 6, color = (0, 0 ,1))

        
        for arrow in arrows:
            (x, y1), (_, y2) = arrow
            sx, sy1 = scale_coords(x, y1)
            _, sy2 = scale_coords(x, y2)

            DA.draw_vertical_arrow(page, sx, sy1, sy2, horizontal_color)

        
        for circle in circles:
            x, y, minimum_y, maximum_y = circle
            sx, sy = scale_coords(x, y)
            line_len = scale_coords(0, maximum_y)[1] - scale_coords(0, minimum_y)[1]
            DA.draw_circles(page, sx, sy, line_color = horizontal_color, line_length = line_len, line_width = 1)


        
        # # Label box indices
        # for idx, box in group:
        #     x1, y1, x2, y2 = box
        #     center_x = int((x1 + x2) / 2)
        #     center_y = int((y1 + y2) / 2)
        #     sx, sy = scale_coords(center_x, center_y)
            
        #     note = page.insert_text((sx, sy), f"{idx},{key_h}", fontsize=8, color=(1, 0, 0))
        #     # Writes the idx and group key

        #     # Draw rectangle
        #     sx1, sy1 = scale_coords(x1, y1)
        #     sx2, sy2 = scale_coords(x2, y2)
        #     rect = fitz.Rect(sx1, sy1, sx2, sy2)
            
        #     shape = page.new_shape()
        #     shape.draw_rect(rect)
        #     shape.finish(color=(0, 1, 0), fill=None, width=0.5)
        #     shape.commit()


    # PROCESS VERTICAL AXIS 

    vertical_color = (0.75, 0.25, 0.75)
    for key_v, group in groups_vertical.items():

        # percentage completion tracking
        percent = (100 * (key_v + key_h) // (len(groups_horizontal)+len(groups_vertical)))
        if percent % 20 == 0 and percent != last_percent:
            print(f"Progress: {percent}% complete")
            last_percent = percent

        # Find vertical lines and horizontal arrows
        lines, arrows, circles = OL.find_optimal_lines_vertical(group, X_OFFSET, Y_OVERLAP, y_topbound, y_bottombound, y_min, y_max, MAX_LEN)

        for line in lines:
            (x, y1), (x, y2) = line
            sx, sy1 = scale_coords(x, y1)
            _, sy2 = scale_coords(x, y2)
            line = page.add_line_annot((sx, sy1), (sx, sy2))
            line.set_colors(stroke=vertical_color)
            line.set_border(width=1.5)
            line.update()
            # note = page.insert_text((sx, 0.5*(sy1 + sy2)), str(key_v), fontsize=6, color=(0, 0, 1))

        for arrow in arrows:
            (x1, y), (x2, _) = arrow
            sx1, sy = scale_coords(x1, y)
            sx2, _ = scale_coords(x2, y)

            DA.draw_horizontal_arrow(page, sx1, sy, sx2, vertical_color)

        for circle in circles:
            x, y, minimum_x, maximum_x = circle
            sx, sy = scale_coords(x, y)
            line_len = scale_coords(maximum_x,0)[0] - scale_coords(minimum_x,0)[0]
            DA.draw_circles(page, sx, sy, line_color = vertical_color, line_length = line_len, line_width = 1)

        # # # Label box indices
        # for idx, box in group:
        #     x1, y1, x2, y2 = box
        #     center_x = int((x1 + x2) / 2)
        #     center_y = int((y1 + y2) / 2)
        #     sx, sy = scale_coords(center_x, center_y)
            
        #     note = page.insert_text((sx, sy), f"{idx},{key_h}", fontsize=8, color=(1, 0, 0))
        #     # Writes the idx and group key

        #     # Draw rectangle
        #     sx1, sy1 = scale_coords(x1, y1)
        #     sx2, sy2 = scale_coords(x2, y2)
        #     rect = fitz.Rect(sx1, sy1, sx2, sy2)
            
        #     shape = page.new_shape()
        #     shape.draw_rect(rect)
        #     shape.finish(color=(0, 1, 0), fill=None, width=0.5)
        #     shape.commit()













    # # Draw rectangles around all void_rects
    # for x1, y1, x2, y2 in void_rects:
    #     sx1, sy1 = scale_coords(x1, y1)
    #     sx2, sy2 = scale_coords(x2, y2)
    #     rect = fitz.Rect(sx1, sy1, sx2, sy2)
    #     shape = page.new_shape()
    #     shape.draw_rect(rect)
    #     shape.finish(color=(1, 0, 0), fill=None, width=0.5)  # Red outline for voids
    #     shape.commit()

    import os #lazy importing

    base_name = "ANNOTATED - " + os.path.basename(doc.name)[:-4]

    ext = ".pdf"
    counter = 0

    while True:
        output_path = f"{base_name}{'' if counter == 0 else f'_{counter}'}{ext}"
        try:
            doc.save(output_path)
            print(f"Saved as {output_path}")
            break
        except Exception as e:
            if "cannot remove file" in str(e).lower() or "permission denied" in str(e).lower():
                counter += 1
            else:
                raise e


    doc.close()
    print(f"\nAnnotated PDF saved as {output_path}")


    #open file
    os.startfile(output_path)




if __name__ == "__main__":
    process_pdf()