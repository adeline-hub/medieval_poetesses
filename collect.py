import requests
import pandas as pd
import time

BASE_URL = "https://en.wikipedia.org/w/api.php"

HEADERS = {
    "User-Agent": "medieval-poetess-collector/1.0 (contact@example.com)"
}

CATEGORIES = [
    "Medieval_women_poets",
    "Women_writers_(medieval)"
]


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
    members = []
    for cat in CATEGORIES:
        print(f"  → Catégorie : {cat}")
        members += get_category_members(cat)

    # Dédoublonner par pageid
    seen = set()
    unique = []
    for m in members:
        if m["pageid"] not in seen:
            seen.add(m["pageid"])
            unique.append(m)

    results = []
    for m in unique:
        print(f"  → {m['title']}")
        data = get_page_extract(m["pageid"])
        results.append(data)
        time.sleep(0.5)

    df = pd.DataFrame(results, columns=["author", "original_text", "date", "source_name", "source_link"])
    df.to_csv("/app/output/medieval_poetess.csv", index=False)
    print(f"\n{len(results)} entrées sauvegardées.")

if __name__ == "__main__":
    main()
