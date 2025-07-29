import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QFileDialog,
    QVBoxLayout, QMessageBox, QTextEdit
)
from PyQt6.QtCore import QObject, pyqtSignal, QThread

# Import your processing function
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Main import process_pdf  # Adjust this to your actual module

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

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            process_pdf(self.file_path)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

class SimpleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF/Image Processor")
        self.setGeometry(100, 100, 400, 300)

        self.label = QLabel("Upload a PDF or Image", self)
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

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "PDF Files (*.pdf);;Image Files (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.file_path = file_path
            self.label.setText(f"Selected: {file_path}")
            print(f"File selected: {file_path}")

    def process_file(self):
        if not self.file_path:
            QMessageBox.warning(self, "No File", "Please upload a file first.")
            return

        print(f"Starting processing for: {self.file_path}")
        self.process_btn.setEnabled(False)

        self.thread = QThread()
        self.worker = ProcessorWorker(self.file_path)
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
