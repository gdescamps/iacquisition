import streamlit as st
import PyPDF2
from io import BytesIO
import base64
import requests
import os
from st_pages import Page, Section, show_pages

st.set_page_config(layout="wide")
st.title("Page d'accueil")
show_pages(
    [
        Page("home.py", "Accueil", "🏠"),
        Page("pages/page1.py", "Extraction CV"),
        Page("pages/page2.py", "Extraction Fiche de poste"),
        Page("pages/page3.py", "Matching Fiche de poste CV"),
        Page("pages/page4.py", "Chatbot Fiche de poste"),
        Page("pages/page5.py", "Chatbot Fiche de poste CV"),
        Page("pages/page6.py", "Assistant Entretien"),
        Page("pages/page7.py", "Tests"),
    ]
)
