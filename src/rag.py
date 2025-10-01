from langchain_community.vectorstores import Chroma
from langchain.embeddings import BedrockEmbeddings
from langchain.chains import RetrievalQA
from langchain.llms.bedrock import Bedrock
from src.configure import CHROMA_DIR

def carregar_rag():
    embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1")

    vectordb = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )

    retriever = vectordb.as_retriever(search_kwargs={"k": 3})

    llm = Bedrock(model_id="anthropic.claude-v2")

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True
    )

    return qa_chain

if __name__ == "__main__":
    qa = carregar_rag()
    pergunta = "Quais são os direitos trabalhistas previstos no documento?"
    resposta = qa({"query": pergunta})

    print("Pergunta:", pergunta)
    print("Resposta:", resposta["result"])
    print("Fontes:", [doc.metadata.get("source") for doc in resposta["source_documents"]])
