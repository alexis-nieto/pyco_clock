import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt, QTimer, QSize, QPoint
from PySide6.QtGui import QFont, QColor, QPalette, QCursor

class MinimalClock(QWidget):
    # --- Configuration ---
    RESIZE_BORDER_SIZE = 5      # Width of the border area for resizing
    ASPECT_RATIO = 3.0 / 1.0    # 3:1 (Width to Height)
    
    def __init__(self):
        super().__init__()
        
        self.BG_COLOR = QColor(0, 0, 0)         # Black
        self.FG_COLOR = QColor(255, 255, 255)   # White
        
        # Variables for custom resizing and dragging
        self.old_pos = None
        self._resizing_edge = None
        
        self.init_ui()
        self.init_timer()

    def init_ui(self):
        # 1. Window Flags and Appearance
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        palette = self.palette()
        palette.setColor(QPalette.Window, self.BG_COLOR)
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        # 2. Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5) # Small padding
        main_layout.setSpacing(0)
        
        # 3. Top Row (For the Close Button)
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.addStretch() # Pushes the button to the right

        # Create Close Button (Small 'X')
        self.close_button = QPushButton("x")
        self.close_button.setFixedSize(20, 20)
        self.close_button.setFont(QFont("Helvetica", 10, QFont.Bold))
        self.close_button.setStyleSheet(f"background-color: transparent; color: {self.FG_COLOR.name()}; border: none;")
        self.close_button.clicked.connect(self.close)
        
        # Add button to the top layout
        top_bar_layout.addWidget(self.close_button)
        main_layout.addLayout(top_bar_layout)
        
        # 4. Time Label
        self.time_label = QLabel("00:00:00", self)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet(f"color: {self.FG_COLOR.name()};")
        
        # Add time label to the main layout
        main_layout.addWidget(self.time_label)

        # 5. Final Setup
        self.resize(300, 100)
        self.setMinimumSize(QSize(150, 50)) 
        self.setMouseTracking(True)

    def init_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(100) 
        self.update_time()

    def update_time(self):
        from datetime import datetime
        current_time = datetime.now().strftime('%H:%M:%S')
        self.time_label.setText(current_time)
        self.update_font_size()

    def update_font_size(self):
        height = self.height()
        if height > 0:
            new_font_size = int(height * 0.5) # Using 0.5 to account for the top bar
            if new_font_size < 12:
                new_font_size = 12
            font = QFont("Helvetica", new_font_size, QFont.Bold)
            self.time_label.setFont(font)
            
    # --- Custom Resizing Logic (Refined for stability) ---

    def get_resize_edge(self, pos):
        """Determines if the mouse is near an edge or corner for resizing."""
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        s = self.RESIZE_BORDER_SIZE

        # Check corners and edges
        if x < s and y < s: return Qt.Corner.TopLeftCorner
        if x > w - s and y < s: return Qt.Corner.TopRightCorner
        if x < s and y > h - s: return Qt.Corner.BottomLeftCorner
        if x > w - s and y > h - s: return Qt.Corner.BottomRightCorner
        if x < s: return Qt.Edge.LeftEdge
        if x > w - s: return Qt.Edge.RightEdge
        if y < s: return Qt.Edge.TopEdge
        if y > h - s: return Qt.Edge.BottomEdge
        return None

    def mousePressEvent(self, event):
        """Handles both starting a drag and starting a resize."""
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
            
            # Check if we are starting a resize operation
            self._resizing_edge = self.get_resize_edge(event.pos())
            event.accept()

    def mouseMoveEvent(self, event):
        """Handles resizing if active, otherwise handles dragging or cursor change."""
        
        # 1. Handle Active Resizing/Dragging
        if event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self.old_pos
            
            if self._resizing_edge is not None:
                self.perform_resize(delta)
            else:
                # Perform standard dragging
                self.move(self.pos() + delta)
                
            self.old_pos = event.globalPosition().toPoint()
        
        # 2. Handle Cursor Hover (Setting the cursor shape)
        else:
            edge = self.get_resize_edge(event.pos())
            if edge is not None:
                self.setCursor(self.cursor_for_edge(edge))
            else:
                # Only reset cursor if no buttons are pressed AND we are not over the button
                self.setCursor(Qt.CursorShape.ArrowCursor) 

        event.accept()

    def mouseReleaseEvent(self, event):
        """Resets the resizing state."""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.old_pos = None
        self._resizing_edge = None
        event.accept()

    def cursor_for_edge(self, edge):
        """Maps an edge/corner to the appropriate cursor shape."""
        cursors = {
            Qt.Edge.TopEdge: Qt.CursorShape.SizeVerCursor,
            Qt.Edge.BottomEdge: Qt.CursorShape.SizeVerCursor,
            Qt.Edge.LeftEdge: Qt.CursorShape.SizeHorCursor,
            Qt.Edge.RightEdge: Qt.CursorShape.SizeHorCursor,
            Qt.Corner.TopLeftCorner: Qt.CursorShape.SizeFDiagCursor,
            Qt.Corner.TopRightCorner: Qt.CursorShape.SizeBDiagCursor,
            Qt.Corner.BottomLeftCorner: Qt.CursorShape.SizeBDiagCursor,
            Qt.Corner.BottomRightCorner: Qt.CursorShape.SizeFDiagCursor,
        }
        return cursors.get(edge, Qt.CursorShape.ArrowCursor)
    
    def perform_resize(self, delta: QPoint):
        """Calculates and applies the new size and position based on the drag delta."""
        rect = self.geometry()
        
        # Initial geometry changes
        new_x, new_y, new_w, new_h = rect.x(), rect.y(), rect.width(), rect.height()

        if self._resizing_edge in [Qt.Edge.LeftEdge, Qt.Corner.TopLeftCorner, Qt.Corner.BottomLeftCorner]:
            new_x += delta.x()
            new_w -= delta.x()
        
        if self._resizing_edge in [Qt.Edge.RightEdge, Qt.Corner.TopRightCorner, Qt.Corner.BottomRightCorner]:
            new_w += delta.x()
        
        if self._resizing_edge in [Qt.Edge.TopEdge, Qt.Corner.TopLeftCorner, Qt.Corner.TopRightCorner]:
            new_y += delta.y()
            new_h -= delta.y()
            
        if self._resizing_edge in [Qt.Edge.BottomEdge, Qt.Corner.BottomLeftCorner, Qt.Corner.BottomRightCorner]:
            new_h += delta.y()

        # Enforce minimum size
        new_w = max(new_w, self.minimumWidth())
        new_h = max(new_h, self.minimumHeight())
        
        # --- Apply Aspect Ratio Lock ---
        
        current_ratio = new_w / new_h
        
        if abs(current_ratio - self.ASPECT_RATIO) > 0.01:
            # Prioritize the dimension that was primarily dragged for the aspect lock
            
            # If resizing Top/Bottom (primarily changing height)
            if self._resizing_edge in [Qt.Edge.TopEdge, Qt.Edge.BottomEdge]:
                new_w = int(new_h * self.ASPECT_RATIO)
                
            # If resizing Left/Right (primarily changing width)
            elif self._resizing_edge in [Qt.Edge.LeftEdge, Qt.Edge.RightEdge]:
                 new_h = int(new_w / self.ASPECT_RATIO)

            # If resizing a corner, adjust the one that needs the least change
            elif self._resizing_edge in [Qt.Corner.TopLeftCorner, Qt.Corner.TopRightCorner, Qt.Corner.BottomLeftCorner, Qt.Corner.BottomRightCorner]:
                 # Decide whether to prioritize width or height based on the current ratio
                 if current_ratio > self.ASPECT_RATIO:
                     new_w = int(new_h * self.ASPECT_RATIO)
                 else:
                     new_h = int(new_w / self.ASPECT_RATIO)

        # Final move/resize
        self.setGeometry(new_x, new_y, new_w, new_h)


    # --- Aspect Ratio Enforcement for external resize (e.g., maximizing) ---
    def resizeEvent(self, event):
        """Called whenever the widget is resized."""
        
        width = self.width()
        height = self.height()
        current_ratio = width / height

        # If the aspect ratio is off and we are NOT actively resizing
        if abs(current_ratio - self.ASPECT_RATIO) > 0.01 and self._resizing_edge is None:
            # Simple fix: adjust width based on height for stability
            new_width = int(height * self.ASPECT_RATIO)
            self.resize(new_width, height)
        
        super().resizeEvent(event)
        self.update_font_size()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    clock = MinimalClock()
    
    # Center the window on the screen
    screen_geometry = app.primaryScreen().geometry()
    x = (screen_geometry.width() - clock.width()) // 2
    y = (screen_geometry.height() - clock.height()) // 2
    clock.move(x, y)
    
    clock.show()
    sys.exit(app.exec())