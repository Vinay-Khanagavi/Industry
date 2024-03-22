import tkinter as tk
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle, Circle
import ezdxf
from tkinter import filedialog
from matplotlib.backends.backend_pdf import PdfPages

def save_as_pdf(shapes_positions, sheet_length, sheet_width):
    pdf_filename = "output.pdf"
    if pdf_filename:
        with PdfPages(pdf_filename) as pdf:
            fig, ax = plt.subplots()
            ax.set_xlim(0, sheet_width)
            ax.set_ylim(0, sheet_length)
            ax.set_aspect('equal', adjustable='box')

            for shape, (x, y) in shapes_positions.items():
                if shape.shape_type == 'rectangle':
                    rect = Rectangle((y, x), shape.width, shape.height, linewidth=1, edgecolor='black', facecolor='none')
                    ax.add_patch(rect)
                elif shape.shape_type == 'circle':
                    circle = Circle((y + shape.width / 2, x + shape.width / 2), shape.width / 2, edgecolor='black', facecolor='none')
                    ax.add_patch(circle)
                elif shape.shape_type == 'square':
                    square = Rectangle((y, x), shape.width, shape.height, linewidth=1, edgecolor='black', facecolor='none')
                    ax.add_patch(square)

            pdf.savefig(fig)

def save_as_dxf(shapes_positions):
    doc = ezdxf.new()
    msp = doc.modelspace()

    for shape, (x, y) in shapes_positions.items():
        if shape.shape_type == 'rectangle':
            points = [
                (y, x), (y + shape.width, x), (y + shape.width, x + shape.height),
                (y, x + shape.height), (y, x)  # Closing the shape
            ]
            msp.add_lwpolyline(points)
        elif shape.shape_type == 'circle':
            msp.add_circle(
                center=(y + shape.width / 2, x + shape.width / 2),
                radius=shape.width / 2
            )

    filename = "output.dxf"
    if filename:
        doc.saveas(filename)
class Shape:
    def __init__(self, shape_type, width, height=None):
        self.shape_type = shape_type
        self.width = width
        self.height = height if height else width

class Sheet:
    def __init__(self, length, width):
        self.length = length
        self.width = width
        self.sheet = [[0 for _ in range(width)] for _ in range(length)]
        self.space = 1

    def place_shape(self, x, y, shape):
        for i in range(shape.height + self.space):
            for j in range(shape.width  + self.space):
                self.sheet[x + i][y + j] = 1

    def is_valid_location(self, x, y, shape):
        for i in range(shape.height):
            for j in range(shape.width):
                if x + i >= self.length or y + j >= self.width or self.sheet[x + i][y + j] == 1:
                    return False
        return True

    def find_empty_space(self, shape):
        for i in range(self.length - shape.height + 1):
            for j in range(self.width - shape.width + 1):
                if self.is_valid_location(i, j, shape):
                    return i, j
        return -1, -1
    
def pack_shapes_on_sheet(shapes, sheet_length, sheet_width):
    sheet = Sheet(sheet_length, sheet_width)
    shapes_positions = {}
    for shape in shapes:
        x, y = sheet.find_empty_space(shape)
        if x != -1 and y != -1:
            sheet.place_shape(x, y, shape)
            shapes_positions[shape] = (x, y)
            print(f"Placed {shape.shape_type} at position ({x}, {y})")
        else:
            print(f"No space available for {shape.shape_type}")
    return shapes_positions

def visualize_result_numbering(shapes_positions, sheet_length, sheet_width):
    fig, ax = plt.subplots()
    ax.set_xlim(0, sheet_width)
    ax.set_ylim(0, sheet_length)
    ax.set_aspect('equal', adjustable='box')

    # Create a dictionary to track counts for each unique shape size
    size_count_dict = {'circle': {}, 'rectangle': {}, 'square': {}}

    # Create a counter for each shape type to assign unique numbers
    shape_counters = {'circle': 0, 'rectangle': 0, 'square': 0}

    for shape, (x, y) in shapes_positions.items():
        shape_key = (shape.shape_type, shape.width, shape.height)

        # Check if the shape's size has already been encountered
        if shape_key in size_count_dict[shape.shape_type]:
            count = size_count_dict[shape.shape_type][shape_key]
        else:
            # Increment the counter for this shape type and size
            shape_counters[shape.shape_type] += 1
            count = shape_counters[shape.shape_type]

            # Store this count for this particular shape size
            size_count_dict[shape.shape_type][shape_key] = count

        if shape.shape_type == 'rectangle':
            rect = Rectangle((y, x), shape.width, shape.height, linewidth=1, edgecolor='black', facecolor='none')
            ax.add_patch(rect)
            plt.text(y + shape.width / 2, x + shape.height / 2, f' {count}', ha='center', va='center')
        elif shape.shape_type == 'circle':
            circle = Circle((y + shape.width / 2, x + shape.width / 2), shape.width / 2, edgecolor='black', facecolor='none')
            ax.add_patch(circle)
            plt.text(y + shape.width / 2, x + shape.width / 2, f' {count}', ha='center', va='center')
        elif shape.shape_type == 'square':
            square = Rectangle((y, x), shape.width, shape.height, linewidth=1, edgecolor='black', facecolor='none')
            ax.add_patch(square)
            plt.text(y + shape.width / 2, x + shape.height / 2, f' {count}', ha='center', va='center')

    plt.show()

def visualize_result(shapes_positions, sheet_length, sheet_width):
    fig, ax = plt.subplots()
    ax.set_xlim(0, sheet_width)
    ax.set_ylim(0, sheet_length)
    ax.set_aspect('equal', adjustable='box')

    for shape, (x, y) in shapes_positions.items():
        if shape.shape_type == 'rectangle':
            rect = Rectangle((y, x), shape.width, shape.height, linewidth=1, edgecolor='black', facecolor='none')
            ax.add_patch(rect)
        elif shape.shape_type == 'circle':
            circle = Circle((y + shape.width / 2, x + shape.width / 2), shape.width / 2, edgecolor='black', facecolor='none')
            ax.add_patch(circle)
        elif shape.shape_type == 'square':
            square = Rectangle((y, x), shape.width, shape.height, linewidth=1, edgecolor='black', facecolor='none')
            ax.add_patch(square)

    plt.show()

def get_user_input():
    shapes_to_pack = []
    
    # Get number of circles from user input
    num_circles = int(num_circles_entry.get())
    for _ in range(num_circles):
        # Get circle diameter for each circle
        circle_diameter = int(circle_diameter_entry.get())
        shapes_to_pack.append(Shape("circle", circle_diameter))
    
    # Get number of rectangles from user input
    num_rectangles = int(num_rectangles_entry.get())
    for _ in range(num_rectangles):
        # Get rectangle width and height for each rectangle
        rect_width = int(rectangle_width_entry.get())
        rect_height = int(rectangle_height_entry.get())
        shapes_to_pack.append(Shape("rectangle", rect_width, rect_height))
    
    # Get number of squares from user input
    num_squares = int(num_squares_entry.get())
    for _ in range(num_squares):
        # Get square side for each square
        square_side = int(square_side_entry.get())
        shapes_to_pack.append(Shape("square", square_side, square_side))
    
    sheet_length = int(sheet_length_entry.get())
    sheet_width = int(sheet_width_entry.get())

    positions = pack_shapes_on_sheet(shapes_to_pack, sheet_length, sheet_width)
    visualize_result_numbering(positions, sheet_length, sheet_width)

    save_button_dxf = tk.Button(root, text="Save as DXF", command=lambda: save_as_dxf(positions))
    save_button_dxf.pack()

    save_button_pdf = tk.Button(root, text="Save as PDF", command=lambda: save_as_pdf(positions, sheet_length, sheet_width))
    save_button_pdf.pack()

# Tkinter GUI setup
root = tk.Tk()
root.title("Steel Sheet Optimization")

# Label and entry for sheet dimensions
sheet_label = tk.Label(root, text="Enter Sheet Dimensions:")
sheet_label.pack()

sheet_length_label = tk.Label(root, text="Length:")
sheet_length_label.pack()
sheet_length_entry = tk.Entry(root)
sheet_length_entry.pack()

sheet_width_label = tk.Label(root, text="Width:")
sheet_width_label.pack()
sheet_width_entry = tk.Entry(root)
sheet_width_entry.pack()

# Label and entry for number of circles
num_circles_label = tk.Label(root, text="Number of Circles:")
num_circles_label.pack()
num_circles_entry = tk.Entry(root)
num_circles_entry.pack()

# Label and entry for circle diameter
circle_diameter_label = tk.Label(root, text="Circle Diameter:")
circle_diameter_label.pack()
circle_diameter_entry = tk.Entry(root)
circle_diameter_entry.pack()

# Label and entry for number of rectangles
num_rectangles_label = tk.Label(root, text="Number of Rectangles:")
num_rectangles_label.pack()
num_rectangles_entry = tk.Entry(root)
num_rectangles_entry.pack()

# Label and entry for rectangle width
rectangle_width_label = tk.Label(root, text="Rectangle Width:")
rectangle_width_label.pack()
rectangle_width_entry = tk.Entry(root)
rectangle_width_entry.pack()

# Label and entry for rectangle height
rectangle_height_label = tk.Label(root, text="Rectangle Height:")
rectangle_height_label.pack()
rectangle_height_entry = tk.Entry(root)
rectangle_height_entry.pack()

# Label and entry for number of squares
num_squares_label = tk.Label(root, text="Number of Squares:")
num_squares_label.pack()
num_squares_entry = tk.Entry(root)
num_squares_entry.pack()

# Label and entry for square side
square_side_label = tk.Label(root, text="Square Side:")
square_side_label.pack()
square_side_entry = tk.Entry(root)
square_side_entry.pack()

# Button to start optimization
optimize_button = tk.Button(root, text="Optimize Steel Sheet", command=get_user_input)
optimize_button.pack()

root.mainloop()