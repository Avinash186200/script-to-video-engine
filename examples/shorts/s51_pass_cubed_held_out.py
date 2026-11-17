META = {
    "id": "s51_pass_cubed_held_out",
    "kicker": "Evals",
    "outro": False,
    "yt_title": "One Eval Pass Is a Demo: pass^3 and a Held-Out Split #Shorts",
    "description": "Run each question 3 times and gate on pass^3: a question counts only if every run passes. A fixed hash puts 12 of 30 questions in a held-out split. The judge must be a different model and is advisory only. Every run writes an evidence file.\n\nCode on my GitHub: https://github.com/your-name/your-course\nFull episode: Why We Deleted Our Router: How AI Assistant Architecture Evolves\n\n#LLMEvaluation #AIAgents #AIEngineering #AIInterview",
    "source_episode": "Why We Deleted Our Router: How AI Assistant Architecture Evolves",
    "tags": ["LLM evaluation", "pass at k", "held out test set", "LLM as a judge", "AI agent evals", "AI engineer interview", "AI engineering", "eval flakiness"],
}

BEATS = [
    {"headline": "How do you evaluate an agent?",
     "say": "Interview question. How do you evaluate an AI agent honestly? Common answer: run the test set once. That hides flakiness.",
     "visual": {"type": "bignum", "num": "1", "label": "pass hides flakiness"}},
    {"headline": "Three repeats, gate on pass^3.",
     "say": "Run each question three times. Gate on pass to the power three: a question counts only if all three runs pass.",
     "visual": {"type": "bignum", "num": "3/3", "label": "runs must pass"}},
    {"headline": "Hold some questions out.",
     "say": "A fixed hash puts twelve of thirty questions in a held-out split. Tune on eighteen, check the other twelve.",
     "visual": {"type": "versus", "left": "18", "left_sub": "dev", "right": "12", "right_sub": "held out"}},
    {"headline": "A judge that is not the model.",
     "say": "An LLM judge must be a different model from the one under test, and it never decides CI. Every run writes an evidence file.",
     "visual": {"type": "versus", "left": "MODEL", "left_sub": "under test", "right": "JUDGE", "right_sub": "different, advisory"}},
    {"headline": "Honest limit.",
     "say": "Offline, my model is deterministic, so it shows thirty of thirty. This pays off with a live model. Code on GitHub: your-course.",
     "visual": {"type": "loop", "items": ["repeat", "hold out", "keep evidence"]}},
]
