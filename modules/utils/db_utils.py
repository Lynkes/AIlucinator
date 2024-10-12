import os
import shutil
import logging
import json
from ollama import AsyncClient, Client
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from tqdm import tqdm
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
logging.basicConfig(level=logging.INFO)

def initialize_db(save_folderpath: str, embedding_service: str = "ollama") -> Chroma:
    """
    Initializes the Chroma database with the provided embedding service.
    """
    logging.info("Initializing the Chroma database")
    embedding_function=get_embedding_function(embedding_service=embedding_service)
    chromaDB_path = os.path.join(save_folderpath, "chroma")
    db = Chroma(persist_directory=chromaDB_path, embedding_function=embedding_function)
    update_db(data_path=save_folderpath, embedding_function=embedding_function, reset=False)
    return db

def get_embedding_function(embedding_service: str):
    """
    Get the appropriate embedding function based on the selected service.
    """
    if embedding_service == "ollama":
        return OllamaEmbeddings(model="llama3.2:3b-instruct-q8_0",base_url="127.0.0.1")
    elif embedding_service == "bedrock":
        return None (credentials_profile_name="default", region_name="us-east-1")
    else:
        logging.error(f"Unsupported embedding service: {embedding_service}")
        return None

def update_db(data_path: str, embedding_function, reset: bool = False):
    """
    Update the Chroma database with documents from the specified path.
    """
    chromaDB_path = os.path.join(data_path, "chroma")
    if reset:
        logging.info("✨ Clearing Database")
        clear_database(chromaDB_path)

    # Load documents and split them into chunks
    documents_json = load_documents_json(data_path)
    documents_pdf = load_documents_pdf(data_path+"/PDFs/")

    # Process and add documents to the Chroma database
    process_documents_and_add_to_chroma(documents_pdf + documents_json, chromaDB_path, embedding_function)

def load_documents_pdf(data_path: str):
    """
    Load PDF documents from the specified path.

    :param data_path: Path to the directory containing PDF files.
    :return: A list of Document objects.
    """
    logging.info(f"Loading PDF documents from: {data_path}")
    documents = []
    try:
        document_loader = PyPDFDirectoryLoader(data_path)
        documents = document_loader.load()
        if not documents:
            logging.warning(f"No PDF documents found in: {data_path}")
        else:
            logging.info(f"Successfully loaded {len(documents)} PDF documents.")
    except Exception as e:
        logging.error(f"Failed to load PDF documents: {e}")
    return documents

def load_documents_json(data_path: str):
    """
    Load JSON documents from the specified path.
    """
    logging.info(f"Loading JSON documents from: {data_path}")
    documents = []
    try:
        for root, _, files in os.walk(data_path):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        content = extract_content_from_json(data, file_path)
                        if content:
                            documents.append(Document(page_content=content, metadata={"source": file_path}))
    except Exception as e:
        logging.error(f"Failed to load JSON documents: {e}")
    return documents

def extract_content_from_json(data, file_path):
    """
    Extract content from JSON data based on its structure.
    """
    if isinstance(data, dict):
        return data.get("content", "")
    elif isinstance(data, list):
        return " ".join(item.get("content", "") for item in data if isinstance(item, dict))
    else:
        logging.error(f"Unexpected JSON structure in file: {file_path}")
        return ""

def split_documents(documents: list[Document]):
    """
    Split documents into chunks using a character-based text splitter.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len
    )
    return text_splitter.split_documents(documents)

def process_documents_and_add_to_chroma(documents: list[Document], chromaDB_path: str, embedding_function):
    """
    Process documents by splitting and adding them to the Chroma database.

    :param documents: List of Document objects to process.
    :param chromaDB_path: Path to the Chroma database.
    :param embedding_function: The embedding function to use.
    """
    if not documents:
        logging.info("No documents found to process.")
        return

    chunks = split_documents(documents)
    logging.info(f"Processing {len(chunks)} chunks.")
    add_to_chroma(chunks, chromaDB_path, embedding_function)

def add_to_chroma(chunks: list[Document], chromaDB_path: str, embedding_function):
    """
    Add document chunks to the Chroma database.

    :param chunks: List of Document chunks to add.
    :param chromaDB_path: Path to the Chroma database.
    :param embedding_function: The embedding function to use.
    """
    db = Chroma(persist_directory=chromaDB_path, embedding_function=embedding_function)
    chunks_with_ids = calculate_chunk_ids(chunks)

    # Log existing documents
    existing_items = db.get(include=[])  # IDs are always included by default
    existing_ids = set(existing_items["ids"])
    logging.info(f"Number of existing documents in DB: {len(existing_ids)}")

    # Log new chunks
    new_chunks = [chunk for chunk in chunks_with_ids if chunk.metadata["id"] not in existing_ids]
    logging.info(f"Number of new chunks to add: {len(new_chunks)}")
    if new_chunks:
        logging.info("Adding new documents...")
        with tqdm(total=len(new_chunks), desc="Adding new documents") as pbar:
            for chunk in new_chunks:
                db.add_documents([chunk], ids=[chunk.metadata["id"]])
                pbar.update(1)
        logging.info("Persisting changes to the database.")
    else:
        logging.info("No new documents to add.")

def calculate_chunk_ids(chunks: list[Document]):
    """
    Calculate unique IDs for document chunks based on their source and page information.
    """
    last_page_id = None
    current_chunk_index = 0
    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page", "0")
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id
        chunk.metadata["id"] = chunk_id

    return chunks

def clear_database(chromaDB_path: str):
    """
    Clear the Chroma database by removing its directory.
    """
    if os.path.exists(chromaDB_path):
        shutil.rmtree(chromaDB_path)
        logging.info(f"Database cleared at: {chromaDB_path}")

if __name__ == "__main__":
    #embedding_function = get_embedding_function("ollama")
    client=Client(host="127.0.0.1")
    embedding_function=get_embedding_function("ollama")
    update_db(data_path="conversations/GLaDOS", embedding_function=embedding_function, reset=True)
