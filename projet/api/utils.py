import numpy as np
from enum import Enum


class OCR(str, Enum):
    tesseract: str = "Tesseract"
    azure: str = "Azure"


def minimal_tuple(tuple1, tuple2):
    if tuple1[0] > tuple2[0]:
        return tuple2, "Profil", tuple1, "Mission"
    elif tuple2[0] > tuple1[0]:
        return tuple1, "Mission", tuple2, "Profil"
    else:
        if tuple1[1] > tuple2[1]:
            return tuple2, "Profil", tuple1, "Mission"
        else:
            return tuple1, "Mission", tuple2, "Profil"


def tuple_before(tuple1, tuple2):
    if tuple1[0] > tuple2[0]:
        return False
    elif tuple2[0] > tuple1[0]:
        return True
    else:
        if tuple1[1] > tuple2[1]:
            return False
        elif tuple2[1] > tuple1[1]:
            return True
