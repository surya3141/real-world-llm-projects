"""
Vector Retriever - Handles document embedding and retrieval
"""
from typing import List, Dict, Optional
import os
from pathlib import Path
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import (
    DirectoryLoader,
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader
)
from langchain.schema import Document


class VectorRetriever:
    """
    Handles document loading, chunking, embedding, and retrieval using FAISS.
    """
    
    def __init__(
        self, 
        embedding_model: str = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        self.embedding_model = embedding_model or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(model=self.embedding_model)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.vectorstore: Optional[FAISS] = None
    
    def load_documents(self, documents_path: str) -> List[Document]:
        """
        Load documents from a directory. Supports TXT, PDF, DOCX.
        
        Args:
            documents_path: Path to directory containing documents
            
        Returns:
            List of Document objects
        """
        documents = []
        documents_path = Path(documents_path)
        
        if not documents_path.exists():
            raise ValueError(f"Documents path does not exist: {documents_path}")
        
        # Load different file types
        loaders = {
            ".txt": TextLoader,
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader
        }
        
        for file_path in documents_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in loaders:
                try:
                    loader_class = loaders[file_path.suffix]
                    loader = loader_class(str(file_path))
                    docs = loader.load()
                    
                    # Add metadata
                    for doc in docs:
                        doc.metadata["source_file"] = file_path.name
                        doc.metadata["file_type"] = file_path.suffix
                    
                    documents.extend(docs)
                    print(f"Loaded: {file_path.name}")
                except Exception as e:
                    print(f"Error loading {file_path.name}: {e}")
        
        print(f"\nTotal documents loaded: {len(documents)}")
        return documents
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks.
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of chunked Document objects
        """
        chunks = self.text_splitter.split_documents(documents)
        print(f"Created {len(chunks)} chunks from {len(documents)} documents")
        return chunks
    
    def create_vectorstore(
        self, 
        documents: List[Document],
        persist_directory: Optional[str] = None
    ) -> FAISS:
        """
        Create FAISS vectorstore from documents.
        
        Args:
            documents: List of Document objects (will be chunked)
            persist_directory: Optional path to save vectorstore
            
        Returns:
            FAISS vectorstore
        """
        # Chunk documents
        chunks = self.chunk_documents(documents)
        
        # Create vectorstore
        print("Creating embeddings and building vector store...")
        self.vectorstore = FAISS.from_documents(
            documents=chunks,
            embedding=self.embeddings
        )
        
        # Persist if directory provided
        if persist_directory:
            persist_path = Path(persist_directory)
            persist_path.mkdir(parents=True, exist_ok=True)
            self.vectorstore.save_local(str(persist_path))
            print(f"Vectorstore saved to: {persist_path}")
        
        return self.vectorstore
    
    def load_vectorstore(self, persist_directory: str) -> FAISS:
        """
        Load existing vectorstore from disk.
        
        Args:
            persist_directory: Path to saved vectorstore
            
        Returns:
            FAISS vectorstore
        """
        persist_path = Path(persist_directory)
        
        if not persist_path.exists():
            raise ValueError(f"Vectorstore path does not exist: {persist_path}")
        
        print(f"Loading vectorstore from: {persist_path}")
        self.vectorstore = FAISS.load_local(
            str(persist_path),
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        
        return self.vectorstore
    
    def retrieve(
        self, 
        query: str, 
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            score_threshold: Optional minimum similarity score
            
        Returns:
            List of dicts with keys: document, score, metadata
        """
        if self.vectorstore is None:
            raise ValueError("Vectorstore not initialized. Call create_vectorstore or load_vectorstore first.")
        
        # Retrieve with scores
        docs_and_scores = self.vectorstore.similarity_search_with_score(
            query=query,
            k=top_k
        )
        
        results = []
        for doc, score in docs_and_scores:
            # Filter by score threshold if provided
            if score_threshold is None or score >= score_threshold:
                results.append({
                    "document": doc.page_content,
                    "score": float(score),
                    "metadata": doc.metadata
                })
        
        return results
    
    def retrieve_documents_only(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[str]:
        """
        Convenience method to get only document texts.
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            
        Returns:
            List of document strings
        """
        results = self.retrieve(query, top_k)
        return [item["document"] for item in results]


if __name__ == "__main__":
    # Example usage
    from dotenv import load_dotenv
    load_dotenv()
    
    # Create sample documents
    sample_docs_dir = Path("data/sample_docs")
    sample_docs_dir.mkdir(parents=True, exist_ok=True)
    
    sample_doc = sample_docs_dir / "france_info.txt"
    sample_doc.write_text("""
    France is a country in Western Europe. Its capital is Paris, which is also its largest city.
    
    Paris is known for its art, culture, and history. The Eiffel Tower is one of the most famous landmarks in Paris.
    
    The Eiffel Tower was built in 1889 and stands 330 meters tall. It was designed by engineer Gustave Eiffel.
    
    France is also famous for its cuisine, including wine, cheese, and pastries.
    """)
    
    print("Testing Vector Retriever\n")
    
    retriever = VectorRetriever()
    
    # Load and create vectorstore
    docs = retriever.load_documents("data/sample_docs")
    vectorstore = retriever.create_vectorstore(docs, "data/vectorstore")
    
    # Test retrieval
    query = "What is the Eiffel Tower?"
    results = retriever.retrieve(query, top_k=2)
    
    print(f"\nQuery: {query}\n")
    print(f"Retrieved {len(results)} documents:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result['score']:.4f}")
        print(f"   Content: {result['document'][:100]}...")
        print(f"   Source: {result['metadata'].get('source_file', 'Unknown')}\n")
