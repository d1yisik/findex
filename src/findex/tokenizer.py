import re

def tokenize(text: str) -> list[str]:
    #Розбиває текст на токени (слова) у нижньому регістрі.
    return re.findall(r"\w+", text.lower())