from __future__ import division
from __future__ import print_function

import cv2
from DataLoader import Batch
from Model import Model
from SamplePreprocessor import preprocess
import contour_pdf

class pdf_to_sentence:
    def __init__(self):
        self.image = 0
        self.sentence = ""
        self.fnCharList = "../model/charList.txt"

    def infer(self, model, img):
        #"recognize text in image provided by file path"
        self.image = preprocess(img, Model.imgSize)
        batch = Batch(None, [self.image])
        (recognized, probability) = model.inferBatch(batch, True)
        self.sentence = self.sentence + recognized[0] + " "
        #print('Recognized:', '"' + recognized[0] + '"')
        #print('Probability:', probability[0])

    def get_word(self, imgs):
        model = Model(open(self.fnCharList).read(), 0, mustRestore=True, dump=False)
        for img in imgs:
            self.infer(model, img)
        return self.sentence

"""
if __name__ == '__main__':
    image = cv2.imread('test7.jpg')

    title = contour_pdf.image_to_words()
    image, words = title.pdf_to_title(image)

    cv2.imshow('test', image)

    get_word = pdf_to_sentence()
    sentence = get_word.get_word(words)

    print(sentence)
    cv2.waitKey()
    cv2.destroyAllWindows()
"""