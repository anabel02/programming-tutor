from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import Chroma
import time

PDF_PATH = "Cap 07 Arrays.pdf"

loader = PyPDFLoader(PDF_PATH)  # Load your PDF file
data = loader.load()
# print(data)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=100)
docs = text_splitter.split_documents(data)

print("Total number of Chunks: ", len(docs))  # Check how many chunks we have
# for chunk in docs:
#     print(chunk.page_content)

api_key = "AIzaSyCoxFsjIYKIz0jxIwlHYR5tI1by7LRvqw4"

os.environ["GEMINI_API_KEY"] = api_key

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set. Please set it as an environment variable.")

# Load the Gemini API key
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)

# Test embedding a query
vector = embeddings.embed_query("hello, world!")
print(len(vector))
print(vector[0])

PERSISTENT_DIRECTORY = "chroma"

# small_docs = docs[:75]  # Use a smaller subset of documents
start_time = time.time()

try:
    vectorstoredb = Chroma.from_documents(
        documents=docs, embedding=embeddings, persist_directory=PERSISTENT_DIRECTORY
    )
except Exception as e:
    print(f"Error: {e}")
else:
    print("Chroma processing completed successfully.")

elapsed_time = time.time() - start_time
print(f"Time taken with smaller dataset: {elapsed_time:.2f} seconds")


retriever = vectorstoredb.as_retriever(search_type="similarity", search_kwargs={"k": 5})

retrieved_docs = retriever.invoke("Como extraer los objetivos especificos")
print(len(retrieved_docs))
print(retrieved_docs[0].page_content)  # Print the first retrieved document
