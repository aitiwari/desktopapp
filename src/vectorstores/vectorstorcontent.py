from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings  # Corrected import
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document

class DocumentProcessor:
    def __init__(self, model_name: str, persist_directory: str, collection_name: str):
        """
        Initializes the DocumentProcessor with the specified model, persistence directory, and collection name.

        :param model_name: The name of the SentenceTransformer model to use for embeddings.
        :param persist_directory: The directory where the Chroma vector store will be persisted.
        :param collection_name: The name of the collection in the Chroma vector store.
        """
        self.model_name = model_name
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model = HuggingFaceEmbeddings(model_name=model_name)
        self.text_splitter = CharacterTextSplitter(chunk_size=2000, chunk_overlap=0)

    def process_document(self, text: str):
        """
        Processes the given document by splitting it into chunks and storing them in Chroma DB.

        :param text: The document text to process.
        """
        # Split the document into 2,000-character chunks
        chunks = self.text_splitter.split_text(text)
        
        # Wrap each chunk in a LangChain Document object
        documents = [Document(page_content=chunk) for chunk in chunks]
        
        # Create a Chroma vector store and add the chunks
        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_model,
            persist_directory=self.persist_directory,
            collection_name=self.collection_name
        )
        print(f"Document processed and stored in collection '{self.collection_name}'.")

if __name__ == "__main__":
    # Example usage
    model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    persist_directory = "./vectordb"  # Replace with your desired path
    collection_name = "your_collection_name"

    document_processor = DocumentProcessor(
        model_name=model_name,
        persist_directory=persist_directory,
        collection_name=collection_name
    )

    document = "Your large document text goes here..."
    document_processor.process_document(document)
