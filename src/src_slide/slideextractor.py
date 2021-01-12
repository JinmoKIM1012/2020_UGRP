import time
import os
import argparse
import cv2
import imutils
import changedetection
import subprocess
import get_sentence
import contour_pdf
import tensorflow as tf


class SlideExtractor:
    slideCounter = 10
    result = []

    # def __init__(self, debug, vidpath, output, stepSize, progressInterval):
    def __init__(self, vidpath):
        # self.vidpath = "../datastr1.mp4"
        self.vidpath = vidpath
        self.output = "../img"
        self.detection = changedetection.ChangeDetection(
            5000, 1, False)
        # self.dupeHandler = duplicatehandler.DuplicateHandler(1)

    # crop image to slide size
    def cropImage(self, frame):
        min_area = (frame.shape[0] * frame.shape[1]) * (2 / 3)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)#회색으로 만들고
        thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)[1]#이미지 이진화(흑백)
        contours = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)#가장 큰 컨투어 찾기
        contours = contours[0] if imutils.is_cv2() else contours[1]#cv버전에 따라 컨투어 변환
        for cnt in contours:
            if cv2.contourArea(cnt) > min_area:
                x, y, w, h = cv2.boundingRect(cnt)
                crop = frame[y:y+h, x:x+w]
                return crop

    def onTrigger(self, frame):
        frame = self.cropImage(frame)
        if frame is not None:
            self.saveSlide(frame)

#save slide in directory
    def saveSlide(self, slide):
        print("Saving slide " + str(self.slideCounter - 10) + "...")
        cv2.imwrite(os.path.join(
            self.output, str(self.slideCounter) + ".jpg"), slide)
        self.slideCounter += 1
#list img after deduplication
    def listImg(self):
        file_names = os.listdir(self.output)

        i = 0
        for name in file_names:
            src = os.path.join(self.output, name)
            dst = str(i) + '.jpg'
            dst = os.path.join(self.output, dst)
            os.rename(src, dst)
            i += 1

    def clearImg(self):
        if not os.path.exists(self.output):
            os.makedirs(self.output)
        file_names = os.listdir(self.output)
        if file_names != None:
            for name in file_names:
                os.remove(os.path.join(self.output, name))

    def start(self):
        now = time.localtime()
        print("%04d/%02d/%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec))
        self.clearImg()
        self.detection.onTrigger += self.onTrigger

        self.video = cv2.VideoCapture(self.vidpath.strip())
        fps = self.video.get(cv2.CAP_PROP_FPS)
        timeStamp = self.detection.start(cv2.VideoCapture(self.vidpath.strip()))
        self.listImg()
        # print("SlideExtractor Done.")
        # print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")

        file_names = os.listdir(self.output)
        if len(file_names) > 1:
            subprocess.call('python ../src_slide/img_dedup.py -o "' + self.output + '"', shell=True)
        title_arr = []

        for name in file_names:
            image = cv2.imread(os.path.join(self.output, name))
            title = contour_pdf.image_to_words()

            image, words = title.pdf_to_title(image)

            get_word = get_sentence.pdf_to_sentence()
            sentence = get_word.get_word(words)

            # print(sentence)
            title_arr.append(sentence)

            tf.reset_default_graph()

        return timeStamp, title_arr
