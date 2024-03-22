<<<<<<< HEAD
from flask import Flask, request, send_file
from PyPDF2 import PdfReader
import ezdxf
import io

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_pdf_to_dxf():
    try:
        # Get the uploaded PDF file from the request
        pdf_file = request.files['pdf']

        # Read the PDF file and convert to DXF
        pdf = PdfReader(pdf_file)
        dxf = ezdxf.new()
        msp = dxf.modelspace()

        # Iterate through PDF pages and convert to DXF entities
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            for content in page.extract_text().split('\n'):
                msp.add_text(content, dxfattribs={'height': 1}).set_pos((0, -1))

        # Save DXF file to a bytesIO object
        dxf_bytes = io.BytesIO()
        dxf.saveas(dxf_bytes)

        # Move to the beginning of the BytesIO buffer
        dxf_bytes.seek(0)

        # Send the DXF file as a response
        return send_file(dxf_bytes, as_attachment=True, attachment_filename='output.dxf', mimetype='application/octet-stream')
    except Exception as e:
        return str(e), 500  # Return error message if something went wrong

if __name__ == '__main__':
    app.run(debug=True)
=======
from flask import Flask, request, send_file
from PyPDF2 import PdfReader
import ezdxf
import io

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_pdf_to_dxf():
    try:
        # Get the uploaded PDF file from the request
        pdf_file = request.files['pdf']

        # Read the PDF file and convert to DXF
        pdf = PdfReader(pdf_file)
        dxf = ezdxf.new()
        msp = dxf.modelspace()

        # Iterate through PDF pages and convert to DXF entities
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            for content in page.extract_text().split('\n'):
                msp.add_text(content, dxfattribs={'height': 1}).set_pos((0, -1))

        # Save DXF file to a bytesIO object
        dxf_bytes = io.BytesIO()
        dxf.saveas(dxf_bytes)

        # Move to the beginning of the BytesIO buffer
        dxf_bytes.seek(0)

        # Send the DXF file as a response
        return send_file(dxf_bytes, as_attachment=True, attachment_filename='output.dxf', mimetype='application/octet-stream')
    except Exception as e:
        return str(e), 500  # Return error message if something went wrong

if __name__ == '__main__':
    app.run(debug=True)
>>>>>>> bb0b97796322c7ab8a2015a0166f74852b11a6f1
