import os
import shutil
import logging
import json
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

logging.basicConfig(level=logging.INFO)

# Caminho padrão de armazenamento do Qdrant
QDRANT_PATH = os.path.join(os.getcwd(), "qdrant_storage")


# === Inicialização da base vetorial ===
def initialize_db(save_folderpath: str = "conversations/__character_name__/qdrant",
                  collection_name: str = "memoria_local",
                  reset: bool = False) -> QdrantClient:
    """
    Inicializa o banco Qdrant local e retorna o cliente configurado.
    """

    os.makedirs(QDRANT_PATH, exist_ok=True)

    client = QdrantClient(path=QDRANT_PATH)

    if reset:
        try:
            client.delete_collection(collection_name)
            logging.info("🧹 Base Qdrant limpa com sucesso.")
        except Exception:
            pass

    if collection_name not in [c.name for c in client.get_collections().collections]:
        logging.info(f"🧠 Criando coleção vetorial '{collection_name}'...")
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )

    logging.info("✅ Qdrant inicializado com sucesso.")
    return client


# === Carregamento de embeddings offline ===
def get_embedding_function(model_name="BAAI/bge-base-pt-v1.5"):
    """
    Retorna o modelo de embeddings local.
    """
    logging.info(f"Carregando modelo local de embeddings: {model_name}")
    model = SentenceTransformer(model_name)
    return model


# === Inserção de documentos ===
def update_db(data_path: str, embedding_model, qdrant_client, collection_name="memoria_local"):
    """
    Atualiza o banco Qdrant com documentos da pasta especificada.
    """
    pdfs = load_documents_pdf(os.path.join(data_path, "PDFs"))
    jsons = load_documents_json(data_path)

    docs = pdfs + jsons
    if not docs:
        logging.warning("Nenhum documento encontrado para indexar.")
        return

    logging.info(f"📄 Total de documentos carregados: {len(docs)}")

    embeddings = []
    textos = []

    for doc in tqdm(docs, desc="Gerando embeddings locais"):
        textos.append(doc["content"])
        embeddings.append(embedding_model.encode(doc["content"]).tolist())

    logging.info("🧩 Inserindo embeddings no Qdrant...")
    points = [
        PointStruct(
            id=int(np.random.randint(1e9)),
            vector=emb,
            payload={"texto": txt, "origem": doc["source"]}
        )
        for emb, txt, doc in zip(embeddings, textos, docs)
    ]

    qdrant_client.upsert(collection_name=collection_name, points=points)
    logging.info("✅ Base Qdrant atualizada com sucesso.")


# === Carregadores de documentos ===
def load_documents_pdf(data_path: str):
    """
    Carrega PDFs (texto plano) da pasta especificada.
    """
    from langchain_community.document_loaders import PyPDFDirectoryLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    if not os.path.exists(data_path):
        logging.warning(f"Nenhum diretório PDF encontrado: {data_path}")
        return []

    logging.info(f"📚 Carregando PDFs de {data_path}...")
    loader = PyPDFDirectoryLoader(data_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
    chunks = splitter.split_documents(docs)

    formatted = [{"content": c.page_content, "source": c.metadata.get("source", "pdf")} for c in chunks]
    return formatted


def load_documents_json(data_path: str):
    """
    Carrega documentos JSON.
    """
    documentos = []
    for root, _, files in os.walk(data_path):
        for file in files:
            if file.endswith(".json"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict) and "content" in data:
                        documentos.append({"content": data["content"], "source": path})
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "content" in item:
                                documentos.append({"content": item["content"], "source": path})
                except Exception as e:
                    logging.error(f"Erro ao ler {path}: {e}")
    return documentos


def clear_database(collection_name="memoria_local"):
    """
    Remove completamente uma coleção Qdrant local.
    """
    client = QdrantClient(path=QDRANT_PATH)
    try:
        client.delete_collection(collection_name)
        logging.info(f"🧹 Coleção '{collection_name}' apagada com sucesso.")
    except Exception as e:
        logging.error(f"Falha ao apagar coleção: {e}")


if __name__ == "__main__":
    # Exemplo de uso local
    model = get_embedding_function()
    client = initialize_db(reset=True)
    update_db(data_path="conversations/GLaDOS", embedding_model=model, qdrant_client=client)
