# import time
import numpy as np
import cv2
import imutils
# import eventhook

class EventHook(object):

    def __init__(self):
        self.__handlers = []

    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.__handlers.remove(handler)
        return self

    def fire(self, *args, **keywargs):
        for handler in self.__handlers:
            handler(*args, **keywargs)

    def clearObjectHandlers(self, inObject):
        for theHandler in self.__handlers:
            if theHandler.im_self == inObject:
                self -= theHandler



class ChangeDetection:
    # minimum contour area (1000)
    minArea = 1000
    # maximum frames before firstFrame reset (3)
    #maxIdle = 3
    # frame step size
    stepSize = 20
    # amount of percent between each progress event
    progressInterval = 1
    # event that fires when motion is confirmed
    onTrigger = EventHook()
    # event that gives feedback of how far the detection is
    # onProgress = eventhook.EventHook()

    def __init__(self, stepSize, progressInterval, showDebug=False):
        self.stepSize = int(stepSize) #고침. stepSize -> int(stepSize)
        self.progressInterval = progressInterval
        self.showDebug = showDebug
        #강의영상으로 한정되어있기 떄문에 짧게 넘기는 슬라이드는 중요도를 낮춘다.
        # 그리고, maxIdle을 고정시키는 것은 멍청한 짓이므로 stepSize에 반비례하게 설정한다.
        #self.maxIdle = 200 / int(stepSize)

    def start(self, camera):
        firstFrame = None
        # prevOG = None
        # amount of contours
        contAmount = 0

        # amount of idle frames that were the same
        # used to determine if that frame should become the new firstFrame
        idleCount = 0

        # current pos in vid
        currentPosition = 0
        lastProgress = 0

        # startTime = time.time()

        print('change detection initiated')

        totalFrames = camera.get(cv2.CAP_PROP_FRAME_COUNT) - 1

        while currentPosition < totalFrames: #동영상이 끝날 때까지
            (grabbed, frame) = camera.read()
            if frame is None:
                break

            original = frame.copy()

            # convert grabbed frame to gray and blur
            frame = imutils.resize(frame, width=500)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            if firstFrame is None:
                firstFrame = np.zeros(gray.shape, np.uint8)

            frameDelta = cv2.absdiff(firstFrame, gray)  # 현재frame과 fristFrame의 차이점 구하기
            thresh = self.calcThresh(frameDelta)
            cnts = self.detectContours(thresh)

            # firstFrame에는 슬라이드 첫 장면, 즉 낙서가 없는 장면 저장.
            # prevFrame에는 슬라이드 마지막 장면, 즉 낙서가 다 포함된 장면 저장.
            # 낙서를 다 지우는 장면에 대한 예외처리를 위해 gray는 firstFrame과 비교한다.
            if cv2.countNonZero(thresh) > frame.shape[0] * frame.shape[1] / 8:
                self.onTrigger.fire(original)

            firstFrame = gray
            progress = (currentPosition / totalFrames) * 100

            # 터미널에 진행퍼센트 출력
            # if progress - lastProgress >= self.progressInterval:
            #     lastProgress = progress
            #     self.onProgress.fire(progress, currentPosition)

            camera.set(1, min(currentPosition +
                              self.stepSize, totalFrames))
            currentPosition = camera.get(cv2.CAP_PROP_POS_FRAMES)

            if self.showDebug:
                # loop over the contours
                for c in cnts:
                    # compute the bounding box for the contour, draw it on the frame
                    (x, y, w, h) = cv2.boundingRect(c)
                    cv2.rectangle(frame, (x, y), (x + w, y + h),
                                  (0, 255, 0), 2)

                cv2.putText(frame, "contours: " + str(contAmount),
                            (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                cv2.putText(frame, "idle: " + str(idleCount), (140, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                cv2.putText(frame, "frame: " + str(currentPosition), (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                cv2.imshow("Frame", frame)
                cv2.imshow("Delta", frameDelta)
                cv2.imshow("Threshold", thresh)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break

        camera.release()
        cv2.destroyAllWindows()

    def calcThresh(self, frame):
        thresh = cv2.threshold(frame, 10, 255, cv2.THRESH_BINARY)[1]    #흑백사진으로.
        return cv2.dilate(thresh, None, iterations=2)                  #ppt의 object들 굵어지게 함.

    def detectContours(self, thresh):
        cnts = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) #가장 바깥쪽 컨투어를 찾는다.
        cnts = cnts[0] if imutils.is_cv2() else cnts[1]

        validCnts = []

        # loop over the contours
        for c in cnts:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) < self.minArea:
                continue

            validCnts.append(c)

        return validCnts