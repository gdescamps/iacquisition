import pandas as pd
import numpy as np
import json
from PIL import Image
import os
import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
import re
from api.utils import *


class JobDescDocument:
    def __init__(self):
        self.id = None
        self.nb_pages = None
        self.pages_content = {}
        self.lines = []
        self.entities = {}

    def get_text_block(self, dataframe, block_number: int):
        """Pour une page, un bloc; récupère le texte du bloc. (Tesseract)

        Args:
            dataframe (pd.DataFrame): La sortie de la page (Tesseract)
            block_number (int): L'identifiant du bloc.

        Returns:
            str: Le texte du bloc.
        """
        try:
            res = dataframe[dataframe["block_num"] == block_number]["text"].str.cat(
                sep=" "
            )
        except:
            print("Erreur get_text_block")
            return ""
        else:
            return res

    def get_text_line(self, page, line_num, block_num):
        """Pour une page, un bloc, et un identifiant de ligne; récupère le texte de la ligne. (Tesseract)

        Args:
            page (str): Le numéro de la page (Ex: 'Page 2')
            line_num (int): L'identifiant de la ligne.
            block_num (int): L'identifiant du bloc.

        Returns:
            str: Le texte de la ligne.
        """
        try:
            res = self.pages_content[page][
                (self.pages_content[page]["block_num"] == block_num)
                & (self.pages_content[page]["line_num"] == line_num)
            ]["text"].str.cat(sep=" ")
        except:
            print("Erreur get_text_line")
            return ""
        else:
            return res

    def get_all_lines(self):
        """Récupère l'ensemble des lignes du document à partir de la sortie OCR (Tesseract)"""
        for page, page_content in self.pages_content.items():
            for block_num_ in page_content["block_num"].unique():
                for line_num in page_content[page_content["block_num"] == block_num_][
                    "line_num"
                ].unique():
                    __ = self.get_text_line(
                        page=page, line_num=line_num, block_num=block_num_
                    )
                    if __:
                        self.lines.append(__.lower())

    def postprocess_ocr(self):
        """Formatte les sorties OCR (Tesseract).

        Returns:
            NoneType
        """
        for page, page_content in self.pages_content.items():
            page_content["text"] = page_content["text"].astype(str)
            page_content = page_content[page_content["text"] != "nan"]

            for block_num in page_content["block_num"].unique():
                if (
                    self.get_text_block(dataframe=page_content, block_number=block_num)
                    == " "
                ):
                    page_content = page_content[page_content["block_num"] != block_num]
            self.pages_content[page] = page_content
        return None

    def check_keywords_in_page_azure(self, page, keyword):
        res = []
        for idx_line, line_ in enumerate(self.pages_content[page]):
            if keyword.lower() in line_.lower():
                res.append((int(idx_line + 1), line_))
        return res

    def check_keywords_in_page(self, dataframe, keyword: str):
        """Récupère les occurences d'un mot clé donné au niveau de la page.

        Args:
            dataframe (_type_): La page de sortie OCR (Tesseract)
            keyword (str): Le mot clé

        Returns:
            List: Les occurences trouvées.
        """
        res = []
        for block_num in dataframe["block_num"].unique():
            __ = self.get_text_block(dataframe, block_number=block_num)
            if keyword.lower() in __.lower():
                res.append((int(block_num), __))
        return res

    def check_keywords_in_doc_azure(self, keyword: str):
        """_summary_

        Args:
            keyword (str): _description_

        Returns:
            _type_: _description_
        """
        resultats = {}
        for page, page_content in self.pages_content.items():
            resultats[page] = self.check_keywords_in_page_azure(
                page=page, keyword=keyword
            )
        return resultats

    def check_keywords_in_doc(self, keyword: str):
        """_summary_

        Args:
            keyword (str): _description_

        Returns:
            _type_: _description_
        """
        resultats = {}
        for page, page_content in self.pages_content.items():
            resultats[page] = self.check_keywords_in_page(
                dataframe=page_content, keyword=keyword
            )
        return resultats

    def extraction_formulaire(self):
        """Récupère les informations du petit formulaire à la fin d'une fiche de poste et
            insère les résultats dans self.entities

        Returns:
            NoneType
        """
        _JOBREQ_REGEX_ = "JOBREQ[0-9]+"
        _DATE_REGEX_ = "[0-9]{2}/[0-9]{2}/[0-9]{4}"

        for page, content in self.pages_content.items():
            for block_num_ in content["block_num"].unique():
                texte = self.get_text_block(dataframe=content, block_number=block_num_)
                jobreq = re.findall(_JOBREQ_REGEX_, texte)
                if jobreq:
                    self.entities["Code de la demande de poste"] = jobreq[0]
                    date_publication = re.findall(_DATE_REGEX_, texte)
                    if date_publication:
                        self.entities["Date de publication"] = date_publication[0]
        return None

    def extraction_azure(self):
        """Récupère les informations relatives à la fiche de poste.
        Insère les résultats dans self.entities.

        Returns:
             NoneType
        """
        #### Extraction Pattern Mission
        mission_pattern = self.check_keywords_in_doc_azure(keyword="mission")
        if mission_pattern != {"Page " + str(i + 1): [] for i in range(self.nb_pages)}:
            for k, v in mission_pattern.items():
                if v:
                    idx_mission = (int(k.split()[1]), v[0][0])
                    print("Identifiants Missions")
                    print(idx_mission)
                    break
        #### Extraction Pattern Profil
        profil_pattern = self.check_keywords_in_doc_azure(keyword="profil")
        if profil_pattern != {"Page " + str(i + 1): [] for i in range(self.nb_pages)}:
            for k, v in profil_pattern.items():
                if v:
                    idx_profil = (int(k.split()[1]), v[0][0])
                    print("Identifiants Profils")
                    print(idx_profil)
                    break

        #### Extractions champs
        bp_pattern = self.check_keywords_in_doc_azure(keyword="·")
        new_bp_pattern = []
        for page, matchs in bp_pattern.items():
            for block_match in matchs:
                __ = re.split("·", block_match[1])
                for ___ in __:
                    if ___:
                        new_bp_pattern.append(
                            ((int(page.split()[1]), block_match[0]), ___.strip())
                        )

        if idx_mission and idx_profil:
            first_tuple, first_pattern, last_tuple, last_pattern = minimal_tuple(
                idx_mission, idx_profil
            )
            for __ in new_bp_pattern:
                if __[0] == first_tuple:
                    try:
                        self.entities[first_pattern].append(__[1])
                    except:
                        self.entities[first_pattern] = [__[1]]
                elif tuple_before(__[0], first_tuple):
                    try:
                        self.entities["Caractéristiques"].append(__[1])
                    except:
                        self.entities["Caractéristiques"] = [__[1]]
                else:
                    if __[0] == last_tuple:
                        try:
                            self.entities[last_pattern].append(__[1])
                        except:
                            self.entities[last_pattern] = [__[1]]
                    elif tuple_before(__[0], last_tuple):
                        try:
                            self.entities[first_pattern].append(__[1])
                        except:
                            self.entities[first_pattern] = [__[1]]
                    else:
                        try:
                            self.entities[last_pattern].append(__[1])
                        except:
                            self.entities[last_pattern] = [__[1]]
        return None

    def extraction(self):
        """Récupère les informations relatives à la fiche de poste.
           Insère les résultats dans self.entities.

        Returns:
            NoneType
        """
        #### Extraction Pattern Mission
        mission_pattern = self.check_keywords_in_doc(keyword="mission")
        if mission_pattern != {"Page " + str(i + 1): [] for i in range(self.nb_pages)}:
            for k, v in mission_pattern.items():
                if v:
                    idx_mission = (int(k.split()[1]), v[0][0])
                    break
        #### Extraction Pattern Profil
        profil_pattern = self.check_keywords_in_doc(keyword="profil")
        if profil_pattern != {"Page " + str(i + 1): [] for i in range(self.nb_pages)}:
            for k, v in profil_pattern.items():
                if v:
                    idx_profil = (int(k.split()[1]), v[0][0])
                    break

        #### Extractions champs
        bp_pattern1 = self.check_keywords_in_doc(keyword="*")
        bp_pattern2 = self.check_keywords_in_doc(keyword="+")
        bp_pattern = {}

        for page in bp_pattern1.keys():
            bp_pattern[page] = list(set(bp_pattern1[page] + bp_pattern2[page]))

        new_bp_pattern = []
        for page, matchs in bp_pattern.items():
            for block_match in matchs:
                __ = re.split("- | -|\*|(?<! [bB][aA][cC]) \+", block_match[1])
                for ___ in __:
                    if ___:
                        new_bp_pattern.append(
                            ((int(page.split()[1]), block_match[0]), ___.strip())
                        )

        if idx_mission and idx_profil:
            first_tuple, first_pattern, last_tuple, last_pattern = minimal_tuple(
                idx_mission, idx_profil
            )
            for __ in new_bp_pattern:
                if __[0] == first_tuple:
                    try:
                        self.entities[first_pattern].append(__[1])
                    except:
                        self.entities[first_pattern] = [__[1]]
                elif tuple_before(__[0], first_tuple):
                    try:
                        self.entities["Caractéristiques"].append(__[1])
                    except:
                        self.entities["Caractéristiques"] = [__[1]]
                else:
                    if __[0] == last_tuple:
                        try:
                            self.entities[last_pattern].append(__[1])
                        except:
                            self.entities[last_pattern] = [__[1]]
                    elif tuple_before(__[0], last_tuple):
                        try:
                            self.entities[first_pattern].append(__[1])
                        except:
                            self.entities[first_pattern] = [__[1]]
                    else:
                        try:
                            self.entities[last_pattern].append(__[1])
                        except:
                            self.entities[last_pattern] = [__[1]]

        return None
