import openai
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from rapidfuzz import process, fuzz

class NameProcessor:
    def __init__(self, prompt_path, batch_size = 5, debug_print = True): 
        self.DEBUG_PRINT = debug_print # prints batches and prompts 
        self.BATCH_SIZE = batch_size   # large batch size: faster with worse results, small batch size: slower with better results and more api calls $ 
        self.API_KEY = self.__get_api_key() 
        self.client = OpenAI(api_key=self.API_KEY)
        self.BASE_PROMPT = self.__get_base_prompt(prompt_path)
        self.CACHE_PATH = prompt_path + "_cache.json"
        self.cache = {}
        self.__load_cache() # load cache on startup only once
    
    def processNames(self, product_name_list): 
        index_list, cached_list, product_name_list = self.__check_cached_names(product_name_list)
        
        name_list = []
        # run in batches of BATCH_SIZE and combine results
        for i in range(0, len(product_name_list), self.BATCH_SIZE):
            batch_list = product_name_list[i:i + self.BATCH_SIZE]
            if self.DEBUG_PRINT:
                print(f"\nCurrent batch{batch_list}")
            
            # build prompt
            complete_prompt: str = self.BASE_PROMPT
            for name in batch_list:
                complete_prompt += "\n"+ name
            if self.DEBUG_PRINT:
                print(f"\nCurrent prompt: {complete_prompt}")
            # get result
            json_response = self.__get_response_json(complete_prompt)
            result_list = (json.loads(json_response)["grocery_items"])
            for name in result_list:
                name_list.append(name)

        if self.DEBUG_PRINT:
            print(f"API response list: {name_list}")
            print(f"Cache response list: {cached_list}")

        # add new items to cache
        for i in range(len(name_list)):
            self.cache[product_name_list[i]] = name_list[i]
        # update cache if needed
        if len(name_list) > 0:
            self.__save_cache()

        # combine cached and api lists
        for i in range(len(index_list)):
            name_list.insert(index_list[i], cached_list[i])

        return name_list
    
    def __check_cached_names(self, product_name_list, threshold = 80):
        # if item is cached, get the result, otherwise return a new list to check with API
        new_product_name_list = []
        index_list = []
        cached_list = []
        for index, name in enumerate(product_name_list):
            # item is in cache
            if name in self.cache:
                index_list.append(index)
                cached_list.append(self.cache[name])

            # not in cache
            else:
                # fuzzy search
                best_match, score, _ = process.extractOne(name, self.cache.keys(), scorer=fuzz.ratio)
                              
                if best_match and score >= threshold: # close match found  
                    index_list.append(index)
                    cached_list.append(self.cache[best_match])
                else: # no close match found  
                    new_product_name_list.append(name)  
        
        return index_list, cached_list, new_product_name_list 
        
    def __get_response_json(self, prompt):
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]       
        )
        return completion.choices[0].message.content
    
    def __get_api_key(self):
        load_dotenv()
        return os.getenv("OPENAI_API_KEY")

    def __get_base_prompt(self, prompt_path):
        with open(prompt_path, "r") as file:
            return file.read().strip()
    def __load_cache(self):
        try:
            with open(self.CACHE_PATH, 'r') as file:
                self.cache = json.load(file)
        except FileNotFoundError:
            self.cache = {}
    def __save_cache(self):
        with open(self.CACHE_PATH, 'w') as file:
            json.dump(self.cache, file)

def main():
    # sample usage decode receipt product names
    my_decoder = NameProcessor(prompt_path="NameProcessing/.decode_prompt")
    product_list = ["S/MTN.BNLS BREAST", "FZN ORGANIC GREEN BEANS", "Milk Half Gal Almond Unsweeten", "PUB DICED TOMATOES", "PEPPERS GREEN BELL", "BELL PEPPERS RED"]
    decoded_list = my_decoder.processNames(product_name_list=product_list)
    print(f"Final decoded list: {decoded_list}")

    # sample usage fuzzy cache
    my_decoder = NameProcessor(prompt_path="NameProcessing/.decode_prompt")
    product_list = ["S/MTN.BNLS BREEST", "FZN DRGANIC GREEN BEDNS", "Milk Half Gall Almond Unsweeten", "PU DICED TOMATOES", "PEPPERS GREEN BELLL", "BLL PEPPERS RD"]
    decoded_list = my_decoder.processNames(product_name_list=product_list)
    print(f"Final decoded list: {decoded_list}")

     # sample usage map decoded names to generic items
    my_mapper = NameProcessor(prompt_path="NameProcessing/.map_prompt")
    product_list = ["Boneless Chicken Breast", "Organic Green Beans", "Unsweetened Almond Milk", "Diced Tomatoes", "Green Bell Peppers", "Red Bell Peppers"]
    item_list = my_mapper.processNames(product_name_list=product_list)
    print(f"Final item list: {item_list}")

    # TODO 
    # optimize duplicates

if __name__ == "__main__":
    main()