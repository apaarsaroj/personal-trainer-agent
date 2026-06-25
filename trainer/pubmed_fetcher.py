from Bio import Entrez
import time

Entrez.email = "apaarsaroj@gmail.com"

def search_pubmed(query: str, max_results:int = 10) -> list[str]:

    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    record = Entrez.read(handle)
    handle.close()

    ids = record["IdList"]

    if not ids:
        return []
    
    handle = Entrez.efetch(db="pubmed", id=ids, rettype="abstract", retmode="text")
    abstracts = handle.read()
    handle.close()

    time.sleep(0.5)

    return abstracts

def fetch_fitness_knowledge() -> list[str]:
    
    queries = [
        "resistance training muscle hypertrophy sets reps",
        "protein intake muscle building athletes",
        "progressive overload strength training beginners",
        "rest intervals resistance training performance",
        "compound exercises muscle activation",
        "injury prevention resistance training form",
        "sleep recovery muscle protein synthesis",
        "nutrition timing pre post workout"
    ]
    
    all_abstracts = []
    
    for query in queries:
        print(f"Fetching: {query}")
        try:
            result = search_pubmed(query, max_results=5)
            if result:
                all_abstracts.append(result)
        except Exception as e:
            print(f"Skipped '{query}' — {e}")
        time.sleep(1)
    
    return all_abstracts