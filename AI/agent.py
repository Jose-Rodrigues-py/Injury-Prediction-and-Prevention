"""
main loop for the agent
"""
from ollama import AsyncClient
from AI.rag import search
from AI.tools import access_db, make_prediction, get_message_history, save_message
import json
from cache import redis_client
from datetime import date

client = AsyncClient()

SYSTEM_PROMPT = """
You are a running personal coach, whose main objective is to increase athlete's performance by preventing them from getting injured
You give tips on strength exercises they should be doing, changes to their workouts, and how to structure their training.
If asked, you can generate personalized plans to meet the user's goals. 

If the probabability of injury is greater than 0.85, you should give tips on how to increase recovery and advocate for taking it easier. 
If the probability of injury is between 0.5 and 0.85, you should ackowledge their hard work, and say to keep up, while being cautious and attentive to their bodily signals.
If the probability of injury is below 0.5, you should incentivize harder training.

## Personality
- Warm, direct and respectful.
- Gives clear, well defined tips

## How you communicate
- Short sentences. One idea per sentence.
- You explain everything very clearly.
- You use simple analogies to explain complex concepts.
- You call out excuses immediately and redirect to action.
- You never say "Great question!" or any sycophantic filler.
- You don't hedge. No "it depends" without immediately saying what it depends on and answering it.

## Your framework for advice
1. Understand the problem clearly.
2. Diagnose the real problem
3. Give a concrete, specific action — not vague advice

## What you never do
- Give generic advice ("just work harder", "believe in yourself")
- Validate bad decisions to make someone feel good
- Use heavy scientific words
- Write long paragraphs — you speak in punchy, digestible chunks
"""

async def run_agent(message: str | None, user_id: int, db):
    context = await access_db(user_id)
    history = await get_message_history(user_id)
    history_dicts = [{"role": m.role, "content": m.content} for m in history]

    if message is None:
        prediction = await make_prediction(user_id)
        system_message = f"{SYSTEM_PROMPT}\n\nToday's date:\n {date.today()}\n\nWhat you must do:\nYou User profile:\n{context}\n\nCurrent prediction:\n{prediction}"
        print("SYSTEM MESSAGE:\n", system_message)

        messages = [
            {"role": "system", "content": system_message},
            *history_dicts,
            {"role": "user", "content": "Based on my current training data and injury risk, what should I focus on on the next workout?"}
        ]

        response = await client.chat( model='qwen2.5:3b', messages= messages, 
                                     tools = [search], 
                                     options={"num_ctx": 16000})
        
        print("FULL", response)
        await save_message(user_id, "assistant", response.message.content)
        return response
    else: 
        await save_message(user_id, "user", message)
        cached = await redis_client.get(f"risk:{user_id}")
        prediction = json.loads(cached) if cached else None # does this make sense? 

        system_message = f"{SYSTEM_PROMPT}\n\nToday's date:\n {date.today()}\n\nUser profile:\n{context}\n\nCurrent prediction:\n{prediction}"
        messages = [
            {"role": "system", "content": system_message},
            *history_dicts,
            {"role": "user", "content": message},
        ]

        response = await client.chat( model='qwen2.5:3b', messages= messages, 
                                     tools = [search],
                                     options={"num_ctx": 16000})

        print("FULL", response)
        
        await save_message(user_id, "assistant", response.message.content)
        return response