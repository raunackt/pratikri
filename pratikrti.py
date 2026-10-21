import os

from krita import DockWidget
from PyQt5.QtWidgets import (
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PratikrtiDocker(DockWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Pratikrti")

        container = QWidget(self)
        layout = QVBoxLayout(container)

        layout.addWidget(QLabel("Pratikrti"))
        layout.addWidget(
            QLabel("Next: load a pattern to fill selection.").setWordWrap(True)
        )

        self.file_label = QLabel("No pattern selected")
        self.file_label.setWordWrap(True)
        layout.addWidget(self.file_label)

        choose_btn = QPushButton("Choose Pattern")
        layout.addWidget(choose_btn)
        choose_btn.clicked.connect(self.choose_pattern)

        self.repeat_btn = QPushButton("Repeat Pattern")
        self.repeat_btn.setEnabled(False)
        self.repeat_btn.clicked.connect(self.repeat_pattern)
        layout.addWidget(self.repeat_btn)

        self.setWidget(container)

    def choose_pattern(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Pattern Image",
            "",
            "Images (*.png, *.jpg, *.jpeg, *.tif, *.tiff, *.webp)"
        )

        if not path:
            return

        self.patter_path = path
        self.file_label.setText(os.path.basename(path))
        self.repeat_btn.setEnabled(True)

    def repeat_pattern(self):
        if not self.patter_path or not os.path.isfile(
            self.patter_path
        ):
            QMessageBox.warning(
                self,
                "Pratikrti",
                "Please choose a valid file."
            )
            return

        QMessageBox.information(
            self,
            "Pratikrti",
            "Pattern image loaded successfully: \n" + self.patter_path
        )


    def canvasChanged(self, canvas):
        pass


from krita import Krita


class PratikrtiExtension:
    pass
