
import fitz  # PyMuPDF
import random
import os

# Page and layout settings
page_width, page_height = fitz.paper_size("a4")
margin = 40
beam_thickness = 8
column_size = 10
beam_color = (0.7, 0.7, 0.7)  # Grey
column_color = (0, 0, 0)      # Black

# Create a new PDF
doc = fitz.open()
page = doc.new_page(width=page_width, height=page_height)

# Define the outer rectangle
outer_rect = fitz.Rect(margin, margin, page_width - margin, page_height - margin)

# Draw outer beams
page.draw_rect(outer_rect, color=beam_color, fill=None, width=beam_thickness)

# List to store column positions
column_positions = []

# List to store dashed rectangles
dashed_rectangles = []

# Function to draw a rectangle with beams and store column positions
def draw_cell(rect):
    # Draw beams (rectangle border)
    page.draw_rect(rect, color=beam_color, fill=None, width=beam_thickness)
    # Store column positions (corners)
    for x in [rect.x0, rect.x1]:
        for y in [rect.y0, rect.y1]:
            column_positions.append((x, y))

    # Randomly decide to draw a dashed box in a corner
    if random.random() < 0.3:  # 30% chance
        min_dashed_size = 30
        max_width = rect.width / 2
        max_height = rect.height / 2
        if max_width > min_dashed_size and max_height > min_dashed_size:
            dw = random.uniform(min_dashed_size, max_width)
            dh = random.uniform(min_dashed_size, max_height)
            corner = random.choice(['tl', 'tr', 'bl', 'br'])
            if corner == 'tl':
                dashed_rect = (rect.x0 + 2, rect.y0 + 2, rect.x0 + dw, rect.y0 + dh)
            elif corner == 'tr':
                dashed_rect = (rect.x1 - dw, rect.y0 + 2, rect.x1 - 2, rect.y0 + dh)
            elif corner == 'bl':
                dashed_rect = (rect.x0 + 2, rect.y1 - dh, rect.x0 + dw, rect.y1 - 2)
            else:  # 'br'
                dashed_rect = (rect.x1 - dw, rect.y1 - dh, rect.x1 - 2, rect.y1 - 2)
            
            dashed_rectangles.append(dashed_rect)

# Function to draw dashed boxes with diagonals
def draw_dashed_boxes_on_pdf(rectangles):
    dash_pattern = "[4] 0"
    for rect in rectangles:
        x1, y1, x2, y2 = rect
        shape1 = page.new_shape()
        shape1.draw_rect(fitz.Rect(x1, y1, x2, y2))
        shape1.finish(width=1, color=(0, 0, 0), dashes=dash_pattern)
        shape1.commit()

        shape2 = page.new_shape()
        shape2.draw_line(fitz.Point(x1, y2), fitz.Point(x2, y1))  # Bottom-left to top-right
        shape2.finish(width=1, color=(0, 0, 0), dashes=dash_pattern)
        shape2.commit()

        shape3 = page.new_shape()
        shape3.draw_line(fitz.Point(x1, y1), fitz.Point(x2, y2))  # Top-left to bottom-right
        shape3.finish(width=1, color=(0, 0, 0), dashes=dash_pattern)
        shape3.commit()

# Recursive subdivision of the outer rectangle
def subdivide(rect, depth=0):
    min_width = 60
    min_height = 60
    if rect.width < 2 * min_width or rect.height < 2 * min_height or depth > 5:
        draw_cell(rect)
        return

    if rect.width > rect.height:
        split = random.uniform(rect.x0 + min_width, rect.x1 - min_width)
        left = fitz.Rect(rect.x0, rect.y0, split, rect.y1)
        right = fitz.Rect(split, rect.y0, rect.x1, rect.y1)
        subdivide(left, depth + 1)
        subdivide(right, depth + 1)
    else:
        split = random.uniform(rect.y0 + min_height, rect.y1 - min_height)
        top = fitz.Rect(rect.x0, rect.y0, rect.x1, split)
        bottom = fitz.Rect(rect.x0, split, rect.x1, rect.y1)
        subdivide(top, depth + 1)
        subdivide(bottom, depth + 1)

# Start subdivision inside the outer rectangle
subdivide(outer_rect)

# Draw dashed boxes after subdivision
draw_dashed_boxes_on_pdf(dashed_rectangles)

# Draw all columns on top
for x, y in column_positions:
    page.draw_rect(fitz.Rect(x - column_size/2, y - column_size/2,
                             x + column_size/2, y + column_size/2),
                   color=column_color, fill=column_color)


base_name = "structural_floor_plan"
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
os.startfile(output_path)
