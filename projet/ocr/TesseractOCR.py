import pandas as pd
import numpy as np
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes


def get_ocr_tesseract(byte, output: str):
    res = {}
    liste_page_content = convert_from_bytes(byte)
    for i in range(len(liste_page_content)):
        img_ = np.asarray(liste_page_content[i])
        PIL_image = Image.fromarray(np.uint8(img_)).convert("RGB")
        output_tesseract = pytesseract.image_to_data(PIL_image, output_type=output)
        res["Page " + str(i + 1)] = output_tesseract
    return res
