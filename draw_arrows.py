import fitz  # PyMuPDF

# Function to draw a triangle arrowhead

def draw_arrowhead(page, tip, direction='up', size=10, color=(1, 0, 0), width=1, opacity=1.0):
    if size < 3:
        if direction == 'up':
            annot.set_line_ends(5, 0)  # arrowhead at top end (0=none, 5=open arrow, 6=closed arrow, etc.)
        elif direction == 'down':
            annot.set_line_ends(0, 5)
        annot.update()
    else:
        x, y = tip
        if direction == 'up':
            p1 = (x, y)
            p2 = (x - size / 2, y + size)
            p3 = (x + size / 2, y + size)
        elif direction == 'down':
            p1 = (x, y)
            p2 = (x - size / 2, y - size)
            p3 = (x + size / 2, y - size)
        else:
            raise ValueError("Only 'up' and 'down' directions are supported")

        # Create three line annotations to form a triangle
        for start, end in [(p1, p2), (p2, p3), (p3, p1)]:
            annot = page.add_line_annot(start, end)
            annot.set_colors(stroke=color)
            annot.set_border(width=width)
            annot.set_opacity(opacity)
            annot.update()


# Function to draw a vertical arrow with triangle arrowheads at both ends
def draw_vertical_arrow(page, x, y1, y2, line_color=(1, 0, 0), line_width=2):
    # Draw the vertical line
    # Add line annotation with arrowheads
    annot = page.add_line_annot((x,y1), (x,y2))
    annot.set_border(width=line_width)  # optional: set line thickness
    annot.set_colors(stroke=line_color)  # red arrow
    annot.update()

    # Draw arrowheads
    arrow_size = min(10, (y2-y1)//3)
    draw_arrowhead(page, (x, y1), direction='up', size=arrow_size, color=line_color)
    draw_arrowhead(page, (x, y2), direction='down', size=arrow_size, color = line_color)


# Example usage: draw arrows of varying size from 10 to 500

# Create a new blank PDF
doc = fitz.open()
page = doc.new_page()


x_start = 50
x_gap = 20
for height in range(10, 510, 5):
    x = x_start + (height // 5) * x_gap
    y1 = 100
    y2 = y1 + height
    draw_vertical_arrow(page, x, y1, y2)

# Save the PDF
output_path = "varying_arrow_sizes.pdf"
doc.save(output_path)
doc.close()

print(f"PDF with varying arrow sizes saved as {output_path}")

