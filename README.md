# Status: Complete (not as idealized)

# Origin

After getting injured from running, I understood how important it is to be cautious with my training and dedicate time to prevent injuries. 
In this light, I came up with this idea. 
It is a simple tracking tool, in which I can log some health metrics (weight, VO2 Max, etc); my workouts and future races.
From the information the user logs, I can then calculate sports science metrics, such as chronic load, training stress balance, among others. 
This would only be useful if the user could interpret that data, that is why I then generated synthethic data to train a Machine Learning model
to predict the likelihood of injury - presented as a percentage of healthiness (since showing 80% healthy is more pleasent than showing 20% injured). 
This model becomes a tool to an AI agent that can interact with the user, proposing different workouts, techniques and answering questions the user may have.
To prevent halucinations and bad information, the agent was fed some of the best books in the running space, with a RAG system. 

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
    |-ingest.py                -> takes the pdfs and creates one big file, to then save on     |                                    the vector database
    |-tools.py                 -> all the tools the AI needs to work
    |-advanced marathoning.pdf -> the book used to give context
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
  |-ml_features.py     -> uses features.py to compute the features for the ML model,         |                              accesses db
  |-cache.py           -> initiates the redis client
  |-database.py
  |-predict.py         -> Gets features, calls model and generates a prediction
  |-security.py        -> password hashing etc
  |-worker.py          -> handles background jobs (Arq)
  |-features.py        -> computes the rolling features for the athlete, fed into the ML                                 model

# Tech Stack

## Backend

Python
FastAPI
SQLAlchemy
Alembic
Arq

## Database

Supabase (PostgreSQL)
Redis

## Machine Learning

scikit-learn
pandas
NumPy

## AI

RAG
LLM API
Vector search

## Infrastructure

Docker
Git
  
  

