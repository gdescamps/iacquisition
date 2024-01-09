from fastapi import FastAPI, File, UploadFile, Query, Response
from typing import List, Union, Optional
import io
from PIL import Image
import httpx

from LLM.extraction import *

from api.JobDocument import *
from api.CVDocument import *
from api.utils import *

from ocr.OCR import *
from ocr.AzureOCR import *
from ocr.TesseractOCR import *
from ocr.preprocessing import *

from PIL import Image


def get_image_bytes(image_path):
    img = Image.open(image_path)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")  # Or the format of your choice
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr


tags_metadata = [
    {
        "name": "OCR",
        "description": "Fonctionnalités pour extraire le texte à partir de Tesseract ou Azure.",
    },
    {
        "name": "Annotation",
        "description": "Fonctionnalités pour labelliser un dataset custom avec LabelStudio.",
    },
    {
        "name": "Extraction",
        "description": "Extraction d'entités à partir de fiches de poste/CVs.",
    },
    {
        "name": "Training",
        "description": "Fonctionnalités pour entrainer un modèle custom avec Spacy.",
    },
]

app = FastAPI(openapi_tags=tags_metadata)


def set_key():
    os.environ["VISION_KEY"] = "31448cea13684055978a88efcb82112c"
    os.environ["VISION_ENDPOINT"] = "https://iacquisition.cognitiveservices.azure.com/"


set_key()


@app.get("/get-image/")
def get_image():
    image_bytes = get_image_bytes("/mnt/data/greg/iacquisition/projet/VITALE_PABLO.jpg")
    return Response(content=image_bytes, media_type="image/JPEG")


@app.post("/TesseractOCR/", tags=["OCR"])
def tesseract_ocr(file: UploadFile = File(...)):
    bytes = file.file.read()
    return get_ocr_tesseract(bytes, output="dict")


@app.post("/AzureOCR/", tags=["OCR"])
def azure_ocr(file: UploadFile = File(...)):
    bytes = file.file.read()
    subscription_key = os.environ["VISION_KEY"]
    endpoint = os.environ["VISION_ENDPOINT"]

    return get_ocr_azure_with_regions(
        endpoint=endpoint, key=subscription_key, byte=bytes
    )


@app.post("/PreprocessCV/", tags=["OCR"])
async def preprocess_cv(file: UploadFile = File(...), save: bool = False):
    bytes = file.file.read()
    document_cv = CVDocument()
    document_cv.id = file.filename.split(".")[0]

    liste_page_content = convert_from_bytes(bytes)
    for i in range(len(liste_page_content)):
        img_ = np.asarray(liste_page_content[i])
        document_cv.images["Page " + str(i + 1)] = img_

    document_cv.PreOCRProcessing()
    if save:
        document_cv.plot_region(save=True, plot=False)

    return document_cv.region_bounding_box


@app.post("/TesseractOCRCV/", tags=["OCR"])
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


@app.post("/CVExtractionLLM/", tags=["Extraction"])
async def cv_extraction_llm(file: UploadFile = File(...), ocr: OCR = OCR.tesseract):
    res = {}
    async with httpx.AsyncClient() as client:
        files = {"file": (file.filename, file.file, file.content_type)}
        response = await client.post(
            "http://127.0.0.1:8000/TesseractOCRCV/", files=files
        )
    # Si la réponse est valide
    if response.status_code == 200:
        ## Création du dossier qui contient les sorties d'extractions.
        main_path = os.getcwd()
        output_path = os.path.join(main_path, "data/Extraction/CV")
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        else:
            pass

        for page, textes in response.json().items():
            res[page] = {}
            for id_block, text_block in enumerate(textes):
                extraction_ = ner_task(text=text_block)
                res[page][id_block + 1] = json.loads(extraction_)

        with open(
            os.path.join(output_path, file.filename.split(".")[0] + ".json"), "w"
        ) as outfile:
            json.dump(res, outfile, indent=4)
        return res
    # Erreur dans l'appel du endpoint TesseractOCRCV
    else:
        return {"Erreur": "Erreur dans l'appel du endpoint TesseractOCRCV"}


@app.post("/JobDescExtraction/", tags=["Extraction"])
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
