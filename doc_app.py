import os
import time
import re

import streamlit as st
from dotenv import load_dotenv
from documents_llm import criteria_explanation
from documents_llm.st_helpers import run_query


# Load environment variables
#USERS: Change the path to the .env file to the path where you have saved the .env file
load_dotenv(dotenv_path='/Users/i749910/ollama-summarizer/.env')

#  model parameters
OPENAI_API_KEY = "ollama"
OPENAI_URL = "http://localhost:11434/v1"

st.title("Factory location selection assistant 🏭")
st.write(
    "This is a factory location selection assistant that uses LLM models to summarize and answer questions about documents. "
    "You can upload a PDF and the model will summarize the document and answer questions about it."
)

with st.sidebar:
    st.header("Model")

    model_name = st.selectbox("Model name", options=["deepseek-r1:7b", "mistral"], index=0)

    st.header("Temperature", help="Temperature controls the randomness of the model's output. Lower values make the output more deterministic.")
    temperature = st.slider("Temperature",value=0.1, min_value=0.0, max_value=1.0)
    

    st.header("Document")
    st.subheader("Upload a PDF file")
    files = st.file_uploader("Upload a PDF file", type=["pdf"], accept_multiple_files=True)
    if files:
        for file in files:
            st.write(f"File {file.name} uploaded successfully!")

    st.subheader("Page range")

    st.write(
        "Select page range. Pages are numbered starting at 0. For end page, you can also use negative numbers to count from the end, e.g., -1 is the last page, -2 is the second to last page, etc."
    )
    col1, col2 = st.columns(2)
    with col1:
        start_page = st.number_input("Start page:", value=0, min_value=0)
    with col2:
        end_page = st.number_input("End page:", value=-1)


    st.subheader("Query type")

    query_type = st.radio("Select the query type", ["Summarize", "Query"])

    st.subheader("Factory Location Criteria")
    # criteria = {
    #     "Economic Feasibility": st.checkbox("Economic Feasibility"),
    #     "Infrastructure and Accessibility": st.checkbox("Infrastructure and Accessibility"),
    #     "Environmental Sustainability": st.checkbox("Environmental Sustainability"),
    #     "Labor Market and Workforce": st.checkbox("Labor Market and Workforce"),
    #     "Proximity and Logistics": st.checkbox("Proximity and Logistics"),
    #     "Legal and Political": st.checkbox("Legal and Political"),
    #     "Growth and Scalability": st.checkbox("Growth and Scalability"),
    #     "Innovation and Technological Ecosystem": st.checkbox("Innovation and Technological Ecosystem"),
    # }

    edited_criteria = {}
    for criterion, explanation in criteria_explanation.criteria_explanation.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.checkbox(criterion, key=f"checkbox_{criterion}")
        with col2:
            if st.button("Edit", key=f"button_{criterion}"):
                st.session_state[f"edit_{criterion}"] = not st.session_state.get(f"edit_{criterion}", False)
        if st.session_state.get(f"edit_{criterion}", False):
            edited_criteria[criterion] = st.text_area(f"Edit {criterion}", value=explanation, key=f"text_{criterion}")

    if st.button("Save"):
        for criterion, new_text in edited_criteria.items():
            criteria_explanation.criteria_explanation[criterion] = new_text
        st.success("Criteria explanations updated successfully!")

    st.subheader("Custom Criteria")
    custom_criteria = st.text_input("Add custom criteria. Phrase it as a request for an assistant.")

    show_prompt = st.checkbox("Show prompt")
    show_thinking = st.checkbox("Show thinking of deepseek model")


selected_criteria = [
    explanation for criterion, explanation in criteria_explanation.criteria_explanation.items() if st.session_state.get(f"checkbox_{criterion}", False)
]
criteria_explanations_text = "\n".join(selected_criteria) if selected_criteria else "" 
if custom_criteria:
    criteria_explanations_text += "\n" + custom_criteria

if query_type == "Query":
    user_query = st.text_area(
        "User query", value="What is the data used in this analysis?"
    )


if st.button("Run"):
    results = None
    start = time.time()
    if not files:
        st.error("Please upload a file.")
    else:
        with st.status("Running...", expanded=True) as status:
            try:
                prompt, results = run_query(
                    uploaded_files=files,
                    summarize=query_type == "Summarize",
                    user_query=user_query if query_type == "Query" else "",
                    start_page=start_page,
                    end_page=end_page,
                    model_name=model_name,
                    openai_api_key=OPENAI_API_KEY,
                    openai_url=OPENAI_URL,
                    temperature=temperature,
                    criteria_explanations_text=criteria_explanations_text,
                )
                status.update(label="Done!", state="complete", expanded=False)

            except Exception as e:
                status.update(label="Error", state="error", expanded=False)
                st.error(f"An error occurred: {e}")
                result = ""
        if show_prompt and query_type == "Summarize":
            st.header("Prompt")
            # Format the prompt to replace placeholders with actual values
            formatted_prompt = str(prompt).replace("{criteria_explanations_text}", criteria_explanations_text)
            # Remove 'input_variables' and 'template=' parts
            formatted_prompt = re.sub(r"template=", "", formatted_prompt)
            formatted_prompt = re.sub(r'Document:.*?Summary:', "", formatted_prompt)
            formatted_prompt = formatted_prompt.replace("input_variables=['criteria_explanations_text', 'document'] ", "")
            formatted_prompt = formatted_prompt.replace('\\n', ' ') 
            formatted_prompt = formatted_prompt.strip()
            st.write(formatted_prompt)
            #st.write(prompt)
        if show_prompt and query_type == "Query":
            st.header("Prompt: ")
            st.write("Based on this list of documents, please identify the information that is most relevant to the following query: ", user_query, "Criteria explanations: ", criteria_explanations_text, "If the document is not relevant, please write not relevant", " Reduce prompt: The following is set of partial answers to a user query. Take these and distill it into a final, consolidated answer to the query.")
        if results:
            st.header("Result")
            for result in results:
                if model_name == "deepseek-r1:7b" and not show_thinking:
                    result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
                st.markdown(result)
            st.info(f"Time taken: {time.time() - start:.2f} seconds", icon="⏱️")
