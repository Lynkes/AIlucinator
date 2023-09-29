import json
from sklearn.metrics.pairwise import cosine_similarity
import re
from nltk.tokenize import word_tokenize
from gensim.models import Word2Vec
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer

# Load pre-trained Word2Vec model
w2v_model = Word2Vec.load('path/to/your/word2vec/model')

kkkk
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    tokens = word_tokenize(text)
    return tokens


def calculate_similarity1(prompt, sentence, model):
    prompt_tokens = preprocess_text(prompt)
    sentence_tokens = preprocess_text(sentence)
    
    prompt_embedding = [model[word] for word in prompt_tokens if word in model]
    sentence_embedding = [model[word] for word in sentence_tokens if word in model]

    if not prompt_embedding or not sentence_embedding:
        return 0.0  # Handle the case of empty embeddings

    similarity = cosine_similarity([prompt_embedding], [sentence_embedding])[0][0]
    return similarity


def load_sentences_from_json(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
        sentences = data.get('internal', [])
    return sentences

def calculate_similarity2(prompt, sentence, vectorizer):
    # Create a document-term matrix for the prompt and sentence
    dtm = vectorizer.transform([prompt, sentence])
    
    # Convert the document-term matrix to dense format
    dtm = dtm.toarray()
    
    # Calculate cosine similarity
    similarity = cosine_similarity(dtm)
    
    # The similarity[0][1] value represents the similarity between the prompt and sentence
    return similarity[0][1]

def search_similar_sentences(prompt, sentences, vectorizer):
    similarities = [(sentence, calculate_similarity2(prompt, sentence, vectorizer)) for sentence in sentences]
    sorted_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)
    return sorted_similarities


# Load sentences from the JSON file
sentences = load_sentences_from_json('history_Hannah.json')

# Create a CountVectorizer for text vectorization
vectorizer = CountVectorizer()

prompt = "Please summarize the main ideas of the article."

relevant_sentences = search_similar_sentences(prompt, sentences, vectorizer)

for sentence, similarity in relevant_sentences:
    print(f"Similarity: {similarity:.2f} - Sentence: {sentence.strip()}")
