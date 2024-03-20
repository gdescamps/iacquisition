header_style = """
<style>
.header {
    color: white;
    padding: 10px;
    font-size: 25px;
    text-align: center;
    background-color: black;
    border-radius: 5px;
    margin: 10px 0;
}
.header2 {
    color: white;
    padding: 10px;
    font-size: 25px;
    text-align: center;
    background-color: grey;
    border-radius: 5px;
    margin: 10px 0;
}
.headertopscore {
    color: black;
    padding: 10px;
    font-size: 25px;
    text-align: center;
    background-color: white;
    border-radius: 5px;
    margin: auto; /* Set margin to auto to center the button */
    width: 25%; /* Set a specific width to make the button smaller */
    display: block; /* This will allow margin: auto to work properly */
}
.headermidscore {
    color: black;
    padding: 10px;
    font-size: 25px;
    text-align: center;
    background-color: white;
    border-radius: 5px;
    margin: auto; /* Set margin to auto to center the button */
    width: 25%; /* Set a specific width to make the button smaller */
    display: block; /* This will allow margin: auto to work properly */
}
.headerbotscore {
    color: black;
    padding: 10px;
    font-size: 25px;
    text-align: center;
    background-color: white;
    border-radius: 5px;
    margin: auto; /* Set margin to auto to center the button */
    width: 25%; /* Set a specific width to make the button smaller */
    display: block; /* This will allow margin: auto to work properly */
}
div.stBox {
    border: 1px solid black;
    border-radius: 5px;
    padding: 10px;
    margin: 10px 0;
}
</style>
"""

business_case_style = """
<style>
    .contexte-box {
        border: 1px solid #cccccc;
        padding: 10px;
        margin-bottom: 5px;
        background-color: #f8f9fa;
    }
    .businesscase-box {
        border-left: 3px solid black;
        border-top: 1px solid #cccccc;
        border-right: 1px solid #cccccc;
        border-bottom: 1px solid #cccccc;
        padding: 10px;
        margin-bottom: 10px;
        background-color: white;
    }
    .header-box {
        background-color: black;
        color: white;
        padding: 10px;
        margin-bottom: 5px;
        font-weight: bold;
    }
"""

question_section_style = """
<style>
    .question-box {
        border: 1px solid #cccccc;
        padding: 10px;
        margin-bottom: 5px;
        background-color: #f8f9fa;
    }
    .answer-box {
        border-left: 3px solid black;
        border-top: 1px solid #cccccc;
        border-right: 1px solid #cccccc;
        border-bottom: 1px solid #cccccc;
        padding: 10px;
        margin-bottom: 10px;
        background-color: white;
    }
    .header-box {
        background-color: black;
        color: white;
        padding: 10px;
        margin-bottom: 5px;
        font-weight: bold;
    }
</style>
"""

sidebar_style = """
<style>
/* Targeting the sidebar with data-testid attribute */
[data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
    background-color: black;
}
/* Changing the color of all text inside the sidebar */
[data-testid="stSidebar"][aria-expanded="true"] > div:first-child * {
    color: white;
}
/* Customizing buttons to appear with white background and black text */
[data-testid="stSidebar"] .stButton > button {
    background-color: white !important;
    color: black !important;
    border: 1px solid #eee !important;
    border-radius: 4px !important;
    padding: 8px 16px !important;
    margin: 5px 0 !important;
    width: 100%;
    display: block;
}
/* Hover effect for buttons */
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #f2f2f2 !important;
    color: black !important;
}
</style>
"""

# Custom CSS to inject
image_style = """
<style>
.image-container {
    padding: 10px;
    border-radius: 5px;
    box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    transition: 0.3s;
    margin-bottom: 15px;
}

.image-container:hover {
    box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
}

img {
    border-radius: 5px;
}
</style>
"""

sidebar_title = """
<style>
.st-emotion-cache-1l23ect p {
    display: block;
    margin-left: auto;
    margin-right: auto;
    font-size: 26px;
    text-align: center;
}
</style>
"""
