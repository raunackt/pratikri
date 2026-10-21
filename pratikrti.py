import os
from select import select

from krita import DockWidget, Krita
from PyQt5.QtCore import QByteArray, QPoint, QRect, QSettings, Qt
from PyQt5.QtGui import QImage, QPainter, QPixmap, QTransform
from PyQt5.QtWidgets import (
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class PratikrtiDocker(DockWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Pratikrti")
        self.pattern_path = None
        self.settings = QSettings(
            QSettings.IniFormat, QSettings.UserScope, "Pratikrti", "Pratikrti"
        )
        self.last_folder = self.settings.value(
            "last_pattern_folder", os.path.expanduser("~"), type=str
        )

        container = QWidget(self)
        layout = QVBoxLayout(container)

        layout.addWidget(QLabel("Pratikrti"))
        layout.addWidget(
            QLabel("Next: load a pattern to fill selection.").setWordWrap(True)
        )

        self.file_label = QLabel("No pattern selected")
        self.file_label.setWordWrap(True)
        layout.addWidget(self.file_label)

        self.preview_label = QLabel("No preview")
        self.preview_label.setFixedSize(160, 160)
        self.preview_label.setScaledContents(False)
        layout.addWidget(self.preview_label)

        choose_btn = QPushButton("Choose Pattern")
        layout.addWidget(choose_btn)
        choose_btn.clicked.connect(self.choose_pattern)

        layout.addWidget(QLabel("Pattern Scale"))

        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(10, 300)
        self.scale_spin.setValue(100)
        self.scale_spin.setSuffix("%")
        layout.addWidget(self.scale_spin)

        layout.addWidget(QLabel("Pattern Rotation"))

        self.rotation_spin = QSpinBox()
        self.rotation_spin.setRange(0, 359)
        self.rotation_spin.setValue(0)
        self.rotation_spin.setSuffix("°")
        layout.addWidget(self.rotation_spin)

        self.repeat_btn = QPushButton("Repeat Pattern")
        self.repeat_btn.setEnabled(False)
        self.repeat_btn.clicked.connect(self.repeat_pattern)
        layout.addWidget(self.repeat_btn)

        self.setWidget(container)

    def choose_pattern(self):
        start_folder = self.last_folder

        if not start_folder or not os.path.isdir(start_folder):
            start_folder = os.path.expanduser("~")

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Pattern Image",
            start_folder,
            "PNG Images (*.png);;"
            "JPEG Images (*.jpg *.jpeg);;"
            "BMP Images (*.bmp);;"
            "TIFF Images (*.tif *.tiff);;"
            "WebP Images (*.webp);;"
            "All Files (*)",
        )

        if not path:
            return

        self.pattern_path = path
        self.last_folder = os.path.dirname(path)

        self.settings.setValue("last_pattern_folder", self.last_folder)
        self.settings.sync()
        print("Saved pattern folder:", self.settings.fileName())
        print("Folder value:", self.settings.value("last_pattern_folder"))

        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.preview_label.setPixmap(
                pixmap.scaled(
                    self.preview_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )
        self.file_label.setText(os.path.basename(path))
        self.repeat_btn.setEnabled(True)

    def repeat_pattern(self):

        app = Krita.instance()
        doc = app.activeDocument()

        if doc is None:
            QMessageBox.warning(self, "Pratikrti", "No document is open.")
            return

        if not self.pattern_path or not os.path.isfile(self.pattern_path):
            QMessageBox.warning(self, "Pratikrti", "Please choose a valid file.")
            return

        selection = doc.selection()

        if selection is None:
            QMessageBox.warning(self, "Pratikrti", "No pixels selected.")
            return

        x = selection.x()
        y = selection.y()
        width = selection.width()
        height = selection.height()

        if width <= 0 or height <= 0:
            QMessageBox.warning(self, "Pratikrti", "Not a valid selection.")
            return

        pattern = QImage(self.pattern_path)
        if pattern.isNull():
            QMessageBox.warning(self, "Pratikrti", "Could not read the selected image")
            return

        scale_percent = self.scale_spin.value()
        scaled_width = max(1, round(pattern.width() * scale_percent / 100))
        scaled_height = max(1, round(pattern.height() * scale_percent / 100))

        pattern = pattern.scaled(
            scaled_width, scaled_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )

        rotation = self.rotation_spin.value()

        if rotation:
            transform = QTransform().rotate(rotation)
            pattern = pattern.transformed(transform, Qt.SmoothTransformation)

        pw = pattern.width()
        ph = pattern.height()

        # Make a transparent image covering the selection bounds
        output = QImage(width, height, QImage.Format_ARGB32)
        output.fill(0)

        # Tile relative to the document origin.
        painter = QPainter(output)
        start_x = (x // pw) * pw
        start_y = (y // ph) * ph

        tile_y = start_y
        while tile_y < y + height:
            tile_x = start_x
            while tile_x < x + width:
                painter.drawImage(tile_x - x, tile_y - y, pattern)
                tile_x += pw
            tile_y += ph

        painter.end()

        # Qt ARGB32 on Windows stores bytes as BGRA,
        # matching Krita's usual RGBA/U8 pixel layout.
        pixels = bytearray(output.bits().asstring(output.sizeInBytes()))

        # Apply the selection mask to each pixel's alpha.
        mask = bytes(selection.pixelData(x, y, width, height))

        if len(mask) < width * height:
            QMessageBox.warning(self, "Pratikrti", "Could not read the selection mask.")
            return

        for i, coverage in enumerate(mask[: width * height]):
            alpha_index = i * 4 + 3
            old_alpha = pixels[alpha_index]
            pixels[alpha_index] = (old_alpha * coverage + 127) // 255

        # Create a new layer so the artwork remains untouched.
        layer = doc.createNode("Repeated Pattern", "paintlayer")

        if layer is None:
            QMessageBox.warning(self, "Pratikrti", "Could not create a paint layer.")
            return

        doc.rootNode().addChildNode(layer, None)

        expected_bytes = bytes(pixels)
        expected_size = width * height * 4

        if len(expected_bytes) != expected_size:
            doc.rootNote().removeChildNode(layer)
            QMessageBox.warning(
                self,
                "Pratikrti",
                "Pixel buffer mismatch.\n"
                f"Expected: {expected_size} bytes\n"
                f"Actual: {len(expected_bytes)} bytes.",
            )
            return

        layer.setPixelData(QByteArray(expected_bytes), x, y, width, height)

        # Read the pixels back to verify the write.
        actual_bytes = bytes(layer.pixelData(x, y, width, height))

        if len(actual_bytes) != expected_size:
            QMessageBox.warning(
                self,
                "Pattern Repeater",
                "Pixel write verification failed.\n"
                f"Expected: {expected_size} bytes\n"
                f"Read back: {len(actual_bytes)} bytes",
            )
            return
        if actual_bytes != expected_bytes:
            # Report the mismatch without silently claiming success.
            differing = sum(a != b for a, b in zip(expected_bytes, actual_bytes))
            QMessageBox.warning(
                self,
                "Pattern Repeater",
                "Pixel data differs after writing.\n"
                f"Differing bytes: {differing}\n"
                "The layer has been kept for inspection.",
            )
            return

        doc.setActiveNode(layer)
        doc.refreshProjection()

        QMessageBox.information(self, "Pratikrti", "Pattern created on a new layer.")

        QMessageBox.information(
            self,
            "Pratikrti",
            "Pattern image loaded successfully: \n" + self.pattern_path,
        )

    def canvasChanged(self, canvas):
        pass


from krita import Krita


class PratikrtiExtension:
    pass
