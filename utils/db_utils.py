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
