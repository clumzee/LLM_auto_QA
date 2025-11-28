import streamlit as st
import requests

FASTAPI_URL = "http://localhost:8000/gherkin" 

st.title("Gherkin Test Case Generator (MVP)")

url = st.text_input("Enter a URL")

if st.button("Generate"):
    if not url.strip():
        st.error("Please enter a valid URL.")
    else:
        with st.spinner("Generating..."):
            try:
                res = requests.post(FASTAPI_URL, json={"url": url})
                if res.status_code != 200:
                    st.error(f"FastAPI Error: {res.status_code}")
                else:
                    try:
                        # Expecting {"gherkin": "..."}
                        gherkin_text = res.json().get("results", "")
                    except:
                        # Fallback: plain text
                        gherkin_text = res.text

                    if not gherkin_text:
                        st.error("No Gherkin returned from API.")
                    else:
                        st.success("Generated!")
                        st.json(gherkin_text)
            except Exception as e:
                st.error(f"Error contacting FastAPI: {e}")
