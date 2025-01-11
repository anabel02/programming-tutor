from abc import ABC, abstractmethod
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os


class CorpusLoader(ABC):
    """
    Abstract base class for a corpus loader.
    """
    def __init__(self, folder_path):
        """
        Initialize with the path to the folder containing the corpus files.

        :param folder_path: Path to the folder with corpus files.
        """
        self.folder_path = folder_path

    @abstractmethod
    def load_corpus(self):
        """
        Abstract method to load and process the corpus.
        :return: Dictionary with filenames as keys and content as values.
        """
        pass


class PDFCorpusLoader:
    def __init__(self, folder_path: str, chunk_size: int = 2000, chunk_overlap: int = 200):
        self.folder_path = folder_path
        # Initialize the text splitter with provided chunk size and overlap
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def load_corpus(self):
        """
        Loads the corpus of PDFs from the specified folder, splits the text into chunks,
        and returns them with metadata.

        Returns:
            dict: A dictionary with filenames as keys and corresponding document chunks as values.
        """
        if not os.path.exists(self.folder_path):
            raise ValueError(f"Invalid folder path: {self.folder_path}")

        pdf_corpus = []
        for filename in os.listdir(self.folder_path):
            if filename.endswith(".pdf"):
                file_path = os.path.join(self.folder_path, filename)
                try:
                    # Load the PDF file using PyPDFLoader
                    loader = PyPDFLoader(file_path)
                    documents = loader.load()

                    chunked_documents = self.split_text(documents)

                    # Store the chunked documents with metadata
                    pdf_corpus.extend(chunked_documents)
                except Exception as e:
                    print(f"Failed to process {filename}: {e}")
        return pdf_corpus

    def split_text(self, data):
        """
        Splits the text data into smaller chunks using the RecursiveCharacterTextSplitter.

        Args:
            data (str): The text to split.

        Returns:
            list[Document]: A list of LangChain Document objects for each chunk.
        """
        # Split the document into chunks
        docs = self.text_splitter.split_documents(data)

        return docs
