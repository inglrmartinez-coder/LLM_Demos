import streamlit as st
from resume_tool import create_brochure

st.title(f"Brochure tool")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

company_input = st.text_input("Type the Copany Name:", key="company_input")
url_input = st.text_input("Type the URL:", key="url_input")

def get_brochure():
    cp_input = st.session_state["company_input"]
    url = st.session_state["url_input"]
    if company_input and url_input:
        st.write(f"Creating brochure for {cp_input} from {url}")
        response = create_brochure(cp_input,url)
        with st.spinner("Please wait....."):
            st.write(response)
        st.session_state["company_input"] = ""
        st.session_state["url_input"] =""
    else:
        st.write("Please enter both company name and URL.")


st.button("Get Brochure", on_click=get_brochure)
