META = {
    "id": "s49_model_never_types_numbers",
    "kicker": "Hallucination",
    "outro": False,
    "yt_title": "Stop LLMs Inventing Numbers: Let Code Write Them #Shorts",
    "description": "The prompt said only use tool numbers. Nothing enforced it. Fix: the model writes tokens like c1.n4, a verifier checks them with set lookups, and code renders the real values. After two failed repairs the turn ends incomplete. A 60-line demo with tests is in the repo.\n\nCode on my GitHub: https://github.com/your-name/your-course\nFull episode: Why We Deleted Our Router: How AI Assistant Architecture Evolves\n\n#LLM #Hallucination #AIEngineering #AIInterview",
    "source_episode": "Why We Deleted Our Router: How AI Assistant Architecture Evolves",
    "tags": ["LLM hallucination numbers", "stop LLM hallucination", "grounded answers", "answer verification", "tool calling", "AI engineer interview", "AI engineering", "structured output"],
}

BEATS = [
    {"headline": "How do you stop invented numbers?",
     "say": "Interview question. How do you stop an LLM inventing numbers? The common answer: tell it in the prompt. That is a wish.",
     "visual": {"type": "versus", "left": "PROMPT", "left_sub": "a wish", "right": "CODE", "right_sub": "a rule"}},
    {"headline": "The model never types digits.",
     "say": "Better: the model never types digits. Every number in a tool result gets a token, like c one dot n four.",
     "visual": {"type": "bignum", "num": "c1.n4", "label": "a token, not a number"}},
    {"headline": "A verifier checks tokens.",
     "say": "A verifier checks with set lookups. A digit in the text? Rejected. A token no tool produced? Rejected.",
     "visual": {"type": "versus", "left": "1.5%", "left_sub": "typed: rejected", "right": "{c1.n0}", "right_sub": "token: accepted"}},
    {"headline": "Code renders the value.",
     "say": "Then code prints the real value, with its label and unit. After two failed repairs, the turn ends incomplete.",
     "visual": {"type": "bignum", "num": "2", "label": "repairs, then incomplete"}},
    {"headline": "Honest limit.",
     "say": "Honest limit: it proves where a number came from, not that the answer is relevant. Code on GitHub: your-course.",
     "visual": {"type": "loop", "items": ["tokenize", "verify", "render"]}},
]
