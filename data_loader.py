import pandas as pd
import re
from collections import Counter

def extract_main_ingredient_greek(name: str) -> str:
    # Enlever parenthèses, chiffres, ponctuation
    name = re.sub(r"[()\d\"',.;:!?]", "", name)
    words = name.lower().split()
    stopwords = {"με", "και", "του", "της", "στο", "στα", "το", "τα", "σε", "για", "ένα"}  # mots vides courants en grec
    words = [w for w in words if w not in stopwords and len(w) > 1]

    # Retourner le mot le plus fréquent ou "unknown"
    return words[0] if words else "unknown"

def load_recipe_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8")
    df["categories"] = df["categories"].astype(str)
    df["main_ingredient"] = df["name"].apply(extract_main_ingredient_greek)
    return df
