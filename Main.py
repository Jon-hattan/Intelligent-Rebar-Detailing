import GUI.main_window as main
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QFileDialog,
    QVBoxLayout, QMessageBox, QTextEdit
)
from PyQt6.QtCore import QObject, pyqtSignal, QThread

app = QApplication(sys.argv)
window = main.SimpleApp()
window.show()
sys.exit(app.exec())
