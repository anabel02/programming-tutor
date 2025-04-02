import logging
from abc import ABC, abstractmethod
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader


class CorpusLoader(ABC):
    """
    Abstract base class for a corpus loader.
    """
    def __init__(self, folder_path: str):
        """
        Initialize with the path to the folder containing the corpus files.

        :param folder_path: Path to the folder with corpus files.
        """
        folder = Path(folder_path)
        print(folder)
        if not folder.exists() or not folder.is_dir():
            raise ValueError(f"Invalid folder path: {folder_path}")

        self.folder_path = folder

    @abstractmethod
    def load_corpus(self):
        """
        Abstract method to load and process the corpus.
        """
        pass


class PDFCorpusLoader(CorpusLoader):
    def __init__(self, folder_path: str, chunk_size: int = 2000, chunk_overlap: int = 200):
        super().__init__(folder_path)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def load_corpus(self):
        """
        Loads PDFs from the specified folder, splits their text into chunks,
        and returns a list of processed document chunks.

        Returns:
            list: A list containing all chunked documents with metadata.
        """
        pdf_corpus = []
        pdf_files = list(self.folder_path.glob("*.pdf"))

        if not pdf_files:
            logging.warning(f"No PDF files found in {self.folder_path}")

        for pdf_file in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_file))
                documents = loader.load()
                chunked_documents = self.text_splitter.split_documents(documents)
                pdf_corpus.extend(chunked_documents)
            except Exception as e:
                logging.error(f"Failed to process {pdf_file.name}: {e}")

        return pdf_corpus

