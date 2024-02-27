from fastapi import FastAPI, File, UploadFile, Query, Response, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from typing import List, Union, Optional
import io
from PIL import Image
import httpx

from api.JobDocument import *
from api.CVDocument import *
from api.utils import *

from ocr.OCR import *
from ocr.AzureOCR import *
from ocr.TesseractOCR import *
from ocr.preprocessing import *

from recherche.utils import *

from LLM.embedding import *
from LLM.extraction import *

import requests
import PyPDF2


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
    {
        "name": "Requêtes",
        "description": "Fonctionnalités pour requêter la BDD vectorielle.",
    },
]


app = FastAPI(openapi_tags=tags_metadata)

# Allow all origins (*), or specify the correct ones
origins = [
    "*",
    "http://localhost:8501",  # Streamlit default port
    "http://localhost:8000",  # FastAPI default port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def set_key():
    os.environ["VISION_KEY"] = "31448cea13684055978a88efcb82112c"
    os.environ["VISION_ENDPOINT"] = "https://iacquisition.cognitiveservices.azure.com/"


set_key()


@app.post("/ExtractTextWithoutOCR/", tags=["OCR"])
async def extract_text_from_pdf_without_ocr(file: UploadFile):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=415, detail="Unsupported file type. Please upload a PDF."
        )

    contents = await file.read()
    reader = PyPDF2.PdfFileReader(io.BytesIO(contents))
    text = ""

    for page_num in range(reader.numPages):
        page = reader.getPage(page_num)
        text += page.extractText()

    return {"Texte": text}


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
                try:
                    res[page][id_block + 1] = eval(extraction_)
                except SyntaxError as e:
                    msg = str(e)
                    if msg.startswith("unterminated"):
                        print(
                            "Problème lié au fait que le texte est de mauvaise qualité"
                        )
                    elif msg.startswith("closing "):
                        print(msg)
                    elif msg.startswith("invalid syntax."):
                        print(msg)
                    continue

        with open(
            os.path.join(output_path, file.filename.split(".")[0] + ".json"), "w"
        ) as outfile:
            json.dump(res, outfile, indent=4)
        return res
    # Erreur dans l'appel du endpoint TesseractOCRCV
    else:
        return {"Erreur": "Erreur dans l'appel du endpoint TesseractOCRCV"}


@app.post("/JobDescExtractionLLM/", tags=["Extraction"])
def jobdesc_extraction(file: UploadFile = File(...), ocr: OCR = OCR.tesseract):
    bytes = file.file.read()
    resultat_ocr = get_ocr_tesseract(byte=bytes, output="data.frame")
    document = JobDescDocument()
    document.nb_pages = len(resultat_ocr)
    document.id = file.filename
    document.pages_content = resultat_ocr
    document.postprocess_ocr()

    full_text = ""

    for page, page_content in document.pages_content.items():
        page_text = " ".join(list(document.pages_content[page]["text"].values))
        if full_text:
            full_text = full_text + " " + page_text
        else:
            full_text = page_text
    final_res = ner_task_jobdesc(full_text)
    return final_res


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

    # res = json.dumps(document.entities)
    # return res
    return document.entities


@app.post("/Requete_BDD/", tags=["Requêtes"])
def requete_simple(
    queries: List[str],
    collection_name: Collection = Collection.Responsibilities,
    n_results: int = 20,
    top_n: int = 3,
):
    final_df = query_collection(
        queries, collection_name=collection_name.value, n_results=top_n
    )
    if type(final_df) == pd.DataFrame:
        final_dict = process_dataframe_get_top(final_df, top_n)
        explicability_dict = explicability(final_df, final_dict)
        combined_json = {
            "final_dict": final_dict,
            "explicability_dict": explicability_dict,
        }
        return combined_json
    else:
        return None
