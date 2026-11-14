META = {
    "id": "short_example",
    "kicker": "MCP",
    "outro": False,
    "yt_title": "MCP vs Function Calling: What's the Difference? #Shorts",
    "description": "Function calling is how a model asks to use a tool. MCP is a standard way to package and share tools so any app can plug them in. They work together.\n\n#MCP #FunctionCalling #AIAgents #AIEngineering #ModelContextProtocol",
    "source_episode": "the full lesson",
    "tags": ["MCP vs function calling", "Model Context Protocol", "function calling", "tool calling", "MCP", "AI agents", "AI engineering", "AI engineer interview"],
}

BEATS = [
    {"headline": "Not the same thing.",
     "say": "MCP versus function calling. People mix them up, but they solve different problems.",
     "visual": {"type": "bignum", "num": "VS", "label": "two different problems"}},
    {"headline": "Function calling.",
     "say": "Function calling is how a model asks to use a tool. Your app defines the tool, and your app runs it.",
     "visual": {"type": "loop", "items": ["model asks", "app runs", "result back"]}},
    {"headline": "MCP.",
     "say": "MCP is a standard way to package tools, so any app can plug them in without custom glue code.",
     "visual": {"type": "versus", "left": "CUSTOM", "left_sub": "glue per app", "right": "MCP", "right_sub": "plug into any app"}},
    {"headline": "They work together.",
     "say": "They work together. MCP shares the tool. Function calling is how the model uses it.",
     "visual": {"type": "bignum", "num": "BOTH", "label": "share with MCP, call with functions"}},
]
