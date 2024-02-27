import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge

st.set_page_config(layout="wide")

# Define the styles for the headers and boxes
header_style = """
<style>
div.stButton > button:first-child {
    display: none;
}
.header {
    color: white;
    padding: 10px;
    font-size: 25px;
    text-align: center;
    background-color: black;
    border-radius: 5px;
    margin: 10px 0;
}
div.stBox {
    border: 1px solid #9C27B0;
    border-radius: 5px;
    padding: 10px;
    margin: 10px 0;
}
</style>
"""
st.markdown(
    """
    <style>
    /* Targeting the sidebar with data-testid attribute */
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
        background-color: white;
    }
    /* Changing the color of all text inside the sidebar */
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child * {
        color: black;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Your Streamlit app code below
st.sidebar.image(
    "/home/pablo/data/iacquisition/projet/streamlit_app/logo.jpg", use_column_width=True
)
st.sidebar.title("Sidebar Title")
st.sidebar.markdown("This is the sidebar.")

present_competencies = ["Python", "Data Analysis", "Machine Learning"]  # Example list
absent_competencies = ["Deep Learning", "SQL"]  # Example list with less than 3 items


# Function to convert a list of strings to HTML list items
def create_html_list(items):
    return "".join(f"<li>{item}</li>" for item in items)


# Write styles to the app
st.markdown(header_style, unsafe_allow_html=True)

st.markdown('<div class="header">Assistant Entretien</div>', unsafe_allow_html=True)
# Create columns for the different sections
col1, col2 = st.columns(2)

# Fill in the first column with a custom styled header and boxes
with col1:
    st.markdown('<div class="header">Compétences clés</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="stBox">
            <p><b>Compétences présentes</b></p>
            <ul>
                {create_html_list(present_competencies)}
            </ul>
        </div>
        <div class="stBox">
            <p><b>Compétences absentes</b></p>
            <ul>
                {create_html_list(absent_competencies)}
            </ul>
        </div>
    """,
        unsafe_allow_html=True,
    )

# Fill in the second column with a custom styled header and box
with col2:
    st.markdown('<div class="header">Niveau de séniorité</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="stBox">
            <p><b>Poste actuel:</b> Lead Data Scientist</p>
            <p><b>Années d'expérience:</b> 6</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

from st_circular_progress import CircularProgress

my_circular_progress = CircularProgress(
    label="Sample Bar", value=55, key="my_circular_progress"
).st_circular_progress()
