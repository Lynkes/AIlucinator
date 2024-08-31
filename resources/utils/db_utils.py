import os
import shutil
import logging
import json
from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.embeddings.bedrock import BedrockEmbeddings
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFDirectoryLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain_community.vectorstores import Chroma
from tqdm import tqdm
import requests
from langchain_chroma import Chroma
from resources.populate_database import get

def initialize_db(save_folderpath: str, embedding_service: str = "ollama") -> Chroma:
    """
    Initializes the Chroma database with the provided embedding service.

    :param save_folderpath: Path to the directory where the database should be saved.
    :param embedding_service: Name of the embedding service to use.
    :return: An initialized Chroma database instance.
    """
    embedding_function = get(embedding_service)
    chromaDB = save_folderpath + "/chroma"
    db = Chroma(persist_directory=chromaDB, embedding_function=embedding_function)
    return db

def get(embedding_service):
    if embedding_service == "huggingface":
        model_name = "sentence-transformers/all-mpnet-base-v2"
        model_kwargs = {'device': 'cuda'}
        encode_kwargs = {'normalize_embeddings': False}
        embeddings = HuggingFaceEmbeddings(model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs)
    elif embedding_service == "ollama":
        embeddings = OllamaEmbeddings(model="llama3.1")
    elif embedding_service == "bedrock":
        embeddings = BedrockEmbeddings(credentials_profile_name="default", region_name="us-east-1")
    # 
    return embeddings


embedding_service = "ollama"

def update_DB(data_path, reset=False):
    chromaDB = data_path+"/chroma"
    # Clear the database if needed
    if reset:
        print("✨ Clearing Database")
        clear_database(chromaDB)

    # Load documents and split them into chunks
    documents = load_documentsJSON(data_path)
    chunks = split_documents(documents)
    add_to_chroma(chunks,chromaDB)

def load_documentsJSON(data_path):
    try:
        documents = []
        for root, dirs, files in os.walk(data_path):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            content = data.get("content", "")
                        elif isinstance(data, list):
                            content = " ".join(item.get("content", "") for item in data if isinstance(item, dict))
                        else:
                            logging.error(f"Unexpected JSON structure in file: {file_path}")
                            continue
                        documents.append(Document(page_content=content, metadata={"source": file_path}))
        return documents
    except Exception as e:
        logging.error(f"Failed to load JSON documents: {e}")
        return []

def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

def add_to_chroma(chunks: list[Document], chromaDB):
            # Load the existing database.
            db = Chroma(
                persist_directory=chromaDB, embedding_function=get(embedding_service=embedding_service)
            )

            # Calculate Page IDs.
            chunks_with_ids = calculate_chunk_ids(chunks)

            # Add or Update the documents.
            existing_items = db.get(include=[])  # IDs are always included by default
            existing_ids = set(existing_items["ids"])
            print(f"Number of existing documents in DB: {len(existing_ids)}")

            # Only add documents that don't exist in the DB.
            new_chunks = [chunk for chunk in chunks_with_ids if chunk.metadata["id"] not in existing_ids]

            if new_chunks:
                print(f"👉 Adding new documents: {len(new_chunks)}")
                new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
                with tqdm(total=len(new_chunks)) as pbar:
                    for _ in new_chunks:
                        db.add_documents(new_chunks, ids=new_chunk_ids)
                        pbar.update(1)  # Update progress bar for each chunk processed
                db.persist()
            else:
                print("✅ No new documents to add")

def calculate_chunk_ids(chunks):
    last_page_id = None
    current_chunk_index = 0
    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id
        chunk.metadata["id"] = chunk_id

    return chunks

def clear_database(chromaDB):
    if os.path.exists(chromaDB):
        shutil.rmtree(chromaDB)

if __name__ == "__main__":
    update_DB(data_path="conversations\GLaDOS", reset=False)
