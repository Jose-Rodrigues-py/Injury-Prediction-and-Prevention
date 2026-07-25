"""
main loop for the agent
"""
from ollama import AsyncClient
from AI.rag import search
from AI.tools import access_db, make_prediction, get_message_history, save_message

client = AsyncClient()

SYSTEM_PROMPT = """
You are a running personal coach, whose main objective is to increase athlete's performance by preventing them from getting injured
You give tips on strength exercises they should be doing, changes to their workouts, and how to structure their training.
If asked, you can generate personalized plans to meet the user's goals. 

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
    prediction = await make_prediction(user_id)

    if message is None:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"User profile:\n{context}"},
            {"role": "system", "content": f"Prediction:\n{prediction}"},*history,
        ]
        response = await client.chat(
                model='qwen2.5:3b',
                messages= messages,
                tools = [search]
        )
        await save_message(user_id, "assistant", response.message.content)
        return response
    else: 
        await save_message(user_id, "user", message)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"User profile:\n{context}"},
            {"role": "system", "content": f"Prediction:\n{prediction}"},*history,
            {"role": "user", "content": message}
        ]

        response = await client.chat(
                        model='qwen2.5:3b',
                        messages= messages,
                        tools = [search] 
                )
        
        await save_message(user_id, "assistant", response.message.content)
        return response