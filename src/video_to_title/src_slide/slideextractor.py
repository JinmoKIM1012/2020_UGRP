import time
import os
import argparse
import cv2
import imutils
import changedetection
import subprocess
import get_sentece
import contour_pdf
import tensorflow as tf

# parser = argparse.ArgumentParser()
# parser.add_argument("-v", "--video", dest="video", required=True,
#                     help="the path to your video file to be analyzed")
# parser.add_argument("-o", "--output", dest="output", default="../img",
#                     help="the output pdf file where the extracted slides will be saved")
# parser.add_argument("-s", "--step-size", dest="step-size", default=20,
#                     help="the amount of frames skipped in every iteration")
# parser.add_argument("-p", "--progress-interval", dest="progress-interval", default=1,
#                     help="how many percent should be skipped between each progress output")
# parser.add_argument("-d", "--debug", dest="debug", default=False, action="store_true",
#                     help="the path to your video file to be analyzed")
# args = vars(parser.parse_args())



class SlideExtractor:
    slideCounter = 10
    result = []

    # def __init__(self, debug, vidpath, output, stepSize, progressInterval):
    def __init__(self):
        self.vidpath = "../datastr1.mp4"
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

        self.detection.start(cv2.VideoCapture(self.vidpath.strip()))

        #subprocess.call('python img_dedup.py -o "' + self.output + '"', shell=True)
        self.listImg()
        print("SlideExtractor Done.")
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")

        file_names = os.listdir(self.output)
        i = 0
        for name in file_names:
            image = cv2.imread(os.path.join(self.output, name))
            title = contour_pdf.image_to_words()

            image, words = title.pdf_to_title(image)

            get_word = get_sentece.pdf_to_sentence()
            sentence = get_word.get_word(words)

            print(sentence)

            f = open("../output.txt", 'a')
            f.write("page" + str(i) + "-----" + sentence +"\n")
            f.close()
            i = i + 1

            tf.reset_default_graph()
        # image = cv2.imread('test7.jpg')
        #
        # title = contour_pdf.image_to_words()
        # image, words = title.pdf_to_title(image)


# main = SlideExtractor(args['debug'], args['video'], args['output'],
#                       args['step-size'], args['progress-interval'])
main = SlideExtractor()
main.start()