import sys
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QVideoFrame, QAbstractVideoSurface, QAbstractVideoBuffer, QVideoSurfaceFormat
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import os
import os.path as osp
import threading
import urllib.request
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests

import cv2
import numpy as np

import tensorflow as tf

import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from slideextractor import *
from get_sentence import *
from contour_pdf import *

class VideoFrameGrabber(QAbstractVideoSurface):
    frameAvailable = pyqtSignal(QImage)

    def __init__(self, widget: QWidget, parent: QObject):
        super().__init__(parent)

        self.widget = widget

    def supportedPixelFormats(self, handleType):
        return [QVideoFrame.Format_ARGB32, QVideoFrame.Format_ARGB32_Premultiplied,
                QVideoFrame.Format_RGB32, QVideoFrame.Format_RGB24, QVideoFrame.Format_RGB565,
                QVideoFrame.Format_RGB555, QVideoFrame.Format_ARGB8565_Premultiplied,
                QVideoFrame.Format_BGRA32, QVideoFrame.Format_BGRA32_Premultiplied, QVideoFrame.Format_BGR32,
                QVideoFrame.Format_BGR24, QVideoFrame.Format_BGR565, QVideoFrame.Format_BGR555,
                QVideoFrame.Format_BGRA5658_Premultiplied, QVideoFrame.Format_AYUV444,
                QVideoFrame.Format_AYUV444_Premultiplied, QVideoFrame.Format_YUV444,
                QVideoFrame.Format_YUV420P, QVideoFrame.Format_YV12, QVideoFrame.Format_UYVY,
                QVideoFrame.Format_YUYV, QVideoFrame.Format_NV12, QVideoFrame.Format_NV21,
                QVideoFrame.Format_IMC1, QVideoFrame.Format_IMC2, QVideoFrame.Format_IMC3,
                QVideoFrame.Format_IMC4, QVideoFrame.Format_Y8, QVideoFrame.Format_Y16,
                QVideoFrame.Format_Jpeg, QVideoFrame.Format_CameraRaw, QVideoFrame.Format_AdobeDng]

    def isFormatSupported(self, format):
        imageFormat = QVideoFrame.imageFormatFromPixelFormat(format.pixelFormat())
        size = format.frameSize()

        return imageFormat != QImage.Format_Invalid and not size.isEmpty() and \
               format.handleType() == QAbstractVideoBuffer.NoHandle

    def start(self, format: QVideoSurfaceFormat):
        imageFormat = QVideoFrame.imageFormatFromPixelFormat(format.pixelFormat())
        size = format.frameSize()

        if imageFormat != QImage.Format_Invalid and not size.isEmpty():
            self.imageFormat = imageFormat
            self.imageSize = size
            self.sourceRect = format.viewport()

            super().start(format)

            self.widget.updateGeometry()
            self.updateVideoRect()

            return True
        else:
            return False

    def stop(self):
        self.currentFrame = QVideoFrame()
        self.targetRect = QRect()

        super().stop()

        self.widget.update()

    def present(self, frame):
        if frame.isValid():
            cloneFrame = QVideoFrame(frame)
            cloneFrame.map(QAbstractVideoBuffer.ReadOnly)
            image = QImage(cloneFrame.bits(), cloneFrame.width(), cloneFrame.height(),
                           QVideoFrame.imageFormatFromPixelFormat(cloneFrame.pixelFormat()))
            self.frameAvailable.emit(image)  # this is very important
            cloneFrame.unmap()

        if self.surfaceFormat().pixelFormat() != frame.pixelFormat() or \
                self.surfaceFormat().frameSize() != frame.size():
            self.setError(QAbstractVideoSurface.IncorrectFormatError)
            self.stop()

            return False
        else:
            self.currentFrame = frame
            self.widget.repaint(self.targetRect)

            return True

    def updateVideoRect(self):
        size = self.surfaceFormat().sizeHint()
        size.scale(self.widget.size().boundedTo(size), Qt.KeepAspectRatio)

        self.targetRect = QRect(QPoint(0, 0), size)
        self.targetRect.moveCenter(self.widget.rect().center())

    def paint(self, painter):
        if self.currentFrame.map(QAbstractVideoBuffer.ReadOnly):
            oldTransform = self.painter.transform()

        if self.surfaceFormat().scanLineDirection() == QVideoSurfaceFormat.BottomToTop:
            self.painter.scale(1, -1)
            self.painter.translate(0, -self.widget.height())

        image = QImage(self.currentFrame.bits(), self.currentFrame.width(), self.currentFrame.height(),
                       self.currentFrame.bytesPerLine(), self.imageFormat)

        self.painter.drawImage(self.targetRect, image, self.sourceRect)

        self.painter.setTransform(oldTransform)

        self.currentFrame.unmap()

class VideoWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        # super(VideoWindow, self).__init__(parent)
        self.setWindowTitle("PyQt5 Media Player")
        self.setGeometry(250, 100, 1500, 800)
        self.search_word = None
        self.counter = 0
        self.capturemode = False

        self.r1 = QRubberBand(QRubberBand.Line, self)
        self.r2 = QRubberBand(QRubberBand.Line, self)
        self.r3 = QRubberBand(QRubberBand.Line, self)
        self.r4 = QRubberBand(QRubberBand.Line, self)

        self.init_ui()

        thread = threading.Thread(target=self.init_video)
        thread.daemon = True
        thread.start()

        self.search_button1.clicked.connect(self.get_search_word)
        self.run_button.clicked.connect(self.searchword)

        # self.statusbar = self.statusBar()
        self.setMouseTracking(True)
        self.click = False
        self.x1, self.y1 = -1, -1

        self.gray = []
        self.cropped_imgs = []

        self.show()

    def init_ui(self):
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.videowidget = QVideoWidget()
        self.videoFrame = QVideoFrame()
        # self.mediaPlayer.setVideoOutput(self.videowidget)
        self.openBtn = QPushButton('Open Video')
        self.playBtn = QPushButton()
        self.playBtn.setEnabled(False)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.scrshotBtn = QPushButton('ScreenShot')
        self.scrshotBtn.setEnabled(False)
        self.searchBtn = QPushButton('Search')
        self.searchBtn.setEnabled(False)
        self.searchBtn.clicked.connect(self.get_search_image)

        self.captureBtn = QPushButton('Capture')
        self.captureBtn.setEnabled(False)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.label = QLabel()
        self.label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # create hbox layout
        playbar_Layout = QHBoxLayout()
        playbar_Layout.setContentsMargins(0, 0, 0, 0)

        # set widgets to the hbox layout
        playbar_Layout.addWidget(self.openBtn)
        playbar_Layout.addWidget(self.playBtn)
        playbar_Layout.addWidget(self.slider)

        capture_Layout = QHBoxLayout()
        capture_Layout.addWidget(self.scrshotBtn)
        capture_Layout.addWidget(self.searchBtn)
        capture_Layout.addWidget(self.captureBtn)

        play_Layout = QVBoxLayout()
        play_Layout.addWidget(self.videowidget)
        play_Layout.addLayout(playbar_Layout)
        play_Layout.addLayout(capture_Layout)
        play_Layout.addWidget(self.label)

        self.print_result = QTextBrowser()
        self.print_result.setOpenExternalLinks(True)
        self.print_time = QTextBrowser()
        self.print_result.setFixedWidth(400)
        self.print_time.setFixedWidth(400)
        self.search_word_line = QLineEdit()
        self.search_word_line.setFixedWidth(400)
        self.search_button1 = QPushButton('Input')
        self.run_button = QPushButton('run')
        self.run_button.setEnabled(False)

        search_Layout = QVBoxLayout()
        search_Layout.addWidget(self.print_result)
        search_Layout.addWidget(self.print_time)
        search_Layout.addWidget(self.search_word_line)
        search_Layout.addWidget(self.search_button1)
        search_Layout.addWidget(self.run_button)

        # whole_Layout = QHBoxLayout()
        whole_Layout = QGridLayout()
        whole_Layout.addLayout(play_Layout, 0, 0)
        whole_Layout.addLayout(search_Layout, 0, 1)

        self.wid = QWidget(self)
        self.setCentralWidget(self.wid)

        # self.setLayout(whole_Layout)
        self.wid.setLayout(whole_Layout)

    def init_video(self):
        self.openBtn.clicked.connect(self.open_file)
        self.playBtn.clicked.connect(self.play_video)
        self.slider.sliderMoved.connect(self.set_position)
        self.scrshotBtn.clicked.connect(self.screenshotCall)

        self.mediaPlayer.stateChanged.connect(self.mediastate_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)

        self.captureBtn.clicked.connect(self.capture_mode)
        # self.print_time.setText("")

    def capture_mode(self):
        self.capturemode = not self.capturemode
        if self.scrshotBtn.isEnabled():
            self.scrshotBtn.setEnabled(False)
            self.searchBtn.setEnabled(True)

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Video")
        if filename != '':
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
            self.playBtn.setEnabled(True)
            self.captureBtn.setEnabled(True)
            slideextrac = SlideExtractor(filename)
            self.print_time.setText("")
            self.timestamp, self.title = slideextrac.start()
            for i in range(len(self.title)):
                self.print_time.append(str(self.timestamp[i]))
                self.print_time.append(self.title[i])
                self.print_time.append("")

    def screenshotCall(self):
        # Call video frame grabber
        self.grabber = VideoFrameGrabber(self.videowidget, self)
        self.mediaPlayer.setVideoOutput(self.grabber)
        self.grabber.frameAvailable.connect(self.process_frame)
        self.label.setText("Taking a screenshot of image " + str(self.counter) + " ....")
        self.mediaPlayer.pause()

    def play_video(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()

        else:
            self.mediaPlayer.play()
            self.mediaPlayer.setVideoOutput(self.videowidget)

    def mediastate_changed(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause)
            )
        else:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay)
            )

    def position_changed(self, position):
        self.slider.setValue(position)

    def duration_changed(self, duration):
        self.slider.setRange(0, duration)

    def set_position(self, position):
        self.mediaPlayer.setPosition(position)

    def handle_errors(self):
        self.playBtn.setEnabled(False)
        self.label.setText("Error: " + self.mediaPlayer.errorString())

    def get_search_word(self):
        self.search_word = self.search_word_line.text()
        self.run_button.setEnabled(True)

    def get_search_image(self):
        # print(self.cropped_imgs)
        # cv2.imshow("sds", self.cropped_imgs)
        title = contour_pdf.image_to_words()
        image, words = title.cropimg_to_word(self.cropped_imgs)

        get_word = pdf_to_sentence()
        sentence = get_word.get_word(words)

        self.search_word_line.setText(sentence)
        self.search_word = sentence# self.search_word_line.text()
        self.run_button.setEnabled(True)
        tf.reset_default_graph()

    def searchword(self):
        if self.search_word == '' or self.search_word is None:
            self.print_result.setText("Please insert word")
            self.run_button.setEnabled(False)

        else:
            quo = urllib.parse.quote(self.search_word)
            base = 'https://www.google.com/search?client=firefox-b-d&q='+quo
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'}

            data = requests.get(base, headers=headers)
            html = data.text

            # html = urllib.request.urlopen(base).read()
            soup = BeautifulSoup(html, 'lxml')

            infor = soup.select('.yuRUbf')

            self.print_result.setText("Result\n")

            for i in infor:
                self.print_result.append(i.select_one('.LC20lb.DKV0Md').text)
                self.print_result.append(i.a.attrs["href"])
                self.print_result.append("")

    def process_frame(self, image):
        # Save image here
        image.save('sdfs.jpg')
        self.convertQImageToMat(image)
        self.crop_words()

        self.counter = self.counter+1
        self.searchBtn.setEnabled(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.capturemode\
                and self.videowidget.x() < event.x() < self.videowidget.x() + self.videowidget.width() \
                and self.videowidget.y() < event.y() < self.videowidget.y() + self.videowidget.height():
            self.click = True
            self.x1, self.y1 = event.x(), event.y()

            self.origin = event.pos()
            self.r1.setGeometry(self.x1 - 5, self.y1 - 5, 10, 10)
            self.r2.setGeometry(self.x1 + QSize().width() - 5, self.y1 - 5, 10, 10)
            self.r3.setGeometry(self.x1 - 5, self.y1 - 5 + QSize().height(), 10, 10)
            self.r4.setGeometry(self.x1 + QSize().width() - 5, self.y1 - 5 + QSize().height(), 10, 10)
            self.r1.show()
            self.r2.show()
            self.r3.show()
            self.r4.show()
        QWidget.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.r1.isVisible() and self.capturemode\
                and self.videowidget.x() < event.x() < self.videowidget.x() + self.videowidget.width() \
                and self.videowidget.y() < event.y() < self.videowidget.y() + self.videowidget.height():
            self.x = event.x() - self.x1
            self.y = event.y() - self.y1

            self.r1.setGeometry(self.x1 - 5, self.y1 - 5, 10, 10)
            self.r2.setGeometry(self.x1 + self.x - 5, self.y1 - 5, 10, 10)
            self.r3.setGeometry(self.x1 - 5, self.y1 - 5 + self.y, 10, 10)
            self.r4.setGeometry(self.x1 + self.x - 5, self.y1 - 5 + self.y, 10, 10)
        QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.r1.isVisible() and self.capturemode\
                and self.videowidget.x() < event.x() < self.videowidget.x() + self.videowidget.width() \
                and self.videowidget.y() < event.y() < self.videowidget.y() + self.videowidget.height():
            # print("첫 클릭 : (" + str(self.x1) + ", " + str(self.y1) + "), 마지막 클릭 : (" + str(event.x()) + ", " + str(
            #     event.y()) + ")")
            self.scrshotBtn.setEnabled(True)
        QWidget.mouseReleaseEvent(self, event)

    def convertQImageToMat(self, incomingImage):
        '''  Converts a QImage into an opencv MAT format  '''
        # incomingImage = incomingImage.convertToFormat(4)
        #
        # self.width = incomingImage.width()
        # self.height = incomingImage.height()
        #
        self.diff = self.videowidget.height() - (self.videowidget.width() / incomingImage.width() * incomingImage.height())
        #
        # ptr = incomingImage.bits()
        # ptr.setsize(incomingImage.byteCount())
        # arr = np.array(ptr).reshape(self.height, self.width, 4)  # Copies the data
        incomingImage.save("qimage.jpg")
        arr = cv2.imread("qimage.jpg")
        arr = cv2.resize(arr, dsize=(self.videowidget.width(), self.videowidget.height() - int(self.diff)))

        self.gray = arr

    def crop_words(self):
        if self.x > 0 and self.y > 0:
            corx = self.x1 - self.videowidget.x()
            cory = self.y1 - self.videowidget.y() - (self.diff / 2)

        elif self.x > 0 and self.y < 0:
            corx = self.x1
            cory = self.y1 + self.y

        elif self.x < 0 and self.y > 0:
            corx = self.x1 + self.x
            cory = self.y1
        elif self.x < 0 and self.y < 0:
            corx = self.x1 + self.x
            cory = self.y1 + self.y

        w = abs(self.x)
        h = abs(self.y)
        # cv2.imshow("1234", self.gray)
        self.cropped_imgs = self.gray[int(cory): int(cory + h), int(corx): int(corx + w)]
        # cv2.imshow("sdfdsf", self.cropped_imgs)
        # cv2.waitKey()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoWindow()
    player.show()
    sys.exit(app.exec_())