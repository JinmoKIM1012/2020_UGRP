import numpy as np
from imutils import contours
import cv2
import imutils

class image_to_words:
    def __init__(self):
        self.gray = 0
        self.title = []
        self.title_num = 0
        self.cropped_imgs = []
        self.check_word = []
        self.highest_y = 1000

    def convertQImageToMat(self, incomingImage):
        '''  Converts a QImage into an opencv MAT format  '''

        incomingImage = incomingImage.convertToFormat(4)

        width = incomingImage.width()
        height = incomingImage.height()

        ptr = incomingImage.bits()
        ptr.setsize(incomingImage.byteCount())
        arr = np.array(ptr).reshape(height, width, 4)  # Copies the data
        return arr

    def cropimg_to_word(self, Qimage):
        image = self.convertQImageToMat(Qimage)
        self.gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(image, (9, 9), 0)

        edged = cv2.Canny(blurred, 30, 150)
        edged = cv2.dilate(edged, None, iterations=1)
        edged = cv2.erode(edged, None, iterations=1)

        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = contours.sort_contours(cnts, method="left-to-right")[0]

        cnts = [x for x in cnts if cv2.contourArea(x) > 100]

        for cnt in cnts:
            x, y, w, h = cv2.boundingRect(cnt)
            box = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype="int")
            self.title_num = self.title_num + 1
            self.title.append(box)
            self.check_word.append(0)

        self.sorting()
        self.crop_words()

        #for cnt in self.title:
        #    cv2.drawContours(image, [cnt.astype("int")], -1, (0, 0, 255), 2)

        return self.cropped_imgs

    def pdf_to_title(self, image):
        self.gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(self.gray, (25, 7), 0)

        edged = cv2.Canny(blurred, 30, 150)
        edged = cv2.dilate(edged, None, iterations=1)
        edged = cv2.erode(edged, None, iterations=1)

        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = contours.sort_contours(cnts, method="left-to-right")[0]

        cnts = [x for x in cnts if cv2.contourArea(x) > 100]

        highest = 1000
        leftmost = 1000

        for cnt in cnts:
            x, y, w, h = cv2.boundingRect(cnt)
            if y < highest:
                highest = y
            if 10 < y - highest < 10 and x < leftmost:
                highest = y

        for cnt in cnts:
            x, y, w, h = cv2.boundingRect(cnt)
            box = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype="int")
            if y - highest < 64:
                self.title_num = self.title_num + 1
                self.title.append(box)
                self.check_word.append(0)

        self.sorting()
        self.crop_words()

        #for cnt in self.title:
        #    cv2.drawContours(image, [cnt.astype("int")], -1, (0, 0, 255), 2)

        return self.cropped_imgs

    def sorting(self):
        result = []
        check_words_num = 0
        while check_words_num != self.title_num:
            self.highest_y = 1000
            self.find_highest_word()
            # title : tl, tr, br, bl (x, y)

            i = 0
            for cnt in self.title:
                cnt_mid_y = round((cnt[0][1] + cnt[1][1] + cnt[2][1] + cnt[3][1]) / 4)
                if abs(self.highest_y - cnt_mid_y) < 10 and self.check_word[i] == 0:
                    result.append(cnt)
                    self.check_word[i] = 1
                    check_words_num = check_words_num + 1
                i = i + 1

        self.title = result

    def find_highest_word(self):
        i = 0
        for cnt in self.title:
            cnt_mid_y = round((cnt[0][1] + cnt[1][1] + cnt[2][1] + cnt[3][1]) / 4)
            if self.highest_y > cnt_mid_y and self.check_word[i] == 0:
                self.highest_y = cnt_mid_y
            i = i + 1

    def crop_words(self):
        for word in self.title:
            x = word[0][0]
            y = word[0][1]
            w = abs(word[0][0] - word[1][0])
            h = abs(word[0][1] - word[3][1])
            self.cropped_imgs.append(self.gray[y: y + h, x: x + w])

