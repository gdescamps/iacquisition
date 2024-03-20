import numpy as np
from enum import Enum
import base64
from mimetypes import guess_type


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


# Your earlier function, slightly modified to use bytes directly.
def image_to_data_url(image_bytes, image_name):
    mime_type, _ = guess_type(image_name)
    if mime_type is None:
        mime_type = "application/octet-stream"
    base64_encoded_data = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{base64_encoded_data}"
