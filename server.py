from io import BytesIO
import os
from zipfile import ZipFile
from PyPDF2 import PdfMerger
from fastapi import FastAPI, File, UploadFile
from typing import List
from fastapi.responses import FileResponse, StreamingResponse
from fpdf import FPDF
from matplotlib import pyplot as plt
from pydantic import BaseModel
from matplotlib.patches import Rectangle, Circle
from matplotlib.backends.backend_pdf import PdfPages
import ezdxf
from fastapi.middleware.cors import CORSMiddleware  # Import CORS middleware

pdf_count = 0
dxf_count = 0
merge_pdfs_count = 0
output_count = 0
detailed_output_count = 0
table_count = 0


class Data(BaseModel):
    shape_type: str
    width: int
    height: int = None
    part_no: str = None
    part_description: str = None
    part_code: str = None
    material_spec: str = None
    size_of_material: str = None
    quantity: int = None
    unit: str = None

class Shape:
    def __init__(self, shape_type, width, height=None, part_no=None, part_description=None, part_code=None,
                    material_spec=None, size_of_material=None, quantity=None, unit=None):
        self.shape_type = shape_type
        self.width = width
        self.height = height if height is not None else width
        self.part_no = part_no
        self.part_description = part_description
        self.part_code = part_code
        self.material_spec = material_spec
        self.size_of_material = size_of_material
        self.quantity = quantity
        self.unit = unit

    def __str__(self):
        return f"Shape Type: {self.shape_type}, Width: {self.width}, Height: {self.height}, " \
                f"Part No: {self.part_no}, Part Description: {self.part_description}, " \
                f"Part Code: {self.part_code}, Material Spec: {self.material_spec}, " \
                f"Size of Material: {self.size_of_material}, Quantity: {self.quantity}, Unit: {self.unit}"

class Sheet:
    def __init__(self, length, width, spacing):
        self.length = length
        self.width = width
        self.sheet = [[0 for _ in range(width)] for _ in range(length)]
        self.space = spacing
        self.remaining = []
    def place_shape(self, x, y, shape):
        for i in range(shape.height + self.space):
            for j in range(shape.width + self.space):
                self.sheet[x + i][y + j] = 1
    
    def is_valid_location(self, x, y, shape :Shape):
        for i in range(shape.height ):
            for j in range(shape.width):
                if x + i >= self.length or y + j >= self.width or self.sheet[x + i][y + j] == 1:
                    return False
        return True
    def find_empty_space(self, shape:Shape, start_x=0, end_x=None, start_y=0, end_y=None):
        if end_x is None:
            end_x = self.length - shape.height - self.space + 1
        if end_y is None:
            end_y = self.width - shape.width - self.space + 1
        while start_y < end_y:
            while start_x < end_x:
                if self.is_valid_location(start_x, start_y, shape):
                    return start_x, start_y
                start_x += 1
            start_y += 1
            start_x = 0  # Reset start_x for the next column
        return -1, -1  # Return if no empty space found



    def print(self):
        for i in range(self.width):
            for j in range(self.length):
                print(str(self.sheet[i][j]) , end="")
            print("")

def merge_pdfs(pdf_files):
    
    global merge_pdfs_count
    merge_pdfs_count += 1
    output_file = "merged" + str(merge_pdfs_count) + ".pdf"
    
    # Create a PDF merger object
    merger = PdfMerger()
    
    for file in pdf_files:
        merger.append(file)
    # Write the merged PDF to a file
    merger.write(output_file)
    # Close the merger
    merger.close()

def create_pdf_with_table(shapes_positions: dict):
    pdf = FPDF(
        orientation='L'
    )
    column_headers = [
        'PART NO.',
        'PART DESCRIPTION',
        'MATERIAL SPECIFICATION',
        'SIZE OF MATERIAL',
        'QTY.',
        'TYPE'
    ]
    pdf.add_page()
    col_widths = [20, 70, 60, 60, 40, 20, 18]  # Adjust column widths as needed
    # Add header outside the loop
    pdf.set_font("Arial", 'B', 12)
    for header, width in zip(column_headers, col_widths):
        pdf.cell(width, 10, header, 1, 0, 'C')
    pdf.ln()

    pdf.set_font("Arial", '', 10)

    shape_counts = {} 
    shapes = []  # List to track unique shapes

    shpae_count = 0
    
    for shape, (x, y) in shapes_positions.items():
        # Generate a unique key based on size and material
        key = (shape.width, shape.height, shape.material_spec, shape.size_of_material, shape.shape_type)

        # Check if the shape has already been encountered
        if key in shape_counts:
            shape_counts[key] += 1
        else:
            shape_counts[key] = 1
            shapes.append(shape)

            # Assuming each shape has corresponding data; adjust this part according to your data structure
            
            
    for shape in shapes:
        key = (shape.width, shape.height, shape.material_spec, shape.size_of_material, shape.shape_type)

        data_for_shape = [
            str(shape_counts[key]),  # Update numbering based on count
            shape.part_description,
            shape.material_spec,
            shape.size_of_material,
            shape_counts[key],  # Update quantity based on count
            shape.shape_type
        ]

        for item, width in zip(data_for_shape, col_widths):
            pdf.cell(width, 10, str(item), 1, 0, 'C')
        pdf.ln()
    print(shape_counts)

    global table_count
    table_count += 1

    pdf_output = "output_detailed" + str(table_count) + ".pdf"

    pdf.output(pdf_output)
    print(f"PDF with tables saved as '{pdf_output}'")


def group_shapes(shapes):
    grouped_shapes = {}
    for shape in shapes:
        key = (shape.width, shape.height, shape.shape_type)
        if key not in grouped_shapes:
            grouped_shapes[key] = []
        grouped_shapes[key].append(shape)
    return grouped_shapes

def first_fit_decreasing(shapes):
    shapes.sort(key=lambda shape: max(shape.width, shape.height), reverse=True)
    return shapes

def next_fit_decreasing(shapes):
    shapes.sort(key=lambda shape: shape.height, reverse=True)
    return shapes

def pack_shapes_on_sheet(grouped_shapes, sheet_length, sheet_width, spacing):
    sheet = Sheet(sheet_length, sheet_width, spacing)
    shapes_positions = {}
    remaining = {}
    current_x = 0  # Track the current column

    for key, shapes_list in grouped_shapes.items():
        for shape in shapes_list:
            x, y = sheet.find_empty_space(shape, start_x=current_x)
            if x != -1 and y != -1:
                # Check if placing the shape will reach the end of the top
                if y + shape.width + spacing >= sheet_width:
                    current_x += 1  # Move to the next column
                    x, y = sheet.find_empty_space(shape, start_x=current_x)

                if x != -1 and y != -1:
                    sheet.place_shape(x + spacing, y + spacing, shape)
                    shapes_positions[shape] = (x, y)
                    print(f"Placed {shape.shape_type} at position ({x}, {y})")
                else:
                    if key not in remaining:
                        remaining[key] = []
                    remaining[key].append(shape)
                    print(f"No space available for {shape.shape_type}")

    return sheet, shapes_positions, remaining

def calculate_sheet_utilization(sheet: Sheet, shapes_positions: dict):
    total_cells = sheet.length * sheet.width
    occupied_cells = 0

    for shape, (x, y) in shapes_positions.items():
        occupied_cells += (shape.width + sheet.space) * (shape.height + sheet.space)

    wastage_percentage = ((total_cells - occupied_cells) / total_cells) * 100
    occupation_percentage = (occupied_cells / total_cells) * 100

    return wastage_percentage, occupation_percentage

def save_visualization_as_pdf(shapes_positions, sheet_length, sheet_width):
    global detailed_output_count
    detailed_output_count += 1

    filename = "output_file" + str(detailed_output_count) + ".pdf"
    with PdfPages(filename) as pdf:
        fig, ax = plt.subplots()
        ax.set_xlim(0, sheet_width)
        ax.set_ylim(0, sheet_length)
        ax.set_aspect('equal', adjustable='box')

        # Create a dictionary to track counts for each unique shape size
        size_count_dict = {'circle': {}, 'rectangle': {}, 'square': {}}

        # Create a single counter for all shapes
        shape_counter = 0
        for shape, (x, y) in shapes_positions.items():
            if shape.shape_type == 'circle':
                # Include only the radius in the shape key for circles
                shape_key = (shape.width / 2,)
            else:
                shape_key = (shape.width, shape.height)

            # Check if the shape's size has already been encountered
            if shape_key in size_count_dict[shape.shape_type]:
                count = size_count_dict[shape.shape_type][shape_key]
            else:
                shape_counter += 1
                count = shape_counter
                # Store this count for this particular shape size
                size_count_dict[shape.shape_type][shape_key] = count

            if shape.shape_type == 'rectangle':
                rect = Rectangle((y, x), shape.width, shape.height, linewidth=1, edgecolor='black', facecolor='none')
                ax.add_patch(rect)
                plt.text(y + shape.width / 2, x + shape.height / 2, f' {count}', ha='center', va='center', fontsize=8)
            elif shape.shape_type == 'circle':
                circle = Circle((y + shape.width / 2, x + shape.width / 2), shape.width / 2, edgecolor='black',
                                facecolor='none')
                ax.add_patch(circle)
                plt.text(y + shape.width / 2, x + shape.width / 2, f' {count}', ha='center', va='center',
                            fontsize=8)
            elif shape.shape_type == 'square':
                square = Rectangle((y, x), shape.width, shape.height, linewidth=1, edgecolor='black', facecolor='none')
                ax.add_patch(square)
                plt.text(y + shape.width / 2, x + shape.height / 2, f' {count}', ha='center', va='center',
                            fontsize=8)
        print(size_count_dict)
        pdf.savefig(fig)

        

def save_as_pdf(shapes_positions, sheet_length, sheet_width  ):
    global pdf_count 
    pdf_count += 1

    pdf_filename = "output"+ str(pdf_count) +".pdf"

    if pdf_filename:
        with PdfPages(pdf_filename) as pdf:
            fig, ax = plt.subplots()
            ax.set_xlim(0, sheet_width)
            ax.set_ylim(0, sheet_length)
            ax.set_aspect('equal', adjustable='box')

            for shape, (x, y) in shapes_positions.items():
                if shape.shape_type == 'rectangle':
                    rect = Rectangle((y , x), shape.width  , shape.height , linewidth=1, edgecolor='black', facecolor='none' )
                    ax.add_patch(rect)
                elif shape.shape_type == 'circle':
                    circle = Circle((y + shape.width / 2, x + shape.width / 2), shape.width / 2, edgecolor='black', facecolor='none')
                    ax.add_patch(circle)
                elif shape.shape_type == 'square':
                    square = Rectangle((y, x), shape.width, shape.height, linewidth=1, edgecolor='black', facecolor='none')
                    ax.add_patch(square)

            pdf.savefig(fig)

def save_as_dxf(shapes_positions  ):
    global dxf_count
    dxf_count += 1

    filename = "output"+ str(dxf_count)+".dxf"

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

    filenamee = filename
    if filenamee:
        doc.saveas(filenamee)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)



remaining_shapes = []
pdf_filename = "output.pdf"  # Provide the filename for PDF
dxf_filename = "output.dxf"  # Provide the filename for DXF

@app.post("/generate_files")
async def generate_files(shapes: List[Data], sheet_length: int, sheet_width: int, spacing: int):
    shapes_to_pack = []

    # Convert input Data objects to Shape instances
    for shape_data in shapes:
        for _ in range(shape_data.quantity):
            shapes_to_pack.append(Shape(
                shape_type=shape_data.shape_type,
                width=shape_data.width,
                height=shape_data.height if shape_data.height else shape_data.width,
                part_no=shape_data.part_no,  # Pass the part number here
                part_description=shape_data.part_description,
                part_code=shape_data.part_code,
                material_spec=shape_data.material_spec,
                size_of_material=shape_data.size_of_material,
                quantity=1,  # Each shape is now considered as a single instance
                unit=shape_data.unit
            ))


    # Perform packing on the sheet
    sp = first_fit_decreasing(shapes_to_pack)
    group_shapes_ = group_shapes(sp)
    sheet, positions, remaining_shapes = pack_shapes_on_sheet(group_shapes_, sheet_length, sheet_width, spacing)
    
    # Calculate sheet utilization
    wastage_percentage, occupation_percentage = calculate_sheet_utilization(sheet, positions)
    print(f"Saved percentage: {wastage_percentage:.2f}%")
    print(f"Occupation percentage: {occupation_percentage:.2f}%")

    # Generate and save PDFs, DXFs, and tables
    save_as_pdf(positions, sheet_length, sheet_width)
    save_visualization_as_pdf(positions, sheet_length, sheet_width)
    save_as_dxf(positions)
    create_pdf_with_table(shapes_positions=positions)
    merge_pdfs(["output_file" + str(detailed_output_count) + ".pdf", "output_detailed" + str(table_count) + ".pdf"])

    # If there are remaining shapes, repeat the packing and generation process
    while len(remaining_shapes) > 0:
        positions, remaining_shapes = pack_shapes_on_sheet(remaining_shapes, sheet_length, sheet_width, spacing)
        save_as_pdf(positions, sheet_length, sheet_width)
        save_visualization_as_pdf(positions, sheet_length, sheet_width)
        save_as_dxf(positions)
        create_pdf_with_table(shapes_positions=positions)
        merge_pdfs(["output_file" + str(detailed_output_count) + ".pdf", "output_detailed" + str(table_count) + ".pdf"])

    return {"response": 200}


@app.get("/stop-server")
async def stop_server():
    os._exit(0)  # Terminate the server process

@app.get("/delete")
async def delete():
    directory_path = os.getcwd()

    # List of file extensions to delete
    file_extensions = ['.pdf', '.dxf', '.zip']

    for file_name in os.listdir(directory_path):
        for ext in file_extensions:
            if file_name.endswith(ext):
                file_path = os.path.join(directory_path, file_name)
                os.unlink(file_path)
                print(f"{file_path} deleted.")



@app.get("/download_zip_pdf")
async def download_zip_pdf():
    pdf_files = []  # Replace with your file paths
    print(pdf_count)
    for i in range(1, pdf_count + 1):  # Ensure pdf_count is defined
        file = "output" + str(i) + ".pdf"
        pdf_files.append(file)

    print(pdf_files)
    # Create a ZIP file containing the PDFs
    file_name = "pdf_files.zip"
    with ZipFile(file_name, 'w') as zip_file:
        for pdf_file in pdf_files:
            zip_file.write(pdf_file, os.path.basename(pdf_file))

    # Set response headers for a ZIP file download
    headers = {
        "Content-Disposition": "attachment; filename=pdf_files.zip",
        "Content-Type": "application/zip",
    }

    # Return the ZIP file as a response using FileResponse
    return FileResponse(file_name, headers=headers)



@app.get("/download_zip_dxf")
async def download_zip_dxf():
    pdf_files = []  # Replace with your file paths
    print(pdf_count)
    for i in range(1, dxf_count + 1):  # Ensure pdf_count is defined
        file = "output" + str(i) + ".dxf"
        pdf_files.append(file)

    print(pdf_files)
    # Create a ZIP file containing the PDFs
    file_name = "dxf_files.zip"
    with ZipFile(file_name, 'w') as zip_file:
        for pdf_file in pdf_files:
            zip_file.write(pdf_file, os.path.basename(pdf_file))

    # Set response headers for a ZIP file download
    headers = {
        "Content-Disposition": "attachment; filename=dxf_files.zip",
        "Content-Type": "application/zip",
    }

    # Return the ZIP file as a response using FileResponse
    return FileResponse(file_name, headers=headers)

@app.get("/download_zip_detailed")
async def download_zip_detailed():
    pdf_files = []  # Replace with your file paths
    print(pdf_count)
    for i in range(1,  merge_pdfs_count+ 1):  # Ensure pdf_count is defined
        file = "merged" + str(i) + ".pdf"
        pdf_files.append(file)

    print(pdf_files)
    # Create a ZIP file containing the PDFs
    file_name = "detailed_files.zip"
    with ZipFile(file_name, 'w') as zip_file:
        for pdf_file in pdf_files:
            zip_file.write(pdf_file, os.path.basename(pdf_file))

    # Set response headers for a ZIP file download
    headers = {
        "Content-Disposition": "attachment; filename=detailed_files.zip",
        "Content-Type": "application/zip",
    }

    # Return the ZIP file as a response using FileResponse
    return FileResponse(file_name, headers=headers)

@app.get("/download_pdf")
async def download_pdf():
    
    return FileResponse(pdf_filename, media_type="application/pdf", filename="output.pdf")  

@app.get("/download_pdf_detailed")
async def download_pdf():
    return FileResponse("merged.pdf", media_type="application/pdf", filename="merged.pdf")

@app.get("/download_dxf")
async def download_dxf():
    return FileResponse(dxf_filename, media_type="application/octet-stream", filename="output.dxf")

@app.get("/get_remaining")
async def get_remaining():
    return remaining_shapes

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host = "127.0.0.1", port=7349)
