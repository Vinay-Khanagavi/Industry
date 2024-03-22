import sys
from tkinter import filedialog

from altair import Shape
from matplotlib.patches import Rectangle
from sympy import Circle
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QMessageBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import ezdxf

from procutter import Sheet

class SteelSheetApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Steel Sheet Optimization")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()

        # Input fields
        layout.addWidget(QLabel("Enter Sheet Dimensions:"))
        self.sheet_length_entry = QLineEdit()
        layout.addWidget(self.create_input_fields("Length:", self.sheet_length_entry))

        self.sheet_width_entry = QLineEdit()
        layout.addWidget(self.create_input_fields("Width:", self.sheet_width_entry))

        self.num_circles_entry = QLineEdit()
        layout.addWidget(self.create_input_fields("Number of Circles:", self.num_circles_entry))

        self.circle_diameter_entry = QLineEdit()
        layout.addWidget(self.create_input_fields("Circle Diameter:", self.circle_diameter_entry))

        self.num_rectangles_entry = QLineEdit()
        layout.addWidget(self.create_input_fields("Number of Rectangles:", self.num_rectangles_entry))

        self.rect_width_entry = QLineEdit()
        layout.addWidget(self.create_input_fields("Rectangle Width:", self.rect_width_entry))

        self.rect_height_entry = QLineEdit()
        layout.addWidget(self.create_input_fields("Rectangle Height:", self.rect_height_entry))

        # Buttons
        optimize_button = QPushButton("Optimize Steel Sheet")
        optimize_button.clicked.connect(self.get_user_input)
        layout.addWidget(optimize_button)

        self.central_widget.setLayout(layout)

    def create_input_fields(self, label_text, line_edit):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label_text))
        layout.addWidget(line_edit)
        return layout

    def save_as_dxf(self, shapes_positions):
        doc = ezdxf.new()
        msp = doc.modelspace()

        for shape, (x, y) in shapes_positions.items():
            if shape.shape_type == 'rectangle':
                msp.add_lwpolyline(
                    [(y, x), (y + shape.width, x), (y + shape.width, x + shape.height), (y, x + shape.height), (y, x)],
                    is_closed=True
                )
            elif shape.shape_type == 'circle':
                msp.add_circle(
                    center=(y + shape.width / 2, x + shape.width / 2),
                    radius=shape.width / 2
                )

        filename, _ = filedialog.getSaveFileName(self, 'Save File', '', "DXF files (*.dxf)")
        if filename:
            doc.saveas(filename)

    def pack_shapes_on_sheet(self, shapes, sheet_length, sheet_width):
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

    def visualize_result(self, shapes_positions, sheet_length, sheet_width):
        fig = Figure(figsize=(5, 5), dpi=100)
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.set_xlim(0, sheet_width)
        ax.set_ylim(0, sheet_length)
        ax.set_aspect('equal', adjustable='box')

        for shape, (x, y) in shapes_positions.items():
            if shape.shape_type == 'rectangle':
                rect = Rectangle((y, x), shape.width, shape.height, linewidth=1, edgecolor='black', facecolor='none')
                ax.add_patch(rect)
            elif shape.shape_type == 'circle':
                circle = Circle((y + shape.width / 2, x + shape.width / 2), shape.width / 2,
                                edgecolor='black', facecolor='none')
                ax.add_patch(circle)

        self.setCentralWidget(canvas)

    def get_user_input(self):
        shapes_to_pack = []
        try:
            num_circles = int(self.num_circles_entry.text())
            for _ in range(num_circles):
                circle_diameter = int(self.circle_diameter_entry.text())
                shapes_to_pack.append(Shape("circle", circle_diameter))

            num_rectangles = int(self.num_rectangles_entry.text())
            for _ in range(num_rectangles):
                rect_width = int(self.rect_width_entry.text())
                rect_height = int(self.rect_height_entry.text())
                shapes_to_pack.append(Shape("rectangle", rect_width, rect_height))

            sheet_length = int(self.sheet_length_entry.text())
            sheet_width = int(self.sheet_width_entry.text())

            positions = self.pack_shapes_on_sheet(shapes_to_pack, sheet_length, sheet_width)
            self.visualize_result(positions, sheet_length, sheet_width)
            self.save_as_dxf(positions)
        except ValueError:
            QMessageBox.warning(self, 'Input Error', 'Invalid input. Please enter numeric values.')

if __name__ == '__main__':
    app = QApplication([])
    window = SteelSheetApp()
    window.show()
    sys.exit(app.exec_())
