import time
# import datetime
import os
import argparse
import cv2
import imutils
# import img2pdf
import changedetection
# import duplicatehandler
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--video", dest="video", required=True,
                    help="the path to your video file to be analyzed")
parser.add_argument("-o", "--output", dest="output", default="slides.pdf",
                    help="the output pdf file where the extracted slides will be saved")
parser.add_argument("-s", "--step-size", dest="step-size", default=20,
                    help="the amount of frames skipped in every iteration")
parser.add_argument("-p", "--progress-interval", dest="progress-interval", default=1,
                    help="how many percent should be skipped between each progress output")
parser.add_argument("-d", "--debug", dest="debug", default=False, action="store_true",
                    help="the path to your video file to be analyzed")
args = vars(parser.parse_args())



class SlideExtractor:
    slideCounter = 0
    result = []

    def __init__(self, debug, vidpath, output, stepSize, progressInterval):
        self.vidpath = vidpath
        self.output = output
        self.detection = changedetection.ChangeDetection(
            stepSize, progressInterval, debug)
        # self.dupeHandler = duplicatehandler.DuplicateHandler(1)

    # def strfdelta(self, tdelta, fmt):
    #     d = {"days": tdelta.days}
    #     d["hours"], rem = divmod(tdelta.seconds, 3600)
    #     d["minutes"], d["seconds"] = divmod(rem, 60)
    #     return fmt.format(**d)

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

#지금은 쓸모없는 함수. 앞으로도 없을 듯.
    # def checkRatio(self, frame):#이전엔 프레임크기 맞추는 용. 지금은 컨투어 올바르게 잡는 용도.
    #     if self.ratioXY == 0:#첫 슬라이드라면 바로 통과.
    #         self.ratioXY = int(frame.shape[0] / frame.shape[1] * 20)#20은 임의의 수.정확도.
    #         return True
    #     if self.ratioXY == int(frame.shape[0] / frame.shape[1] * 20):
    #         return True
    #     return False

        #ratio = frame.shape[1] / frame.shape[0]
        #return ratio >= min and ratio <= max

    def onTrigger(self, frame):
        frame = self.cropImage(frame)
        if frame is not None:
            # if self.dupeHandler.check(frame):
            #     print("Found a new slide!")
            self.saveSlide(frame)

#이건 슬라이드를 jpg로 하나씩 저장하는 함수
    def saveSlide(self, slide):
        self.result.append(slide)

        # if not os.path.exists("asdf"):
        #     os.makedirs("asdf")
        # print("Saving slide " + str(self.slideCounter) + "...")
        # cv2.imwrite(os.path.join(
        #     "asdf", str(self.slideCounter) + ".jpg"), slide)
        # self.slideCounter += 1

    # def onProgress(self, percent, pos):
    #     elapsed = time.time() - self.startTime
    #     eta = (elapsed / percent) * (100 - percent)
    #     fps = pos / elapsed
    #     etaString = self.strfdelta(datetime.timedelta(seconds=eta),
    #                                "{hours}h {minutes}min {seconds}s")
    #     print("progress: ~%d%% @ %d fps | about %s left" %
    #           (percent, fps, etaString))

    # def convertToPDF(self):
    #     imgs = []
    #     for i in self.dupeHandler.entries:
    #         imgs.append(cv2.imencode('.jpg', i)[1].tostring())
    #
    #     with open(self.output, "wb") as f:
    #         f.write(img2pdf.convert(imgs))

    def start(self):
        self.detection.onTrigger += self.onTrigger
        # self.detection.onProgress += self.onProgress

        # self.startTime = time.time()

        self.detection.start(cv2.VideoCapture(self.vidpath.strip()))

        subprocess.call('python sort.py', shell=True)

        # print("Saving PDF...")
        # self.convertToPDF()

        print("SlideExtractor Done.")


main = SlideExtractor(args['debug'], args['video'], args['output'],
                      args['step-size'], args['progress-interval'])
main.start()