import os
from imagededup.methods import DHash
from imagededup.methods import WHash
from imagededup.methods import PHash
from imagededup.methods import CNN
if __name__ == '__main__':

    # phasher = DHash()
    # duplicates = phasher.find_duplicates_to_remove(image_dir='./img', max_distance_threshold=8)
    # for i in duplicates:
    #     os.remove('./img/' + i)
    #
    # phasher = WHash()
    # duplicates = phasher.find_duplicates_to_remove(image_dir='./img', max_distance_threshold=8)
    # for i in duplicates:
    #     os.remove('./img/' + i)

    phasher = CNN()
    duplicates = phasher.find_duplicates_to_remove(image_dir='./img', min_similarity_threshold=0.95)
    for i in duplicates:
        os.remove('./img/' + i)

    # phasher = PHash()
    # duplicates = phasher.find_duplicates_to_remove(image_dir='./img', max_distance_threshold=8)
    # for i in duplicates:
    #     os.remove('./img/' + i)