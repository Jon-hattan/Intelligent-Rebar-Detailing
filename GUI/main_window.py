import sys
import os
import fitz  # PyMuPDF
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QFileDialog,
    QVBoxLayout, QMessageBox, QTextEdit
)
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtGui import QIcon
from .scale_calibration import ImageViewer
from Processor.Main_processor import process_pdf


# Custom stream to redirect print output to GUI
class EmittingStream(QObject):
    text_written = pyqtSignal(str)

    def write(self, text):
        self.text_written.emit(str(text))

    def flush(self):
        pass


# Worker class to run processing in a background thread
class ProcessorWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, file_path, scale_factor=None):
        super().__init__()
        self.file_path = file_path
        self.scale_factor = scale_factor

    def run(self):
        try:
            process_pdf(self.file_path, self.scale_factor)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class SimpleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Slab Reinforcement Detailing Processor")
        self.setWindowIcon(QIcon("./GUI/icon.ico"))
        self.setGeometry(100, 100, 700, 500)

        self.label = QLabel("Upload your PDF:", self)
        self.upload_btn = QPushButton("Browse", self)
        self.process_btn = QPushButton("Process", self)
        self.output_box = QTextEdit(self)
        self.output_box.setReadOnly(True)

        self.upload_btn.clicked.connect(self.upload_file)
        self.process_btn.clicked.connect(self.process_file)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.upload_btn)
        layout.addWidget(self.process_btn)
        layout.addWidget(self.output_box)
        self.setLayout(layout)

        # Redirect stdout to the output box
        sys.stdout = EmittingStream()
        sys.stdout.text_written.connect(self.output_box.append)

        self.file_path = None
        self.thread = None
        self.scale_factor = None

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.file_path = file_path
            self.label.setText(f"Selected: {file_path}")
            print(f"File selected: {file_path}")

    def process_file(self):
        if not self.file_path:
            QMessageBox.warning(self, "No File", "Please upload a file first.")
            return

        if not self.file_path.lower().endswith(".pdf"):
            QMessageBox.warning(self, "Invalid File", "Please upload a PDF file.")
            return

        # Convert first page of PDF to image
        try:
            doc = fitz.open(self.file_path)
            pix = doc[0].get_pixmap(dpi=300)
            os.makedirs("./resources", exist_ok=True)
            image_path = "./resources/page1.png"
            pix.save(image_path)
            doc.close()
            print("First page of PDF converted to image for calibration.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to convert PDF to image:\n{str(e)}")
            return

        # Open calibration window
        self.calibration_window = QWidget()
        self.calibration_window.setWindowTitle("Calibrate Scale")
        self.calibration_window.setGeometry(150, 150, 800, 600)

        self.viewer = ImageViewer(image_path)
        self.viewer.scale_calibrated.connect(self.start_processing_after_calibration)

        layout = QVBoxLayout()
        layout.addWidget(self.viewer)
        self.calibration_window.setLayout(layout)
        self.calibration_window.show()

    def start_processing_after_calibration(self, scale):
        self.scale_factor = scale
        self.calibration_window.close()
        print(f"Scale factor set: {scale:.6f} units/pixel")
        self.run_processing_thread()

    def run_processing_thread(self):
        print(f"Starting processing for: {self.file_path}")
        self.process_btn.setEnabled(False)

        self.thread = QThread()
        self.worker = ProcessorWorker(self.file_path, self.scale_factor)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(lambda: self.process_btn.setEnabled(True))
        self.worker.error.connect(self.show_error)
        self.thread.finished.connect(lambda: print("Processing complete."))

        self.thread.start()

    def show_error(self, message):
        QMessageBox.critical(self, "Error", f"An error occurred:\n{message}")
        print(f"Error: {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleApp()
    window.show()
    sys.exit(app.exec())
