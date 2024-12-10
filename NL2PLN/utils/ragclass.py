import uuid
import requests
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from requests.exceptions import RequestException, Timeout

class RAG:
    def __init__(self, collection_name="sentences", ollama_base_url="http://localhost:11434", qdrant_url="http://localhost:6333", reset_db=False):
        self.collection_name = collection_name
        self.ollama_base_url = ollama_base_url
        self.qdrant_client = QdrantClient(qdrant_url)
        if reset_db:
            self.delete_collection()
        self.ensure_collection()

    def get_embedding(self, text):
        """
        Get the embedding for a given text using Ollama's API.
        """
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
                timeout=30
            )
            response.raise_for_status()
            return response.json()['embedding']
        except Timeout:
            print("Timeout occurred while getting embedding from Ollama API")
            raise
        except RequestException as e:
            print(f"Error occurred while getting embedding: {str(e)}")
            raise

    def store_embedding(self, data):
        """
        Store the embedding of a JSON object in Qdrant.
        """
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary (JSON object)")
        
        text = data.get('sentence', '') + ' ' + data.get('pln', '')
        embedding = self.get_embedding(text)
        
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload=data
                )
            ]
        )

    def delete_collection(self):
        """
        Delete the collection if it exists.
        """
        try:
            self.qdrant_client.delete_collection(self.collection_name)
            print(f"Deleted '{self.collection_name}' collection from Qdrant")
        except Exception as e:
            print(f"Error deleting collection: {str(e)}")

    def ensure_collection(self):
        """
        Ensure the collection exists in Qdrant.
        """
        collections = self.qdrant_client.get_collections().collections
        if not any(collection.name == self.collection_name for collection in collections):
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
            )
            print(f"Created '{self.collection_name}' collection in Qdrant")

    def search_similar(self, sentence, limit=3):
        try:
            query_vector = self.get_embedding(sentence)
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
            similar_items = [hit.payload for hit in search_result]
            return similar_items
        except Timeout:
            print("Timeout occurred during the search operation")
            return []
        except UnexpectedResponse as e:
            print(f"Unexpected response from Qdrant: {str(e)}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            return []

    def search_exact(self, sentence):
        """
        Search for an exact match of the given sentence in Qdrant.
        """
        try:
            query_vector = self.get_embedding(sentence)
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=10  # Arbitrary limit to get a reasonable number of candidates
            )
            for hit in search_result:
                if hit.payload.get('sentence') == sentence:
                    return hit.payload
            return None
        except Timeout:
            print("Timeout occurred during the search operation")
            return None
        except UnexpectedResponse as e:
            print(f"Unexpected response from Qdrant: {str(e)}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            return None
