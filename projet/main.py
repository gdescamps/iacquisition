from fastapi import FastAPI, File, UploadFile, Query
from typing import List, Union, Optional
import io
import requests

from api.JobDocument import *
from api.CVDocument import *
from api.utils import *

from ocr.OCR import *
from ocr.AzureOCR import *
from ocr.TesseractOCR import *
from ocr.preprocessing import *


app = FastAPI()


def set_key():
    os.environ["VISION_KEY"] = "31448cea13684055978a88efcb82112c"
    os.environ["VISION_ENDPOINT"] = "https://iacquisition.cognitiveservices.azure.com/"


set_key()


@app.post("/TesseractOCR/")
def tesseract_ocr(file: UploadFile = File(...)):
    bytes = file.file.read()
    return get_ocr_tesseract(bytes, output="dict")


@app.post("/AzureOCR/")
def azure_ocr(file: UploadFile = File(...)):
    bytes = file.file.read()
    subscription_key = os.environ["VISION_KEY"]
    endpoint = os.environ["VISION_ENDPOINT"]

    return get_ocr_azure_with_regions(
        endpoint=endpoint, key=subscription_key, byte=bytes
    )


@app.post("/PreprocessCV/")
async def preprocess_cv(file: UploadFile = File(...)):
    bytes = file.file.read()
    document_cv = CVDocument()

    liste_page_content = convert_from_bytes(bytes)
    for i in range(len(liste_page_content)):
        img_ = np.asarray(liste_page_content[i])
        document_cv.images["Page " + str(i + 1)] = img_

    document_cv.preprocess()

    return document_cv.region_bounding_box


@app.post("/TesseractOCRCV/")
async def tesseract_ocr_cv(file: UploadFile = File(...)):
    bytes = file.file.read()
    document_cv = CVDocument()

    liste_page_content = convert_from_bytes(bytes)
    for i in range(len(liste_page_content)):
        img_ = np.asarray(liste_page_content[i])
        document_cv.images["Page " + str(i + 1)] = img_

    document_cv.PreOCRProcessing()

    document_cv.ocr(ocr_engine="tesseract")

    return document_cv.text


@app.post("/JobDescExtraction/")
def jobdesc_extraction(file: UploadFile = File(...), ocr: OCR = OCR.tesseract):
    bytes = file.file.read()

    if ocr.value == "Tesseract":
        resultat_ocr = get_ocr_tesseract(byte=bytes, output="data.frame")
        document = JobDescDocument()
        document.nb_pages = len(resultat_ocr)
        document.id = file.filename
        document.pages_content = resultat_ocr
        document.postprocess_ocr()
        document.extraction()
        document.extraction_formulaire()

    else:
        subscription_key = os.environ["VISION_KEY"]
        endpoint = os.environ["VISION_ENDPOINT"]
        resultat_ocr = get_ocr_azure(
            endpoint=endpoint, key=subscription_key, byte=bytes
        )
        document = JobDescDocument()
        document.nb_pages = len(resultat_ocr)
        document.id = file.filename
        document.pages_content = resultat_ocr
        document.extraction_azure()
        # document.extraction_formulaire_azure()

    return document.entities
