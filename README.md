# Reddit RAG Chatbot 🤖

A Retrieval-Augmented Generation (RAG) chatbot that answers questions based on real Reddit discussions. The system scrapes Reddit content, processes it into a vector database, and uses hybrid search with LLM-powered reranking to provide comprehensive answers.

## Features

- 🔍 **Reddit Scraping**: Automatically scrapes posts and comments from Reddit
- 📚 **Vector Database**: Efficient document storage and retrieval using ChromaDB
- 🎯 **Hybrid Search**: Combines semantic similarity with BM25 keyword matching
- 🧠 **LLM Reranking**: Uses GPT-4 to rerank results for better relevance
- 💬 **Chat Interface**: Clean Streamlit UI for conversational interactions


## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/reddit-rag-chatbot.git
cd reddit-rag-chatbot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# OpenAI API Key (for embeddings and LLM)
OPENAI_API_KEY=your_openai_api_key_here

# OpenRouter API Key (alternative LLM provider)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Reddit API Credentials
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=reddit_rag_app/1.0
```

### 5. Get API Credentials

#### Reddit API:
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" as the app type
4. Copy the client ID (under the app name) and client secret

#### OpenAI API:
1. Go to https://platform.openai.com/api-keys
2. Create a new API key

#### OpenRouter API:
1. Go to https://openrouter.ai/keys
2. Create a new API key

## Usage

### Run the Application

```bash
streamlit run app.py
```

## Configuration

Edit `config.py` to customize:

- `MAX_TOKENS`: Maximum tokens per chunk (default: 512)
- `MIN_TOKENS`: Minimum tokens per chunk (default: 100)
- `OVERLAP`: Sentence overlap between chunks (default: 2)
- `K`: Number of candidates for hybrid search (default: 20)
- `TOP_K`: Final number of results after reranking (default: 5)

## Deployment

### Streamlit Community Cloud

1. Push your code to GitHub (make sure `.env` is in `.gitignore`)
2. Go to https://streamlit.io/cloud
3. Deploy from your GitHub repository
4. Add secrets in the Streamlit dashboard under "Settings" → "Secrets":

```toml
OPENAI_API_KEY = "your_key_here"
OPENROUTER_API_KEY = "your_key_here"
REDDIT_CLIENT_ID = "your_id_here"
REDDIT_CLIENT_SECRET = "your_secret_here"
REDDIT_USER_AGENT = "reddit_rag_app/1.0"
```

### Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py"]
```

Build and run:

```bash
docker build -t reddit-rag-chatbot .
docker run -p 8501:8501 --env-file .env reddit-rag-chatbot
```


- Open an issue on GitHub
- Check existing issues for solutions
- Review the documentation at [Streamlit Docs](https://docs.streamlit.io)
