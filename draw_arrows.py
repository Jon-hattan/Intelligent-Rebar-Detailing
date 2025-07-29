import fitz  # PyMuPDF

# Function to draw a triangle arrowhead


def draw_arrowhead(annot, page, tip, direction='up', size=10, color=(1, 0, 0), line_width=1, opacity=1.0):
    x,y = tip
    if direction == 'up':
        p1 = (x, y)
        p2 = (x - size / 2, y + size)
        p3 = (x + size / 2, y + size)
    elif direction == 'down':
        p1 = (x, y)
        p2 = (x - size / 2, y - size)
        p3 = (x + size / 2, y - size)
    elif direction == 'left':
        p1 = (x, y)
        p2 = (x + size, y - size / 2)
        p3 = (x + size, y + size / 2)
    elif direction == 'right':
        p1 = (x, y)
        p2 = (x - size, y - size / 2)
        p3 = (x - size, y + size / 2)
    else:
        raise ValueError("Direction must be 'up', 'down', 'left', or 'right'")

    for start, end in [(p1, p2), (p2, p3), (p3, p1)]:
        triangle = page.add_line_annot(start, end)
        triangle.set_colors(stroke=color)
        triangle.set_border(width=line_width)
        triangle.set_opacity(opacity)
        triangle.update()



# Function to draw a vertical arrow with triangle arrowheads at both ends
def draw_vertical_arrow(page, x, y1, y2, line_color=(1, 0, 0), line_width=1):
    annot = page.add_line_annot((x, y1), (x, y2))
    annot.set_border(width=line_width)
    annot.set_colors(stroke=line_color)
    annot.update()

    arrow_size = min(10, abs(y2 - y1) // 3)
    draw_arrowhead(annot, page, (x, y1), direction='up', size=arrow_size, color=line_color)
    draw_arrowhead(annot, page, (x, y2), direction='down', size=arrow_size, color=line_color)

# Function to draw a horizontal arrow with triangle arrowheads at both ends
def draw_horizontal_arrow(page, x1, y, x2, line_color=(1, 0, 0), line_width=1):
    annot = page.add_line_annot((x1, y), (x2, y))
    annot.set_border(width=line_width)
    annot.set_colors(stroke=line_color)
    annot.update()

    arrow_size = min(10, abs(x2 - x1) // 3)
    draw_arrowhead(annot, page, (x1, y), direction='left', size=arrow_size, color=line_color)
    draw_arrowhead(annot, page, (x2, y), direction='right', size=arrow_size, color=line_color)



# # Example usage: draw arrows of varying size from 10 to 500

# # Create a new blank PDF
# doc = fitz.open()
# page = doc.new_page()


# x_start = 50
# x_gap = 20
# for height in range(10, 510, 5):
#     x = x_start + (height // 5) * x_gap
#     y1 = 100
#     y2 = y1 + height
#     draw_vertical_arrow(page, x, y1, y2, line_color = (0.75, 0.25, 0.75))

# # Save the PDF
# output_path = "varying_arrow_sizes.pdf"
# doc.save(output_path)
# doc.close()

# print(f"PDF with varying arrow sizes saved as {output_path}")

