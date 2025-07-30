import fitz  # PyMuPDF
import random

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

# Function to draw a rectangle with beams and columns
def draw_cell(rect):
    # Draw beams (rectangle border)
    page.draw_rect(rect, color=beam_color, fill=None, width=beam_thickness)
    # Draw columns (black squares) at corners
    for x in [rect.x0, rect.x1]:
        for y in [rect.y0, rect.y1]:
            page.draw_rect(fitz.Rect(x - column_size/2, y - column_size/2,
                                     x + column_size/2, y + column_size/2),
                           color=column_color, fill=column_color)

# Recursive subdivision of the outer rectangle
def subdivide(rect, depth=0):
    min_width = 30
    min_height = 30
    if rect.width < 2 * min_width or rect.height < 2 * min_height or depth > 5:
        draw_cell(rect)
        return

    # Decide whether to split vertically or horizontally
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


import os #lazy importing

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
