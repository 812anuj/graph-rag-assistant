from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

class TextSplitter:
    def __init__(
            self,
            chunk_size: int = 1000,
            chunk_overlap: int = 200,
    ):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True,
        )

    def split_documents(
            self,
            document: list[Document],
    ) -> list[Document]:
        chunks = self.splitter.split_documents(document)
        return chunks

