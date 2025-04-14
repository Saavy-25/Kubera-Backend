import openai
import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

class EmbeddingVectorManager:
    def __init__(self, cache_path):
        self.API_KEY = self.__get_api_key() 
        self.client = OpenAI(api_key=self.API_KEY)
        self.CACHE_PATH = cache_path
        self.cache = {}
        self.__load_cache() # load cache on startup only once
    
    def getEmbedding(self, genericName):
        if genericName in self.cache: # embedding already generated
            return self.cache[genericName]
        
        embedding = self.__generate_embedding(genericName)
        self.cache[genericName] = embedding # add embedding to cache
        self.__save_cache()
        return embedding
    
    def __generate_embedding(self, genericName):
        response = openai.embeddings.create(
            input=genericName,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding

    def __get_api_key(self):
        load_dotenv()
        return os.getenv("OPENAI_API_KEY")
    
    def __load_cache(self):
        try:
            self.cache = np.load(self.CACHE_PATH, allow_pickle=True).item()
        except FileNotFoundError:
            self.cache = {}

    def __save_cache(self):
        np.save(self.CACHE_PATH, self.cache)

def main():
    my_manager = EmbeddingVectorManager(cache_path="NameProcessing/vector_cache")
    embedding = my_manager.getEmbedding("Mayonnaise")
    embedding2 = my_manager.getEmbedding("Green Apples")
    print(f"Embedding vector Mayo: {embedding}")
    print(f"Embedding vector Apple: {embedding2}")

if __name__ == "__main__":
    main()