# Status: On going

# Origin

After getting injured from running, I understood how important it is to be cautious with my training and dedicate time to prevent injuries. 
In this light, I came up with this idea. 
It is a simple tracking tool, in which I can log some health metrics (weight, VO2 Max, etc); my workouts and future races.
From the information the user logs, I can then calculate sports science metrics, such as chronic load, training stress balance, among others. 
This would only be useful if the user could interpret that data, that is why I then generated synthethic data to train a Machine Learning model
to predict the likelihood of injury - presented as a percentage of healthiness (since showing 80% healthy is more pleasent than showing 20% injured). 
This model becomes a tool to an AI agent that can interact with the user, proposing different workouts, techniques and answering questions the user may have.
To prevent halucinations and bad information, the agent was fed some of the best books in the running space, with a RAG system. 

# Project Structure
SummerProject/
|
|- AI/
    |-agent.py
    |-rag.py
    |-tools.py 
|-ML/
    |-gen_data.py
    |-train.py
    |-synthetic_data.csv
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
  |-models.py
  |-ml_features.py
  |-cache.py
  |-database.py
  |-predict.py
  |-security.py
  |-worker.py

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
  
  

