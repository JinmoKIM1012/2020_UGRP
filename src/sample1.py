import sys, os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QRubberBand, QPushButton
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()

        self.setAlignment(Qt.AlignCenter)
        self.setText('\n\n Drop Image Here \n\n')
        self.setStyleSheet('''
            QLabel{
                border: 4px dashed #aaa
            }
        ''')

    def setPixmap(self, image):
        super().setPixmap(image)


class AppDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(400, 400)
        self.setAcceptDrops(True)

        mainLayout = QVBoxLayout()

        self.photoViewer = ImageLabel()
        mainLayout.addWidget(self.photoViewer)

        self.setLayout(mainLayout)
        self.rubberband = QRubberBand(QRubberBand.Rectangle, self)

        self.click = False
        self.x1, self.y1 = -1, -1

    def dragEnterEvent(self, event):
        if event.mimeData().hasImage:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasImage:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasImage:
            global img
            event.setDropAction(Qt.CopyAction)
            file_path = event.mimeData().urls()[0].toLocalFile()
            self.set_image(file_path)

            event.accept()
        else:
            event.ignore()

    def set_image(self, file_path):
        self.photoViewer.setPixmap(QPixmap(file_path))


    #마우스 이벤트

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.click = True
            self.x1, self.y1 = event.x(), event.y()

            self.origin = event.pos()
            self.rubberband.setGeometry(self.x1, self.y1, QSize().width(), QSize().height())
            self.rubberband.show()

    def mouseMoveEvent(self, event):
        if self.rubberband.isVisible():
            self.rubberband.setGeometry(QRect(self.origin, event.pos()).normalized())
        QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.rubberband.isVisible():
            print("첫 클릭 : (" + str(self.x1) + ", " + str(self.y1) + "), 마지막 클릭 : (" + str(event.x()) + ", " + str(event.y()) + ")")

        QWidget.mouseReleaseEvent(self, event)

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    demo = AppDemo()
    demo.show()

    sys.exit(app.exec_())