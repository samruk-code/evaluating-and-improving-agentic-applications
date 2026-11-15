"""Run the lab's 15 test queries through ask_agent, one at a time."""
import asyncio
import time

from app import ask_agent

QUERIES = [
    "What colors does the Classic Tee come in?",
    "How much is the Wool Beanie?",
    "Do you sell raincoats?",
    "Can I get the Classic Tee in medium, and what's your return policy?",
    "What's the cheapest pair of shoes you have, and do they come in size 12?",
    "I need a winter outfit — sweater, pants, and a beanie. What do you recommend?",
    "What's a good gift idea for someone who works from home?",
    "What's a good gift idea for someone who works from home?",
    "What's a good gift idea for someone who works from home?",
    "Tell me about all the shoes you have.",
    "What kind of stuff do you sell?",
    "How should I care for the merino wool sweater?",
    "Where's my order #4521?",
    "What's your phone number for customer service?",
    "yo u got those blue shirts lol",
]


async def main():
    n = len(QUERIES)
    start = time.monotonic()
    for i, query in enumerate(QUERIES, 1):
        print(f"Query {i}/{n}: {query}", flush=True)
        answer = await ask_agent(query)
        first_line = answer.strip().splitlines()[0] if answer.strip() else "(no answer)"
        print(f"A: {first_line}\n", flush=True)
    elapsed_min = (time.monotonic() - start) / 60
    print(f"Done. {n} queries in {elapsed_min:.1f} minutes.", flush=True)
    print(f"Expect {n} new traces in Phoenix.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
