META = {
    "id": "s52_unset_means_prod",
    "kicker": "Production",
    "outro": False,
    "yt_title": "Fail Closed: Unset Means Prod #Shorts",
    "description": "Any mix of settings used to start the server, so a forgotten variable could switch on a test model in production. Fix: one environment setting, unset means prod, and one policy table checked before start-up that reports every broken rule at once. A mistake can only make the system stricter.\n\nCode on my GitHub: https://github.com/your-name/your-course\nFull episode: Why We Deleted Our Router: How AI Assistant Architecture Evolves\n\n#LLMOps #AIEngineering #DevOps #AIInterview",
    "source_episode": "Why We Deleted Our Router: How AI Assistant Architecture Evolves",
    "tags": ["fail closed configuration", "production config", "environment variables", "LLMOps", "AI deployment", "AI engineer interview", "AI engineering", "secure defaults"],
}

BEATS = [
    {"headline": "A forgotten variable.",
     "say": "A forgotten environment variable can switch on a test model, or a fake clock, in production. Ours could.",
     "visual": {"type": "versus", "left": "TEST", "left_sub": "model", "right": "PROD", "right_sub": "by accident"}},
    {"headline": "One setting: dev, staging, prod.",
     "say": "The fix: one setting says dev, staging or prod. Any other value stops the server.",
     "visual": {"type": "loop", "items": ["dev", "staging", "prod"]}},
    {"headline": "Unset means prod.",
     "say": "And if it is unset, treat it as prod, the strictest row.",
     "visual": {"type": "bignum", "num": "unset", "label": "= prod"}},
    {"headline": "One policy table.",
     "say": "One policy table says what each environment allows: test model, pinned clock, exact versions. It reports every broken rule before start-up.",
     "visual": {"type": "gauge", "value": 0.9, "lo": "LOOSE", "hi": "STRICT", "label": "DEFAULT"}},
    {"headline": "Mistakes make it stricter.",
     "say": "Now a mistake can only make the system stricter. The cost: one explicit line on your laptop. Code on GitHub: your-course.",
     "visual": {"type": "bignum", "num": "1", "label": "line on your laptop"}},
]
