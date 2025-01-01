import streamlit as st
from langchain.chains import RetrievalQA
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Load pre-trained vector store
@st.cache_resource
def load_vectorstore():
    embedding_model = OpenAIEmbeddings()
    return FAISS.load_local("yatsu_knowledge_base", embedding_model)

# Initialize RetrievalQA
def initialize_yatsu():
    vectorstore = load_vectorstore()
    qa_chain = RetrievalQA.from_chain_type(
        llm="gpt-4",
        retriever=vectorstore.as_retriever()
    )
    return qa_chain

def main():
    st.set_page_config(
        page_title="Yatsu AI",
        page_icon="💬",
        layout="wide"
    )
    st.title("💬 **Yatsu Immigration Specialist**")
    st.markdown("### Gain Insights on Immigration Procedures")
    
    with st.sidebar:
        st.image("https://www.ustayinusa.com/logo.svg")
        st.markdown("### **Immigration Specialist**")
        st.write("Explore AI-Powered Immigration Specialist.")

    # Load Yatsu's Q&A chain
    with st.spinner("Loading Yatsu..."):
        yatsu = initialize_yatsu()

    # Chat interface
    st.markdown("## **Chat with Yatsu**")
    user_query = st.text_input("What would you like to know about immigration?", "")
    
    if user_query:
        with st.spinner("Yatsu is thinking..."):
            response = yatsu.run(user_query)
        st.markdown("### **Yatsu's Answer**")
        st.write(response)

if __name__ == "__main__":
    main()
