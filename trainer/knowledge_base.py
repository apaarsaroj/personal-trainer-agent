import os
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from trainer.pubmed_fetcher import fetch_fitness_knowledge

KNOWLEDGE_DIR = "data/fitness_knowledge"
CHROMA_PATH = "data/chroma_db"

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection("fitness_knowledge")
model = SentenceTransformer("all-MiniLM-L6-v2")

def load_markdown_files() -> list[str]:
    docs = []
    for filename in os.listdir(KNOWLEDGE_DIR):
        if filename.endswith(".md"):
            with open(os.path.join(KNOWLEDGE_DIR, filename), "r") as f:
                docs.append(f.read())
    return docs

def build_knowledge_base():
    print("Loading markdown files...")
    markdown_docs = load_markdown_files()
    
    print("Fetching PubMed abstracts...")
    pubmed_docs = fetch_fitness_knowledge()
    
    all_docs = markdown_docs + pubmed_docs
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    
    chunks = splitter.create_documents(all_docs)
    texts = [c.page_content for c in chunks]
    
    print(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts).tolist()
    
    collection.add(
        documents=texts,
        embeddings=embeddings,
        ids=[f"chunk_{i}" for i in range(len(texts))]
    )
    
    print(f"Knowledge base built — {len(texts)} chunks stored.")

def retrieve(query: str, n_results: int = 5) -> list[str]:
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )
    return results["documents"][0]