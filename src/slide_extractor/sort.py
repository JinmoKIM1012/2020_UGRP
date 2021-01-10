import os
from imagededup.methods import PHash
if __name__ == '__main__':

    phasher = PHash()
    duplicates = phasher.find_duplicates_to_remove(image_dir='./asdf', max_distance_threshold=16)
    for i in duplicates:
        os.remove('./asdf/' + i)
