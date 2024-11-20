import umap
import numpy as np
import pandas as pd
import plotly.express as px
from langchain_community.embeddings.ollama import OllamaEmbeddings
import logging

# pip install umap-learn plotly pandas numpy

def get_embeddings_from_model(texts):
    """
    Generate embeddings for a list of texts using the Llama model.
    """
    embedding_model = OllamaEmbeddings(model="llama3.1")
    embeddings = embedding_model._embed(texts)  # Assuming embed is the method to get embeddings
    return embeddings

def visualize_embeddings(texts, n_components=3):
    """
    Visualize embeddings generated from the model in 3D.
    """
    logging.info("Generating embeddings for provided texts...")
    
    # Get embeddings from the model
    embeddings = get_embeddings_from_model(texts)

    # Ensure the embeddings exist and are not empty
    embeddings = np.array(embeddings)
    
    if embeddings.size == 0:
        logging.error("No embeddings generated from the model.")
        return

    # Ensure embeddings is a 2D array
    if embeddings.ndim == 1:
        logging.error("Embeddings are 1D; expected 2D. Ensure your texts produce valid embeddings.")
        return

    # Convert to dense if necessary
    if hasattr(embeddings, 'toarray'):  # Check if embeddings are sparse
        embeddings = embeddings.toarray()

    # Apply UMAP to reduce to 3D
    reducer = umap.UMAP(n_components=n_components)
    embeddings_3d = reducer.fit_transform(embeddings)

    # Create a DataFrame for easier plotting
    df = pd.DataFrame(embeddings_3d, columns=['x', 'y', 'z'])
    df['metadata'] = texts  # Use texts as labels for points

    # Plot the 3D scatter
    logging.info("Creating 3D scatter plot...")
    fig = px.scatter_3d(df, x='x', y='y', z='z', text='metadata', title='3D Visualization of Embeddings')
    fig.show()

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example texts to visualize
    texts = [
        "This is the first document.",
        "This is the second document.",
        "And here is the third one."
    ]
    
    visualize_embeddings(texts)
