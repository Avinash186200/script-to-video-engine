META = {
    "id": "s50_step_limit_from_data",
    "kicker": "Agents",
    "outro": False,
    "yt_title": "How Many Steps Should Your AI Agent Get? Measure It #Shorts",
    "description": "Our step limit was 6, picked by feel. We measured 38 offline runs: max 3 model calls and about 4,500 tokens. Rule: 2x the largest call counts, plus 2, and 3x tokens. Shipped 5 model calls and 14,000 tokens. Re-derive when the model changes.\n\nCode on my GitHub: https://github.com/your-name/your-course\nFull episode: Why We Deleted Our Router: How AI Assistant Architecture Evolves\n\n#AIAgents #LLM #AIEngineering #AIInterview",
    "source_episode": "Why We Deleted Our Router: How AI Assistant Architecture Evolves",
    "tags": ["AI agent step limit", "agent token budget", "LLM cost control", "agent loop", "AI agent design", "AI engineer interview", "AI engineering", "LLMOps"],
}

BEATS = [
    {"headline": "How many steps for an agent?",
     "say": "Interview question. How many steps should your AI agent get? Ours was six. Picked by feel.",
     "visual": {"type": "bignum", "num": "6", "label": "steps, picked by feel"}},
    {"headline": "Count everything.",
     "say": "So we made every bound a setting, and a ledger counted every model call, retry, tool call and token.",
     "visual": {"type": "loop", "items": ["model calls", "retries", "tokens"]}},
    {"headline": "Measure 38 runs.",
     "say": "Across thirty eight offline runs, the max was three model calls and about four thousand five hundred tokens.",
     "visual": {"type": "versus", "left": "3", "left_sub": "model calls, max", "right": "~4,500", "right_sub": "tokens, max"}},
    {"headline": "Apply a written rule.",
     "say": "Rule: two times the largest call counts, plus two, and three times the tokens. Shipped: five calls, fourteen thousand tokens.",
     "visual": {"type": "versus", "left": "5", "left_sub": "model calls", "right": "14,000", "right_sub": "tokens"}},
    {"headline": "Re-derive per model.",
     "say": "Honest limit: a scripted model is efficient. A real model explores more, so re-measure. Code on GitHub: your-course.",
     "visual": {"type": "loop", "items": ["run evals", "measure", "set bounds"]}},
]
