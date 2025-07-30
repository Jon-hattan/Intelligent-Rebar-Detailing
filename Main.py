#RUN the main GUI from here
import os
import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap, QGuiApplication, QFont, QColor
from PyQt6.QtCore import Qt, QRect
from pathlib import Path



def resource_path(relative_path): #to ensure that once it is made into an exe file the paths dont get screwed up
    base_path = getattr(sys, '_MEIPASS', Path(__file__).parent)
    return os.path.join(base_path, relative_path)

app = QApplication(sys.argv)

# Load and resize splash image
splash_pix = QPixmap(resource_path("GUI/splash.png")).scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)

# Center the splash screen
screen_geometry = QGuiApplication.primaryScreen().geometry()
x = (screen_geometry.width() - splash_pix.width()) // 2
y = (screen_geometry.height() - splash_pix.height()) // 2
splash.setGeometry(QRect(x, y, splash_pix.width(), splash_pix.height()))

# Show splash screen with message

# Set a larger font before showing the message
font = QFont("Sans Serif", 13, QFont.Weight.Bold) 
splash.setFont(font)
custom_color = QColor(36, 75, 92)  # RGB values

# Then show the message
splash.showMessage("Loading app...", 
                   Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, 
                   custom_color)
splash.show()


# Initialize and show main window
icon = resource_path("GUI/icon.ico")
#lazy import
from GUI.main_window import SimpleApp
window = SimpleApp(icon)
window.show()

# Close splash screen once main window is ready
splash.finish(window)

sys.exit(app.exec())
