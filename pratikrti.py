from krita import DockWidget
from PyQt5.QtWidgets import (
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

        test_btn = QPushButton("Test Plugin")
        layout.addWidget(test_btn)

        test_btn.clicked.connect(self.test_plugin)
        self.setWidget(container)

    def test_plugin(self):
            QMessageBox.information(self, "Pratikrti", "saphalata! karyam karoti")

    def canvasChanged(self, canvas):
            pass


from krita import Krita


class PratikrtiExtension:
    pass
