import os
import numpy as np
from imutils import perspective
from imutils import contours
import cv2
import imutils
from string import ascii_uppercase

# def get_title(image):
image = cv2.imread('../img/testccc.PNG')
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (25, 7), 0)

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
title_hight = 0
title_y_mid = 0
title = 0

for cnt in cnts:
    x, y, w, h = cv2.boundingRect(cnt)
    box = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype="int")
    if y < highest:
        highest = y
        title_hight = h
        title_y_mid = round(y - h / 2)
        title = [box]
    if 10 < y - highest < 10 and x < leftmost:
        highest = y
        title_hight = h
        title_y_mid = round(y-h/2)
        title = [box]


for cnt in cnts:
    x, y, w, h = cv2.boundingRect(cnt)
    box = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype="int")
    print(y - title_hight)
    if y - highest < 64:
        title = title + [box]

for cnt in title:
    cv2.drawContours(image, [cnt.astype("int")], -1, (0, 0, 255), 2)

cv2.imshow('image', image)
cv2.waitKey()
cv2.destroyAllWindows()