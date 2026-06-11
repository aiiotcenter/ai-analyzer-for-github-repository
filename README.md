# gitreview

A Python-based REST API that analyzes code quality using AI. Feed it a GitHub repository URL or upload a source file, and it returns a scored breakdown of your codebase's readability, maintainability, and performance.

---

## How It Works

1. **Fetch** — Pull source files from a GitHub repo (via the GitHub API) or accept a direct file upload.
2. **Chunk & Embed** — Split the code into chunks and generate vector embeddings using OpenAI's `text-embedding-3-small` model.
3. **Retrieve** — Use cosine similarity to find the most relevant code chunks for a quality-focused query.
4. **Analyze** — Pass the top chunks to `gpt-4.1-mini` and receive a structured JSON score.

---

## API Endpoints

### `POST /analyze_repo/`
Analyze a public GitHub repository.

**Request body:**
```json
{
  "github_url": "https://github.com/owner/repo"
}
```

**Response:**
```json
{
  "overall_score": 78,
  "readability": 82,
  "maintainability": 75,
  "performance": 70,
  "description": "The codebase is generally well-structured..."
}
```

---

### `POST /upload/`
Analyze a locally uploaded source file (UTF-8 text).

**Request:** `multipart/form-data` with a `file` field.

**Response:** Same structure as above.

---

## Setup

### Prerequisites
- Python 3.9+
- An [OpenAI API key](https://platform.openai.com/account/api-keys)
- *(Optional)* A [GitHub Personal Access Token](https://github.com/settings/tokens) to avoid rate limits on private/large repos

### Installation

```bash
git clone https://github.com/BADIR64/gitreview.git
cd gitreview
pip install flask flask-cors openai python-dotenv requests
```

### Configuration

Create a `.env` file in the project root:

```env
OPENAI_API=your_openai_api_key
GITHUB_TOKEN=your_github_token   # optional but recommended
```

### Running the server

```bash
python server.py
```

The API will be available at `http://localhost:5000`.

---

## Project Structure

```
gitreview/
├── server.py       # Flask app — defines the API routes
├── middleware.py   # Core logic — fetching, chunking, embedding, and analysis
└── .env            # Environment variables (not committed)
```

---

## Supported File Types

`.py` `.js` `.ts` `.jsx` `.tsx` `.java` `.go` `.rs` `.c` `.cpp` `.html`

Files under `tests/`, `docs/`, `node_modules/`, `dist/`, or `build/` are excluded. Files with fewer than 20 lines are also skipped.

---

## License

MIT
