![image](https://github.com/user-attachments/assets/fc317c76-4e66-4168-8404-dc7bed48104e)

# PDF Combiner

A PyQt5-based application for combining PDF pages and adding direct text overlays. This tool allows you to load PDF files, view pages as thumbnails, add and format text annotations directly on PDF pages, and export a new PDF with the modifications merged.

EXE Download: https://github.com/Kavex/PDF-Combine/releases

## Features

- **Add PDF Files:** Load one or more PDFs; each page is converted to an image and displayed as a thumbnail.
- **Direct Text Editing:** Double-click any page thumbnail to open a dedicated text editor. Add, move, and format text overlays with ease.
- **Text Formatting:** Right-click on text items to change the font or color, or to delete the text.
- **Reorder Pages:** Easily change the order of pages using "Move Up" and "Move Down" buttons.
- **Export PDF:** Merge direct text overlays with the original PDF pages and export the final combined PDF.

## Dependencies

- [Python 3.x](https://www.python.org/)
- [PyQt5](https://pypi.org/project/PyQt5/)
- [PyMuPDF](https://pypi.org/project/PyMuPDF/) – for converting PDF pages to images.
- [Pillow](https://pypi.org/project/Pillow/) – for image processing.
- [PyPDF2](https://pypi.org/project/PyPDF2/) – for PDF manipulation.
- [ReportLab](https://pypi.org/project/reportlab/) – for creating PDF overlays.

## Installation

1. **Clone or download** the repository containing the script.

2. **Install the dependencies** using pip:
    ```bash
    pip install PyQt5 PyMuPDF Pillow PyPDF2 reportlab
    ```

## Usage

1. **Run the Application:**
    ```bash
    python PDFCombine.py
    ```
2. **Load PDFs:** Click the **Add PDF** button and select one or more PDF files. Each page of the PDFs will be displayed as a thumbnail.
3. **Edit Direct Text:**
   - Double-click a page thumbnail to open the Direct Text Editor.
   - Click **Add Direct Text** to insert a text box. Double-click the text to edit it.
   - Drag the text to reposition it. Right-click on the text for options to change the font, color, or delete it.
   - Click **OK** to save your changes.
4. **Reorder Pages:** Use the **Move Up** and **Move Down** buttons to change the order of pages if needed.
5. **Export Combined PDF:** Click **Export Combined PDF** to save a new PDF file with all the direct text overlays merged onto the original pages.

## Code Overview

- **PDF Conversion Functions:** Uses PyMuPDF to convert entire PDFs or individual pages into PIL images.
- **Data Model:** The `PageData` class stores each page’s data, including the file path, page number, thumbnail image, and any direct text overlays.
- **Direct Text Items:** Custom QGraphicsTextItem objects support in-place text editing, dragging, and a right-click context menu for font and color changes.
- **Direct Text Dialog:** A dedicated dialog (`DirectTextDialog`) for editing text overlays on a PDF page, including a draggable title bar.
- **Main Window:** Provides the user interface for adding PDFs, managing pages, and exporting the final combined PDF.

## License

See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [PyQt5 Documentation](https://www.riverbankcomputing.com/software/pyqt/intro)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [PyPDF2 Documentation](https://pypdf2.readthedocs.io/)
- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
