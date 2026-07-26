# Status: 
Complete (not as idealized)

# Origin

After getting injured from running, I understood how important it is to be cautious with my training and dedicate time to prevent injuries. 
In this light, I came up with this idea. 
It is a simple tracking tool, in which I can log some health metrics (weight, VO2 Max, etc); my workouts and future races.
From the information the user logs, I can then calculate sports science metrics, such as chronic load, training stress balance, among others. 
This would only be useful if the user could interpret that data, that is why I then generated synthethic data to train a Machine Learning model
to predict the likelihood of injury - presented as a percentage of healthiness (since showing 80% healthy is more pleasant than showing 20% injured). 
This model became a tool the AI agent could call, proposing different workouts, techniques and answering questions the user may have.
To prevent hallucinations and bad information, the agent was fed some of the best books in the running space, with a RAG system. 

### Important Note: 
To keep costs low I chose to use a local model (Ollama qwen2.5:3B).
This model has known limitations, namely hallucinations and low accuracy. A bigger, and thus more reliable model was also tested, (Ollama qwen2.5:7b) and the results were indeed better (more personalized and real), but my machine struggled to run it, forcing me to use the smallest model instead.
In conclusion, the app is functional, but not as one would have liked.

The frontend was done by AI.

# Project Structure
SummerProject/
|
|- AI/
    |-agent.py                 -> AI's main loop
    |-rag.py                   
    |-ingest.py                 -> takes the pdfs and creates one big file, to then save on the vector database
    |-tools.py                  -> all the tools the AI needs to work
    |-advanced marathoning.pdf  -> the book used to give context
|-ML/
    |-gen_data.py               -> generates synthetic data to feed the model
    |-train.py                  -> cleans data, trains the model, predicts result
    |-synthetic_data.csv        -> the result of gen_data
    |-injury_risk_model.pkl
    |-session_type_encoder.pkl    
|-alembic/
|- routers/
    |-ai_agent.py
    |-athletes.py
    |-auth.py
    |-health_metrics.py
    |-predict_risk.py
    |-races.py
    |workouts.py
  |
  |-main.py
  |-models.py          -> the tables in the database
  |-ml_features.py     -> uses features.py to compute the features for the ML model, accesses db
  |-cache.py           -> initiates the redis client
  |-database.py
  |-predict.py         -> Gets features, calls model and generates a prediction
  |-security.py        -> password hashing etc
  |-worker.py          -> handles background jobs (Arq)
  |-features.py        -> computes the rolling features for the athlete, fed into the ML model

# Tech Stack

## Backend

Python
FastAPI
SQLAlchemy
Alembic
Arq

## Database

PostgreSQL
Redis

## Machine Learning

scikit-learn
pandas
NumPy

## AI

RAG 
Local LLM 
Vector search
Qdrant as vector database and sentence-transformers for embeddings

## Infrastructure

Docker
Git

## How to run:

### 1. Prerequisites
- Python 3.11+ and a virtual environment
- [Docker Desktop](https://www.docker.com/products/docker-desktop) running
- [Ollama](https://ollama.com) installed, with the model pulled:
```bash
  ollama pull qwen2.5:3b
```

### 2. Clone and set up the environment
```bash
git clone <your-repo-url>
cd SummerProject
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```
> If `requirements.txt` doesn't exist yet, generate it once from a working environment with `pip freeze > requirements.txt`.

### 3. Start the infrastructure containers
```bash
docker run --name pg-dev -e POSTGRES_PASSWORD=devpass -e POSTGRES_DB=athletelog -p 5432:5432 -d postgres:16
docker run --name redis-dev -p 6379:6379 -d redis:7
docker run --name qdrant-dev -p 6333:6333 -d qdrant/qdrant
```
(If you've run these before, use `docker start pg-dev redis-dev qdrant-dev` instead.)

### 4. Configure environment variables
Create a `.env` file in the project root:
DATABASE_URL=postgresql+asyncpg://postgres:devpass@localhost:5432/athletelog
SYNC_DATABASE_URL=postgresql+psycopg2://postgres:devpass@localhost:5432/athletelog
SECRET_KEY=<generate one: python -c "import secrets; print(secrets.token_hex(32))">

### 5. Run database migrations
```bash
alembic upgrade head
```

### 6. Ingest the RAG source material (one-time, or whenever the source PDFs change)
```bash
python AI/ingest.py
```

### 7. Train the ML model (one-time, or to retrain on new synthetic data)
```bash
python ML/gen_data.py
python ML/train.py
```

### 8. Run the app — three processes, three terminals

**Terminal 1 — API server:**
```bash
uvicorn main:app --reload
```

**Terminal 2 — background worker (ML predictions + automatic coach messages):**
```bash
arq worker.WorkerSettings
```

**Terminal 3 — Ollama (often already running as a background service — check with `ollama ps` before starting a second instance):**
```bash
ollama serve
```

### 9. Open the frontend
Open `index.html` directly in a browser, or serve it:
```bash
python -m http.server 5500
```
then visit `http://localhost:5500`.

Sign up, log a workout, and check the dashboard...
