META = {
    "id": "s48_deleted_router",
    "kicker": "Architecture",
    "outro": False,
    "yt_title": "We Deleted Our Router. The New Agent Lost. #Shorts",
    "description": "Old router (rules + classifier): 95.7% on 46 hard labels. New agent loop with a keyword-only offline model: 69.6%. Architecture alone is not a win. The model and the evals carry it.\n\nCode on my GitHub: https://github.com/your-name/your-course\nFull episode: Why We Deleted Our Router: How AI Assistant Architecture Evolves\n\n#AIAgents #LLM #AIEngineering #AIInterview",
    "source_episode": "Why We Deleted Our Router: How AI Assistant Architecture Evolves",
    "tags": ["delete LLM router", "AI agent architecture", "intent classifier", "agent loop", "LLM evaluation", "AI engineer interview", "AI engineering", "tool calling"],
}

BEATS = [
    {"headline": "We deleted our router.",
     "say": "We deleted the router from our AI assistant, and let the model pick tools itself. Cleaner design. Then we measured it.",
     "visual": {"type": "versus", "left": "ROUTER", "left_sub": "rules + classifier", "right": "AGENT", "right_sub": "model picks tools"}},
    {"headline": "The router scored 95.7%.",
     "say": "On forty six hard labels, the old router, rules plus a classifier, scored ninety five point seven percent.",
     "visual": {"type": "bignum", "num": "95.7%", "label": "old router, 46 hard labels"}},
    {"headline": "The agent scored 69.6%.",
     "say": "The new agent, with my keyword-only offline model, scored sixty nine point six. It lost by twenty six points.",
     "visual": {"type": "versus", "left": "95.7%", "left_sub": "old router", "right": "69.6%", "right_sub": "new agent, offline"}},
    {"headline": "Routing became model quality.",
     "say": "Why? In an agent loop, routing quality is model quality. A weak model routes badly.",
     "visual": {"type": "bignum", "num": "26", "label": "points lost with a weak model"}},
    {"headline": "Keep it as a baseline.",
     "say": "So keep what you delete as a measured baseline. Architecture alone is not a win. Code on GitHub: your-course.",
     "visual": {"type": "loop", "items": ["change", "measure", "keep baseline"]}},
]
