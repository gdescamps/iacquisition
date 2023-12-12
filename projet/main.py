from fastapi import FastAPI, File, UploadFile, Query
from typing import List, Union, Optional

from api.JobDocument import *

app = FastAPI()


@app.post("/Job Desc Extraction/")
def jobdesc_extraction(
    file: UploadFile = File(...)
    ):
    
    bytes = file.file.read()
    document = JobDescDocument()
    document.id = file.filename
    
    
    liste_page_content = convert_from_bytes(bytes)
    for i in range(len(liste_page_content)):
        img_ = np.asarray(liste_page_content[i])
        PIL_image = Image.fromarray(np.uint8(img_)).convert("RGB")
        output_tesseract = pytesseract.image_to_data(PIL_image, output_type="data.frame")
        document.pages_content['Page ' + str(i+1)] = output_tesseract
    document.nb_pages = len(document.pages_content)
    
    document.postprocess_ocr()
    document.extraction()
    
    document.extraction_formulaire()
        
    return document.entities