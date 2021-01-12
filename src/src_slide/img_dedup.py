import os
from imagededup.methods import DHash
from imagededup.methods import WHash
from imagededup.methods import PHash
from imagededup.methods import CNN
from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-o", "--output", dest="output", default="../img",
                    help="the output pdf file where the extracted slides will be saved")
args = vars(parser.parse_args())

class Hash:
    def __init__(self, output):
        self.output = output

    def start(self):
        CNN_hasher = CNN()
        p = Path(self.output)
        duplicates = CNN_hasher.find_duplicates_to_remove(image_dir=p, min_similarity_threshold=0.95)
        for i in duplicates:
            os.remove(p, i)


if __name__ == '__main__':
    main = Hash(args['output'])
    main.start()

    # output = '../img'
    # p = Path(output)
    # cnn_encoder = CNN()
    # encodings = cnn_encoder.encode_images(image_dir=p)
    # duplicates = cnn_encoder.find_duplicates_to_remove(encodings, min_similarity_threshold=0.95)
    # for i in duplicates:
    #     os.remove(output, i)
    #
    #
    # phasher = WHash()
    # duplicates = phasher.find_duplicates_to_remove(image_dir='./img', max_distance_threshold=8)
    # for i in duplicates:
    #     os.remove('./img/' + i)