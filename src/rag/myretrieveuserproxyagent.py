from typing import Dict, List, Union
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from langchain.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings 

from typing import TypedDict, Optional, List, Tuple

# Define the Metadata and Vector types (placeholders)
Metadata = dict
Vector = List[float]
ItemID = str

# Define the Document class
class Document(TypedDict):
    """A Document is a record in the vector database.

    id: ItemID | the unique identifier of the document.
    content: str | the text content of the chunk.
    metadata: Metadata, Optional | contains additional information about the document such as source, date, etc.
    embedding: Vector, Optional | the vector representation of the content.
    """
    id: ItemID
    content: str
    metadata: Optional[Metadata]
    embedding: Optional[Vector]

# Define QueryResults type
QueryResults = List[List[Tuple[Document, float]]]

# Function to convert the input format to the Document class
def convert_to_document(input_docs: List[dict]) -> List[Document]:
    documents = []
    for idx, doc in enumerate(input_docs):
        document = Document(
            id=idx + 1,  # Assign a unique ID (can be customized)
            content=doc.page_content,  # Map page_content to content
            metadata=doc.metadata,  # Use metadata if available, else empty dict
            embedding=None  # Placeholder for embedding
        )
        documents.append(document)
    return documents
    
    

class MyRetrieveUserProxyAgent(RetrieveUserProxyAgent):
    
    def query_vector_db(
        self,
        query_texts: List[str],
        n_results: int = 10,
        search_string: str = "",
        **kwargs,
    ) -> Dict[str, Union[List[str], List[List[str]]]]:
        model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        persist_directory = "./vectordb"  # Replace with your desired path
        embedding_model = HuggingFaceEmbeddings(model_name=model_name)
        
        
        # define your own query function here
        vector_store = Chroma(
                 embedding_function=embedding_model,
                persist_directory=persist_directory,
                collection_name=self._collection_name
            )
        docs = vector_store.similarity_search(query_texts)
        return docs
    
   
    
    def retrieve_docs(self, problem: str, n_results: int = 20, search_string: str = "", **kwargs):
        res = self.query_vector_db(
            query_texts=problem,
            n_results=n_results,
            search_string=search_string,
            **kwargs,
        )
        
        # Convert the input data to the Document class format
        documents = convert_to_document(res)
        self._results = [[documents]]
        
    @staticmethod
    def get_max_tokens(model="gpt-3.5-turbo"):
        if "32k" in model:
            return 32000
        elif "16k" in model:
            return 16000
        elif "gpt-4" in model:
            return 8000
        else:
            return 32000
            