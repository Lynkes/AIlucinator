import gensim
import json
from gensim.models import Word2Vec
from annoy import AnnoyIndex
from numpy.linalg import norm
import numpy as np

def load_sentences_from_json(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
        sentences = data.get('internal', [])
    return sentences

# Load sentences from the JSON file
sentences = load_sentences_from_json('history_Hannah.json')


# Load pre-trained Word2Vec model
word2vec_model = Word2Vec.load("path/to/word2vec/model")


# Create sentence embeddings
def sentence_embedding(sentence, model):
    words = sentence.split()
    vector = sum(model.wv[word] for word in words if word in model.wv) / len(words)
    return vector

# Calculate cosine similarity
def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

# Build an index
embedding_size = word2vec_model.vector_size
annoy_index = AnnoyIndex(embedding_size)

# Index your sentences
sentences = ["Your dataset sentences go here"]
for i, sentence in enumerate(sentences):
    vector = sentence_embedding(sentence, word2vec_model)
    annoy_index.add_item(i, vector)

annoy_index.build(10)  # 10 trees for the index (adjust as needed)

# Perform a similarity search
query = "Your query sentence"
query_vector = sentence_embedding(query, word2vec_model)

# Find the most similar sentences and calculate similarity scores
similar_indices = annoy_index.get_nns_by_vector(query_vector, 5)  # Adjust the number of results as needed
similar_sentences = [sentences[i] for i in similar_indices]
similarities = [cosine_similarity(query_vector, sentence_embedding(sent, word2vec_model)) for sent in similar_sentences]

# Display similar sentences and their similarity scores
for i, (sent, similarity) in enumerate(zip(similar_sentences, similarities), 1):
    print(f"Similarity {i}: {similarity * 100:.2f}%")
    print(f"Sentence {i}: {sent}\n")
