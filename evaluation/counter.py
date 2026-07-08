import os

def load_count(path: str) -> int:
    if not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    return int(text) if text else 0

def save_count(path: str, count: int) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(count))

def increment(path: str) -> int:
    count = load_count(path) + 1
    save_count(path, count)
    return count