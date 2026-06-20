import requests
import pandas as pd
import time

BASE_URL = "https://en.wikipedia.org/w/api.php"

HEADERS = {
    "User-Agent": "medieval-poetess-collector/1.0 (contact@example.com)"
}

def get_category_members(category):
    members = []
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category}",
        "cmlimit": "500",
        "format": "json"
    }
    while True:
        r = requests.get(BASE_URL, params=params, headers=HEADERS).json()
        members += r["query"]["categorymembers"]
        if "continue" not in r:
            break
        params["cmcontinue"] = r["continue"]["cmcontinue"]
    return members

def get_page_extract(pageid):
    params = {
        "action": "query",
        "pageids": pageid,
        "prop": "extracts|info",
        "exintro": True,
        "inprop": "url",
        "format": "json"
    }
    r = requests.get(BASE_URL, params=params, headers=HEADERS).json()
    page = r["query"]["pages"][str(pageid)]
    return {
        "author": page.get("title", ""),
        "original_text": page.get("extract", ""),
        "source_name": "Wikipedia",
        "source_link": page.get("fullurl", ""),
        "date": ""
    }

def main():
    print("Récupération des membres de la catégorie...")
    members = get_category_members("Medieval_women_writers")
    
    results = []
    for m in members:
        print(f"  → {m['title']}")
        data = get_page_extract(m["pageid"])
        results.append(data)
        time.sleep(0.5)  # respecter les limites Wikipedia

    df = pd.DataFrame(results, columns=["author", "original_text", "date", "source_name", "source_link"])
    df.to_csv("medieval_poetess.csv", index=False)
    print(f"\n{len(results)} entrées sauvegardées dans medieval_poetess.csv")

if __name__ == "__main__":
    main()
