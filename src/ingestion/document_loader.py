from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader

class DocumentLoader:

    def load_pdf(self, file_path: str | Path):

        # Convert the given path into a Path object
        pdf_path = Path(file_path)

        # Check whether the PDF exists
        if not pdf_path.exists():
            raise FileNotFoundError(
                f"PDF file not found: {pdf_path}"
            )

        # Check whether the file is a PDF
        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError("The provided file must be a PDF.")

        # Create the PDF loader
        loader = PyPDFLoader(str(pdf_path))

        # Extract text and metadata from every page
        documents = loader.load()

        return documents
