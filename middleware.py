import os
import re
import json
import base64
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

EMBED_MODEL = "text-embedding-3-small"
MODEL = "gpt-4.1-mini"

TOP_K = 10
CHUNK_SIZE = 1200
MIN_LINES = 20

TEXT_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".c", ".cpp", ".html"}
EXCLUDE = {"tests/", "docs/", "node_modules/", "dist/", "build/"}


def from_upload(text: str, filename="upload"):
    return {filename: text}


def from_github(repo_url: str):
    m = re.match(r"https?://github.com/([^/]+)/([^/]+)", repo_url)
    if not m:
        raise ValueError("Invalid GitHub URL")

    owner, repo = m.groups()

    repo_data = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers=HEADERS
    ).json()

    branch = repo_data.get("default_branch", "main")

    tree = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
        headers=HEADERS
    ).json().get("tree", [])

    files = {}

    for f in tree:
        path = f["path"]

        if f["type"] != "blob":
            continue

        if any(path.startswith(x) for x in EXCLUDE):
            continue

        if not any(path.endswith(ext) for ext in TEXT_EXTS):
            continue

        blob = requests.get(f["url"], headers=HEADERS).json()
        code = base64.b64decode(blob["content"]).decode("utf-8", "ignore")

        if code.count("\n") < MIN_LINES:
            continue

        files[path] = code

    return files


def chunk(text):
    return [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]


def embed(texts):
    if not texts:
        return []
    r = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts
    )
    return [e.embedding for e in r.data]


def build_index(files):
    if not files:
        return []

    docs = []

    for path, code in files.items():
        for i, c in enumerate(chunk(code)):
            if c.strip():
                docs.append({
                    "path": path,
                    "chunk": c,
                    "embedding": None
                })

    if not docs:
        return []

    embeddings = embed([d["chunk"] for d in docs])

    for d, e in zip(docs, embeddings):
        d["embedding"] = e

    return docs


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


def retrieve(index, query):
    if not index:
        return []

    q = embed([query])[0]

    scored = [
        (cosine(q, d["embedding"]), d)
        for d in index
    ]

    scored.sort(reverse=True, key=lambda x: x[0])

    return [d for _, d in scored[:TOP_K]]


def analyze(index):
    if not index:
        raise ValueError("No indexable content found. Check that the repo contains supported file types with at least 20 lines.")

    ctx = retrieve(index, "architecture code quality performance")

    prompt = {
        "task": "Analyze codebase, score is from 0-100",
        "output_format": {
            "overall_score": "number",
            "readability": "number",
            "maintainability": "number",
            "performance": "number",
            "description": "string"
        },
        "code": [c["chunk"] for c in ctx]
    }

    r = client.responses.create(
        model=MODEL,
        input=json.dumps(prompt)
    )

    return json.loads(r.output_text)


def analyze_input(source):
    if isinstance(source, dict):
        files = source

    elif isinstance(source, str) and "github.com" in source:
        files = from_github(source)

    elif isinstance(source, str):
        files = from_upload(source)

    else:
        raise ValueError("Unsupported input type")

    index = build_index(files)
    return analyze(index)


def fetch_repo_and_analyze(url):
    return analyze_input(url)


def analyze_uploaded_file(text):
    return analyze_input(text)