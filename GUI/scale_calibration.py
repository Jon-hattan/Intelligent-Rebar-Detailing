from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem, QInputDialog
from PyQt6.QtGui import QPixmap, QPen
from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal

import cv2
import os

class ImageViewer(QGraphicsView):
    scale_calibrated = pyqtSignal(float)

    def __init__(self, image_path):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.original_path = image_path
        self.resized_path = "./resources/resized_page1.png"
        self.resize_ratio = self.resize_image_for_qt(image_path, self.resized_path)

        self.pixmap = QPixmap(self.resized_path)
        if self.pixmap.isNull():
            print("Failed to load image.")
        else:
            self.scene.addPixmap(self.pixmap)

        self.start_point = None
        self.line_item = None
        self.scale_factor = None  # in real-world units per original pixel

    def resize_image_for_qt(self, input_path, output_path, max_dim=2000):
        img = cv2.imread(input_path)
        h, w = img.shape[:2]
        scale = max_dim / max(h, w)
        if scale < 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            cv2.imwrite(output_path, img)
        else:
            # If no resizing needed, just copy the file
            if input_path != output_path:
                cv2.imwrite(output_path, img)
        return 1.0 / scale if scale < 1.0 else 1.0  # resize_ratio = original / resized


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = self.mapToScene(event.pos())
            if self.line_item:
                self.scene.removeItem(self.line_item)
            self.line_item = QGraphicsLineItem()
            pen = QPen(Qt.GlobalColor.red, 2)
            self.line_item.setPen(pen)
            self.scene.addItem(self.line_item)

    def mouseMoveEvent(self, event):
        if self.start_point and self.line_item:
            current_pos = self.mapToScene(event.pos())
            self.line_item.setLine(self.start_point.x(), self.start_point.y(),
                                current_pos.x(), current_pos.y())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.start_point and self.line_item:
            end_point = self.mapToScene(event.pos())
            self.calculate_scale(self.start_point, end_point)
            self.start_point = None


    def draw_line(self, start, end):
        if self.line_item:
            self.scene.removeItem(self.line_item)
        pen = QPen(Qt.GlobalColor.red, 2)
        self.line_item = QGraphicsLineItem(start.x(), start.y(), end.x(), end.y())
        self.line_item.setPen(pen)
        self.scene.addItem(self.line_item)

    def calculate_scale(self, start, end):
        pixel_distance_resized = ((start.x() - end.x())**2 + (start.y() - end.y())**2)**0.5
        pixel_distance_original = pixel_distance_resized * self.resize_ratio
        real_distance, ok = QInputDialog.getDouble(self, "Real Distance", "Enter real-world distance (e.g., meters):", 1.0, 0.01, 10000, 2)
        if ok:
            self.scale_factor = real_distance / pixel_distance_original
            print(f"Scale factor: {self.scale_factor:.6f} units per original pixel")
            self.scale_calibrated.emit(self.scale_factor)  # Emit the signal here
