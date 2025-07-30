#RUN the main GUI from here

import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap, QGuiApplication
from PyQt6.QtCore import Qt, QRect
from GUI.main_window import SimpleApp

app = QApplication(sys.argv)

# Load and resize splash image
splash_pix = QPixmap("./GUI/splash.png").scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)

# Center the splash screen
screen_geometry = QGuiApplication.primaryScreen().geometry()
x = (screen_geometry.width() - splash_pix.width()) // 2
y = (screen_geometry.height() - splash_pix.height()) // 2
splash.setGeometry(QRect(x, y, splash_pix.width(), splash_pix.height()))

# Show splash screen with message
splash.showMessage("Loading floor plan processor...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)
splash.show()

# Initialize and show main window
window = SimpleApp()
window.show()

# Close splash screen once main window is ready
splash.finish(window)

sys.exit(app.exec())
