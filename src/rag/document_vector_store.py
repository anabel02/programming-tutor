import os
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.schema import Document
from dotenv import load_dotenv
from pdf_loader import PDFCorpusLoader

# Load environment variables
load_dotenv()


class ChromaVectorDatabase:
    def __init__(self, persist_directory: str, embedding_model="models/text-embedding-004"):
        """
        Initializes the Chroma vector database with GoogleGenerativeAIEmbeddings.

        Args:
            persist_directory (str): Path to the directory where the database will persist.
            embedding_model (str): The embedding model to use. Default is "models/embedding-001".
        """
        self.persist_directory = persist_directory
        self.embeddings = self._initialize_embeddings(embedding_model)
        self.vector_db = None
        self._initialize_vector_store()

    def _initialize_embeddings(self, model: str):
        """
        Initializes the Google Generative AI embeddings.

        Args:
            model (str): The embedding model to use.

        Returns:
            GoogleGenerativeAIEmbeddings: Initialized embeddings.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set. Please set it as an environment variable.")
        return GoogleGenerativeAIEmbeddings(model=model, google_api_key=api_key)

    def _initialize_vector_store(self):
        """Initializes the Chroma vector store."""
        if not os.path.exists(self.persist_directory):
            os.makedirs(self.persist_directory)

        self.vector_db = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )

    def add_documents(self, documents: list[Document], batch_size: int = 30):
        """
        Adds documents to the vector store in batches to prevent crashes.

        Args:
            documents (list[Document]): A list of LangChain Document objects to add.
            batch_size (int): The size of each batch of documents to insert. Default is 50.
        """
        if not documents:
            raise ValueError("No documents provided for insertion.")

        # Split the documents into smaller batches
        batches = [documents[i:i + batch_size] for i in range(0, len(documents), batch_size)]
        print(len(batches))

        for i, batch in enumerate(batches):
            try:
                self.vector_db.add_documents(batch)  # Add a batch of documents to the vector store
                # Optionally persist after each batch
                # self.vector_db.persist()
                print(f"Batch {i + 1} added: {len(batch)} documents.")
            except Exception as e:
                print(f"Failed to add batch: {e}")
                continue  # Continue adding remaining batches

        # Optionally persist after all batches are added
        # self.vector_db.persist()

    def search(self, query: str, top_k: int = 5):
        """
        Searches the vector database.

        Args:
            query (str): The search query.
            top_k (int): Number of top results to retrieve.

        Returns:
            list[Document]: A list of matching documents.
        """
        results = self.vector_db.similarity_search(query, k=top_k)
        return results

    def list_collections(self):
        """
        Lists all collections in the Chroma vector store.

        Returns:
            list[str]: Collection names.
        """
        return self.vector_db.list_collections()

    def delete_collection(self):
        """
        Deletes the entire collection in the vector store.
        """
        self.vector_db.delete_collection()


# Example Usage
if __name__ == "__main__":
    folder_path = os.path.abspath("corpus")  # Convert to absolute path
    pdf_loader = PDFCorpusLoader(folder_path, chunk_size=5000)

    try:
        pdf_corpus = pdf_loader.load_corpus()
        print(f"Loaded {len(pdf_corpus)} PDFs.")

        # Initialize the vector database
        persist_dir = "chroma_db"
        vector_db = ChromaVectorDatabase(persist_directory=persist_dir)

        # Load the PDFs and add them to the vector store
        vector_db.add_documents(pdf_corpus)

        # Search for a query
        search_query = "array bidimensional"
        results = vector_db.search(search_query)

        # Display search results
        print("Search Results:")
        for doc in results:
            print(f"Content: {doc.page_content}\nMetadata: {doc.metadata}\n")

    except ValueError as e:
        print(e)
