import os
from langchain.chains import RetrievalQA
from langchain_community.llms import Bedrock
from langchain_community.vectorstores import Chroma
from src.configure import CHROMA_DIR, BEDROCK_LLM_MODEL

def criar_chain(persist_dir: str = CHROMA_DIR):
    if not os.path.exists(persist_dir):
        raise FileNotFoundError(
            f"Chroma não encontrado em {persist_dir}. Rode save.py primeiro."
        )

    
    vectordb = Chroma(persist_directory=persist_dir)
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})

    llm = Bedrock(model_id=BEDROCK_LLM_MODEL)

    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents = True
    )

    return qa_chain
