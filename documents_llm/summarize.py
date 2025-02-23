from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain_core.documents.base import Document
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


def summarize_document(
    docs: list[Document],
    model_name: str,
    openai_api_key: str,
    base_url: str,
    temperature: float = 0.1,
    criteria_explanations_text: str = "",
) -> tuple[str, str]:
    pass

    # Define LLM chain
    llm = ChatOpenAI(
        temperature=temperature,
        model_name=model_name,
        api_key=openai_api_key,
        base_url=base_url,
        model=model_name,
    )

    prompt_template = """Write a long summary of the following document. 
    Only include information that is part of the document. 
    Do not include your own opinion or analysis.

    Criteria explanations:
    "{criteria_explanations_text}"

    Document:
    "{document}"
    Summary:"""
    prompt = PromptTemplate.from_template(prompt_template)

    llm_chain = LLMChain(llm=llm, prompt=prompt)

    stuff_chain = StuffDocumentsChain(
        llm_chain=llm_chain, document_variable_name="document"
    )
    result = stuff_chain.invoke({"input_documents": docs, "criteria_explanations_text": criteria_explanations_text})
    return prompt, result["output_text"]
