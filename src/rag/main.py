import os
from rag.pdf_loader import PDFCorpusLoader
from rag.document_vector_store import ChromaVectorDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from rag.ai_tutor import AITutor
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# Initialize the vector database
persist_dir = "chroma_db"

add_docs = not os.path.exists(persist_dir)

vector_db = ChromaVectorDatabase(persist_directory=persist_dir)

if (add_docs):
    folder_path = os.path.abspath("corpus")  # Convert to absolute path
    pdf_loader = PDFCorpusLoader(folder_path, chunk_size=5000)

    pdf_corpus = pdf_loader.load_corpus()
    print(f"Loaded {len(pdf_corpus)} documents.")

    # Load the PDFs and add them to the vector store
    vector_db.add_documents(pdf_corpus)

retriever = vector_db.vector_db.as_retriever(search_type="similarity", search_kwargs={"k": 5})

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, api_key=api_key)

ai_tutor = AITutor(llm, retriever)

question = "array bidimensional"
answer = ai_tutor.answer_question(question)
print(answer['answer'])
