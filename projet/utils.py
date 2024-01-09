from PIL import Image
import io
import os
import openai
import fitz
import PyPDF2
import re


def split_pdf(pdf_path, split_indexes, names):
    # Create the output folder
    main_path = os.getcwd()
    output_path = os.path.join(main_path, "data/CV")
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        pass

    # Get the Jobreq id
    jobreq = re.search("JOBREQ[0-9]+", pdf_path)
    if jobreq:
        jobreq = jobreq.group(0)
    else:
        jobreq = "JOBREQ"

    # Open the original PDF
    with open(pdf_path, "rb") as infile:
        reader = PyPDF2.PdfFileReader(infile)
        # total_pages = reader.numPages

        # Starting index for the first chunk
        start_index = 0

        # Iterate through split indexes
        for i, index in enumerate(split_indexes):
            writer = PyPDF2.PdfFileWriter()

            # Add pages to the new PDF
            for page in range(start_index, index):
                writer.addPage(reader.getPage(page))

            # Save the new PDF
            if i == 0:
                pass
            else:
                with open(
                    os.path.join(output_path, "{}_{}.pdf".format(jobreq, names[i - 1])),
                    "wb",
                ) as outfile:
                    writer.write(outfile)

            # Update the start index for the next chunk
            start_index = index


def extract_button_actions(pdf_path):
    # Open the PDF
    doc = fitz.open(pdf_path)
    # print(doc.metadata)
    resultats = []
    for _ in doc.get_toc():
        resultats.append([_[1], _[2]])
    doc.close()
    return [i[0] for i in resultats], [i[1] - 1 for i in resultats]
