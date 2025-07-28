PDF Outline Extractor — Adobe Connecting the Dots Challenge (Round 1A):

Overview
This project extracts structured outlines from PDFs, detecting titles and hierarchical headings (H1, H2, H3) using font size, boldness, and numbering patterns. Outputs are JSON files with the document structure by page.

Requirements:

Python libraries (see requirements.txt):
PyMuPDF==1.23.7
pytesseract==0.3.10
pdf2image==1.16.3
Pillow==10.3.0

System packages (installed in Docker):

tesseract-ocr, libtesseract-dev, poppler-utils, libgl1-mesa-glx, libglib2.0-0

Setup & Run
Using Docker

docker build -t pdf-outline-extractor .
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output pdf-outline-extractor



Output

JSON files per PDF with keys:
title: extracted or suggested title
outline: list of headings with level, text, and page

