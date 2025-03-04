import sys
import os
from io import BytesIO

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QListWidgetItem,
    QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QInputDialog,
    QDialog, QGraphicsView, QGraphicsScene, QDialogButtonBox,
    QMenu, QFontDialog, QColorDialog, QLabel
)
from PyQt5.QtGui import QPixmap, QIcon, QImage, QPainter, QFont
from PyQt5.QtCore import QSize, Qt

import fitz  # PyMuPDF
from PIL import Image

import PyPDF2
from reportlab.pdfgen import canvas

# ---------------------------------------------------------------------
# PDF Conversion Functions
# ---------------------------------------------------------------------

def convert_pdf_to_images(pdf_path, zoom=1.0):
    """
    Converts a PDF into a list of PIL images using PyMuPDF.
    """
    doc = fitz.open(pdf_path)
    images = []
    for page in doc:
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images

def convert_pdf_page_to_image(pdf_path, page_number, zoom=1.0):
    """
    Converts a single PDF page to a PIL image using PyMuPDF.
    Returns the image and the original PDF dimensions (width, height) in points.
    """
    doc = fitz.open(pdf_path)
    page = doc[page_number]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img, page.rect.width, page.rect.height

# ---------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------

class PageData:
    def __init__(self, pdf_path, page_number, pixmap):
        self.pdf_path = pdf_path
        self.page_number = page_number  # 0-indexed
        self.pixmap = pixmap
        # Direct text overlays are stored as a list of dicts.
        # Each dict has keys: text, x, y, font_family, font_size, color (RGB tuple in 0-1)
        self.direct_texts = []

# ---------------------------------------------------------------------
# Direct Text Item with Context Menu
# ---------------------------------------------------------------------

from PyQt5.QtWidgets import QGraphicsTextItem

class DirectTextItem(QGraphicsTextItem):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        # Set default font properties (adjust as needed)
        self.setFont(QFont("Helvetica", 12))
        self.setDefaultTextColor(Qt.black)
        # Allow moving, selection, and in-place editing
        self.setFlag(QGraphicsTextItem.ItemIsMovable, True)
        self.setFlag(QGraphicsTextItem.ItemIsSelectable, True)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)

    def contextMenuEvent(self, event):
        menu = QMenu()
        changeFontAction = menu.addAction("Change Font")
        changeColorAction = menu.addAction("Change Color")
        deleteAction = menu.addAction("Delete Text")
        action = menu.exec_(event.screenPos())
        if action == changeFontAction:
            font, ok = QFontDialog.getFont(self.font(), None, "Select Font")
            if ok:
                self.setFont(font)
        elif action == changeColorAction:
            color = QColorDialog.getColor(self.defaultTextColor(), None, "Select Color")
            if color.isValid():
                self.setDefaultTextColor(color)
        elif action == deleteAction:
            if self.scene():
                self.scene().removeItem(self)
        event.accept()

# ---------------------------------------------------------------------
# Draggable Title Bar for the Direct Text Dialog
# ---------------------------------------------------------------------

class DraggableTitleBar(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("background-color: #444; color: white; padding: 4px;")
        self.setAlignment(Qt.AlignCenter)
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.window().frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.window().move(event.globalPos() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

# ---------------------------------------------------------------------
# Direct Text Dialog
# ---------------------------------------------------------------------

class DirectTextDialog(QDialog):
    """
    A dialog that shows a full-size view of a PDF page and lets you add
    direct text overlays via a dedicated button. Direct text items are
    draggable and support a right-click context menu for font/color changes.
    """
    def __init__(self, pdf_path, page_number, direct_zoom=2.0, parent=None):
        super().__init__(parent)
        self.direct_zoom = direct_zoom

        # Create a draggable title bar
        self.titleBar = DraggableTitleBar("Direct Text Editor", self)

        # Get full-size page image and PDF dimensions (in points)
        pil_img, self.pdf_width, self.pdf_height = convert_pdf_page_to_image(pdf_path, page_number, zoom=direct_zoom)
        self.image = self.pil2pixmap(pil_img)

        # Set up the scene and view
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, self.image.width(), self.image.height())
        self.scene.addPixmap(self.image)

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)

        # Button to add a new direct text item
        self.addTextButton = QPushButton("Add Direct Text")
        self.addTextButton.clicked.connect(self.add_direct_text_item)

        # Dialog buttons (OK/Cancel)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Layout: title bar, view, add button, and dialog buttons
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.titleBar)
        layout.addWidget(self.view)
        layout.addWidget(self.addTextButton)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

    def pil2pixmap(self, im):
        """Convert a PIL Image to QPixmap."""
        im = im.convert("RGBA")
        data = im.tobytes("raw", "RGBA")
        qimage = QImage(data, im.size[0], im.size[1], QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)
        return pixmap

    def add_direct_text_item(self):
        """
        Adds a new DirectTextItem at a default position.
        The default text is "Double-click to edit".
        """
        item = DirectTextItem("Double-click to edit")
        # Place at a default position (e.g., 50,50)
        item.setPos(50, 50)
        self.scene.addItem(item)

    def getDirectTexts(self):
        """
        Ensures any active text edits are committed, then iterates over
        the scene items to extract direct text items.
        Returns a list of dicts with keys:
          - text: text content
          - x, y: coordinates in PDF points (origin bottom left)
          - font_family: font family string
          - font_size: font size in points
          - color: RGB tuple (each between 0 and 1)
        """
        # Force commit any in-progress edits
        for item in self.scene.items():
            if isinstance(item, DirectTextItem) and item.hasFocus():
                item.clearFocus()

        texts = []
        for item in self.scene.items():
            if isinstance(item, DirectTextItem):
                pos = item.pos()  # Scene coordinates (top-left origin)
                pdf_x = pos.x() / self.direct_zoom
                pdf_y = self.pdf_height - (pos.y() / self.direct_zoom)
                text = item.toPlainText()
                font = item.font()
                font_family = font.family()
                font_size = font.pointSize()
                color = item.defaultTextColor()
                r = color.red() / 255.0
                g = color.green() / 255.0
                b = color.blue() / 255.0
                texts.append({
                    "text": text,
                    "x": pdf_x,
                    "y": pdf_y,
                    "font_family": font_family,
                    "font_size": font_size,
                    "color": (r, g, b)
                })
        return texts

# ---------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Combiner")
        self.resize(900, 600)

        self.listWidget = QListWidget()
        self.listWidget.setIconSize(QSize(120, 160))
        self.listWidget.setViewMode(QListWidget.IconMode)
        self.listWidget.setDragDropMode(QListWidget.NoDragDrop)
        # Open Direct Text Editor by double-clicking a page thumbnail
        self.listWidget.itemDoubleClicked.connect(self.open_direct_text_dialog)

        self.addButton = QPushButton("Add PDF")
        self.removeButton = QPushButton("Remove Selected")
        self.moveUpButton = QPushButton("Move Up")
        self.moveDownButton = QPushButton("Move Down")
        self.exportButton = QPushButton("Export Combined PDF")

        layout = QVBoxLayout()
        layout.addWidget(self.listWidget)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.addButton)
        buttonLayout.addWidget(self.removeButton)
        buttonLayout.addWidget(self.moveUpButton)
        buttonLayout.addWidget(self.moveDownButton)
        buttonLayout.addWidget(self.exportButton)
        layout.addLayout(buttonLayout)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.addButton.clicked.connect(self.add_pdf)
        self.removeButton.clicked.connect(self.remove_selected)
        self.moveUpButton.clicked.connect(self.move_up)
        self.moveDownButton.clicked.connect(self.move_down)
        self.exportButton.clicked.connect(self.export_pdf)

    def pil2pixmap(self, im):
        """Convert a PIL Image to QPixmap."""
        im = im.convert("RGBA")
        data = im.tobytes("raw", "RGBA")
        qimage = QImage(data, im.size[0], im.size[1], QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)
        return pixmap

    def add_pdf(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select PDF Files", "", "PDF Files (*.pdf)")
        if not file_paths:
            return
        for path in file_paths:
            try:
                pages = convert_pdf_to_images(path, zoom=1.0)
                for i, page_image in enumerate(pages):
                    qt_pix = self.pil2pixmap(page_image)
                    qt_pix_copy = qt_pix.copy()
                    page_data = PageData(pdf_path=path, page_number=i, pixmap=qt_pix_copy)
                    item_text = f"{os.path.basename(path)} - Page {i+1}"
                    item = QListWidgetItem(QIcon(qt_pix_copy), item_text)
                    # Store direct texts separately
                    page_data.direct_texts = []
                    item.setData(Qt.UserRole, page_data)
                    item.setSizeHint(QSize(130, 180))
                    self.listWidget.addItem(item)
            except Exception as e:
                print(f"Error processing {path}: {e}")

    def remove_selected(self):
        selected_items = self.listWidget.selectedItems()
        for item in selected_items:
            self.listWidget.takeItem(self.listWidget.row(item))

    def open_direct_text_dialog(self, item):
        """
        Opens the Direct Text Editor dialog for the selected page.
        """
        page_data = item.data(Qt.UserRole)
        dialog = DirectTextDialog(page_data.pdf_path, page_data.page_number, direct_zoom=2.0, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            direct_texts = dialog.getDirectTexts()
            page_data.direct_texts = direct_texts
            item.setText(f"{os.path.basename(page_data.pdf_path)} - Page {page_data.page_number+1} (Direct Text Added)")
            item.setData(Qt.UserRole, page_data)

    def move_up(self):
        current_row = self.listWidget.currentRow()
        if current_row > 0:
            item = self.listWidget.takeItem(current_row)
            self.listWidget.insertItem(current_row - 1, item)
            self.listWidget.setCurrentRow(current_row - 1)

    def move_down(self):
        current_row = self.listWidget.currentRow()
        if current_row < self.listWidget.count() - 1 and current_row != -1:
            item = self.listWidget.takeItem(current_row)
            self.listWidget.insertItem(current_row + 1, item)
            self.listWidget.setCurrentRow(current_row + 1)

    def export_pdf(self):
        export_path, _ = QFileDialog.getSaveFileName(self, "Export Combined PDF", "", "PDF Files (*.pdf)")
        if not export_path:
            return
        output = PyPDF2.PdfWriter()
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            page_data = item.data(Qt.UserRole)
            try:
                pdf_reader = PyPDF2.PdfReader(page_data.pdf_path)
                src_page = pdf_reader.pages[page_data.page_number]
            except Exception as e:
                print(f"Error reading {page_data.pdf_path} page {page_data.page_number+1}: {e}")
                continue
            if page_data.direct_texts:
                width = float(src_page.mediabox.getWidth())
                height = float(src_page.mediabox.getHeight())
                packet = BytesIO()
                can = canvas.Canvas(packet, pagesize=(width, height))
                for text_data in page_data.direct_texts:
                    try:
                        can.setFont(text_data["font_family"], text_data["font_size"])
                        r, g, b = text_data["color"]
                        can.setFillColorRGB(r, g, b)
                        can.drawString(text_data["x"], text_data["y"], text_data["text"])
                    except Exception as e:
                        print("Error drawing direct text:", e)
                can.save()
                packet.seek(0)
                try:
                    overlay_pdf = PyPDF2.PdfReader(packet)
                    overlay_page = overlay_pdf.pages[0]
                    src_page.merge_page(overlay_page)
                except Exception as e:
                    print(f"Error merging direct text on page: {e}")
            output.add_page(src_page)
        try:
            with open(export_path, "wb") as f:
                output.write(f)
            print(f"Exported combined PDF to {export_path}")
        except Exception as e:
            print(f"Error exporting PDF: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
