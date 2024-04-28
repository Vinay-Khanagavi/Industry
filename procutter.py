import fitz  # PyMuPDF

from tkinter import *
from tkinter import filedialog

class PDFEditor:
    def __init__(self, root):
        self.root = root

        self.canvas = Canvas(self.root, width=800, height=600, bg='white')
        self.canvas.pack(expand=YES, fill=BOTH)

        self.shapes = []
        self.selected_shape = None

        self.load_pdf_button = Button(self.root, text="Load PDF", command=self.load_pdf)
        self.load_pdf_button.pack()

        self.canvas.bind("<Button-1>", self.select_shape)
        self.canvas.bind("<B1-Motion>", self.move_shape)

    def load_pdf(self):
        pdf_file = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if pdf_file:
            self.load_shapes_from_pdf(pdf_file)
            self.draw_shapes()

    def load_shapes_from_pdf(self, pdf_file):
        self.doc = fitz.open(pdf_file)
        self.shapes = []

        for page_num in range(len(self.doc)):
            page = self.doc.load_page(page_num)

            # Extract rectangles, squares, and circles (just for demonstration, you may need to handle more shape types)
            for annot in page.annots():
                if annot.type[0] == 3:  # Check if the annotation is a square or rectangle
                    bbox = annot.rect
                    self.shapes.append({'page': page_num, 'type': 'rectangle', 'bbox': bbox})
                elif annot.type[0] == 4:  # Check if the annotation is a circle
                    bbox = annot.rect
                    self.shapes.append({'page': page_num, 'type': 'circle', 'bbox': bbox})

    def draw_shapes(self):
        self.canvas.delete("all")
        for shape in self.shapes:
            x0, y0, x1, y1 = shape['bbox']
            if shape['type'] == 'rectangle':
                self.canvas.create_rectangle(x0, y0, x1, y1, outline='blue', tags=('shape',))
            elif shape['type'] == 'circle':
                self.canvas.create_oval(x0, y0, x1, y1, outline='red', tags=('shape',))

    def select_shape(self, event):
        x, y = event.x, event.y
        shapes = self.canvas.find_overlapping(x, y, x, y)
        if shapes:
            self.selected_shape = shapes[-1]  # Select the topmost shape
            self.canvas.tag_raise(self.selected_shape)

    def move_shape(self, event):
        if self.selected_shape:
            x, y = event.x, event.y
            bbox = self.canvas.bbox(self.selected_shape)
            dx, dy = x - bbox[0], y - bbox[1]
            self.canvas.move(self.selected_shape, dx, dy)
            shape_index = self.canvas.find_withtag('shape').index(self.selected_shape)
            self.shapes[shape_index]['bbox'] = [x, y, x + (bbox[2] - bbox[0]), y + (bbox[3] - bbox[1])]

    def save_pdf(self):
        output_pdf = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if output_pdf:
            writer = fitz.open()
            for page_num in range(len(self.doc)):
                page = self.doc.load_page(page_num)
                for shape in self.shapes:
                    if shape['page'] == page_num:
                        page.insert_rect(shape['bbox'], width=0, color=(0, 0, 0))
                writer.insert_pdf(page_num, page)
            writer.save(output_pdf)

if __name__ == "__main__":
    root = Tk()
    app = PDFEditor(root)
    save_button = Button(root, text="Save as PDF", command=app.save_pdf)
    save_button.pack()
    root.mainloop()