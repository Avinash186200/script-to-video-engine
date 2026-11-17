META = {
    "id": "arch_evolution",
    "day": "Special",
    "part": 1,
    "tag": "Architecture Special",
    "yt_title": "Why We Deleted Our Router: How AI Assistant Architecture Evolves",
    "description": """Most AI assistants go through the same eight stages: a regex router, an intent classifier, one agent loop with typed tools, a verifier so the model cannot invent numbers, pinned tool contracts, bounds measured from data, honest evals, and fail-closed config. This episode walks through all eight with real numbers from my own projects, including the one that surprised me: after we deleted the router, the new agent scored 69.6% against the old router's 95.7% on a weak offline model.

You will learn:
- Why keyword routers and classifiers break, and when they are still the right choice
- One agent loop with typed tools, and the honest cost of deleting the router
- A deterministic verifier: the model writes tokens, code renders the numbers
- Pinned tool contracts and version admission at start-up
- Step limits and token budgets measured from data, not guessed
- Honest evals: repeats, pass^3, a held-out split, an independent judge, evidence files
- Fail-closed configuration: unset means prod

Code (a 60-line verifier with tests), a cheat sheet and 14 interview questions are linked below. Tip: watch at 1.25x.""",
    "code": "arch_evolution",
    "tags": ["AI agent architecture", "LLM router", "intent classification", "AI agent loop", "tool calling",
             "LLM hallucination", "LLM evaluation", "AI engineering", "AI system design", "AI engineer interview"],
}

STEPS = [
    {"t": {"tpl": "title", "over": "Architecture Special", "title": "Why we deleted our router",
           "subtitle": "How AI assistant architecture evolves, in eight stages", "tip": "Tip: watch at 1.25x"},
     "say": "We deleted the router from our AI assistant. The new design was cleaner, easier to extend, and on paper, better. Then we measured it, and it lost. Today: the eight stages most AI assistants go through, why each one happens, what each one costs, and the number that taught me the biggest lesson.",
     "chapter_name": "Intro"},

    {"t": {"tpl": "table", "kicker": "The journey", "title": "Eight stages",
           "headers": ["Stages 1-4", "Stages 5-8"], "widths": [820, 820],
           "rows": [["1. Regex router", "5. Pinned tool contracts"], ["2. Intent classifier", "6. Bounds from data"],
                    ["3. One agent loop, typed tools", "7. Honest evals"], ["4. Verifier, code renders numbers", "8. Fail-closed config"]]},
     "say": "Here is the map. A regex router. An intent classifier. One agent loop with typed tools. A verifier, so code renders the numbers. Pinned tool contracts. Bounds from data. Honest evals. And fail-closed config. Every number in this video comes from my own projects. Many come from an offline scripted model, a fake model that lets tests run without an API key. I will label those, because they measure plumbing, not intelligence."},

    # Stage 1-2
    {"t": {"tpl": "section", "kicker": "Stages 1 and 2", "title": "Routers: rules, then a classifier"},
     "say": "Let's start where almost everyone starts.",
     "chapter_name": "Stages 1-2: Regex router and classifier"},
    {"t": {"tpl": "flow", "kicker": "Stage 1", "title": "A regex router",
           "boxes": [["Question", "free text", "panel"], ["Regex rules", "if 'forecast' in q", "gold"],
                     ["One tool", "chosen by code", "accent"], ["LLM", "writes the sentence", "green"]],
           "note": "Fast, cheap, predictable. Only knows the phrasings you thought of."},
     "say": "Stage one. You have four tools and a deadline. So you write rules: if the question says forecast, call the forecast tool. The LLM only writes the final sentence. It is fast, cheap and predictable. But it only knows the phrasings you thought of. In my project, rules alone got eighty four point eight percent of hard labels right, and only fifty seven percent of document questions, because people ask for documents in many ways."},
    {"t": {"tpl": "bars", "kicker": "Stage 2", "title": "Add a classifier behind the rules",
           "items": [["Rules + classifier", 0.957], ["Rules only", 0.848]],
           "note": "46 hard router labels. Document recall: 57% to 86%."},
     "say": "Stage two. Rules miss paraphrases, so you put a small classifier behind them. Rules fire first, the classifier catches what they miss. It works. On my forty six hard labels, accuracy went from eighty four point eight to ninety five point seven percent. Document recall went from fifty seven to eighty six."},
    {"t": {"tpl": "callout", "kicker": "Routing between models", "title": "Cheaper, faster, with an error rate",
           "text": "28% cheaper. p50 4.80 s to 2.62 s.", "sub": "But 15% of queries went to a model that was too small.", "color": "gold"},
     "say": "Routers are not only for tools. In a separate serving benchmark, I routed between a small and a large model with rules plus a classifier. Twenty eight percent cheaper than always using the large model. Median latency from four point eight seconds to two point six. But fifteen percent of queries landed on a model that was too small. Every router has an error rate. You have to measure it."},

    # Stage 3
    {"t": {"tpl": "section", "kicker": "Stage 3", "title": "One agent loop, typed tools"},
     "say": "So why delete something that scores ninety five percent?",
     "chapter_name": "Stage 3: Deleting the router"},
    {"t": {"tpl": "bullets", "kicker": "The problem", "title": "Two brains",
           "items": ["The router decides before the model sees the question",
                     "A wrong route is silent: the model cannot fix it",
                     "Every new tool: new rules and new training data"]},
     "say": "Because it is a second brain. The router decides before the model ever sees the question. When the router is wrong, it is silent: the model gets the wrong tool and has no chance to fix it. And every new tool means new rules and new training data."},
    {"t": {"tpl": "flow", "kicker": "The change", "title": "The model sees the whole catalog",
           "boxes": [["Question", "", "panel"], ["LLM", "full typed catalog", "gold"],
                     ["Tools", "run by code", "accent"], ["Answer", "checked by code", "green"]],
           "note": "A CI check fails if the agent code imports regex."},
     "say": "So we took the router off the request path. The model gets the full catalog, including document search and a way to decline, with typed parameters and clear descriptions. Code only runs tools, checks and renders. And a CI check fails the build if anyone imports regex in the agent code, so the keyword router cannot creep back in."},
    {"t": {"tpl": "bars", "kicker": "Then we measured it", "title": "The agent lost",
           "items": [["Old router: rules + classifier", 0.957], ["New agent, offline keyword model", 0.696]],
           "note": "Same 46 labels. On the 30-question end-to-end set, both scored 30/30 offline."},
     "say": "Then we measured it. Same forty six labels. Old router, ninety five point seven. New agent, driven by my keyword-only offline model, sixty nine point six. On the easier thirty-question end-to-end set, both scored thirty out of thirty. But on the hard labels, the new architecture lost by twenty six points."},
    {"t": {"tpl": "callout", "kicker": "The biggest lesson", "title": "Architecture alone is not a win",
           "text": "The model and the evals carry it", "sub": "Keep what you delete as a measured baseline.", "color": "red"},
     "say": "That is the biggest lesson in this video. Architecture alone is not a win. In an agent loop, routing quality is model quality. With a weak model, the old router is better. So I did not delete the router. I moved it into the evals as a baseline, and its score sits right next to the agent's in every report. If a real model does not beat ninety five point seven, the router comes back."},

    # Stage 4
    {"t": {"tpl": "section", "kicker": "Stage 4", "title": "The model never types a number"},
     "say": "Next problem: invented numbers.",
     "chapter_name": "Stage 4: Verifier and code-rendered numbers"},
    {"t": {"tpl": "twocol", "kicker": "Prompt vs code", "title": "A wish vs a rule",
           "left": {"head": "Before", "items": ["Prompt: 'only use tool numbers'", "Model picks rounding and units", "Nothing enforces it"]},
           "right": {"head": "After", "items": ["Answer is a submit_answer tool call", "Numbers are tokens: c1.n4", "Verifier checks, code renders"]}},
     "say": "The prompt said: only use numbers from tools. That is a wish, not a rule. So two changes. First, the final answer is a tool call, submit answer, with a schema, not free prose. Second, the model never types digits. Every number in a tool result gets a token, like c one dot n four, and the answer uses tokens."},
    {"t": {"tpl": "code", "kicker": "python arch_evolution/verifier_demo.py", "title": "A made-up number is rejected", "file": "output",
           "code": """grounded : {'status': 'ok', 'text': 'Expected return is
            0.99 (predicted_return_pct), volatility
            12.40 (volatility_pct).'}
made up  : {'status': 'repair', 'errors': ['DIGIT_IN_TEXT']}
bad token: {'status': 'repair', 'errors': ['UNKNOWN_TOKEN:c2.n0']}""",
           "hl": [4, 5]},
     "say": "Here is the sixty-line demo in the repo. A grounded answer uses tokens, and code prints the real values with labels. If the model types one point five percent by itself, the verifier rejects it: digit in text. If it uses a token no tool produced, rejected. These are set lookups: exact, cheap, and one test per rule. After two failed repairs, the turn ends as incomplete. The user never sees an unchecked answer."},
    {"t": {"tpl": "bullets", "kicker": "Honest limit", "title": "A floor, not a ceiling",
           "items": ["Proves where each number came from", "Does not prove the answer is relevant",
                     "Answers read like reports", "A weak model burns repairs"]},
     "say": "The honest limit. This is a floor. It proves where every number came from. It does not prove the answer is relevant or well argued. Answers read more like a report than a chat. And a weak model will burn repairs learning the token syntax."},

    # Stage 5-6
    {"t": {"tpl": "section", "kicker": "Stages 5 and 6", "title": "Contracts and bounds"},
     "say": "Now, protecting everything around the model.",
     "chapter_name": "Stages 5-6: Contracts and bounds from data"},
    {"t": {"tpl": "steps", "kicker": "Stage 5", "title": "Pin the tool contract",
           "items": ["Snapshot every tool schema + hash in git",
                     "CI regenerates it and fails on any diff",
                     "Start-up admits each package by version",
                     "Mismatch: tool unavailable, typed reason, readiness 503"]},
     "say": "Stage five. A package renames a field, and every user gets the new shape with no warning. So commit a snapshot of every tool schema with a hash. CI fails on any diff. At start-up, each package is admitted by version: in dev, the pinned version or a pre-release of it, in staging and prod, the exact version. A package that fails is marked unavailable with a typed reason, the other tools keep working, and readiness returns five oh three."},
    {"t": {"tpl": "table", "kicker": "Stage 6", "title": "Bounds measured, not guessed",
           "headers": ["", "Measured max", "Shipped default"], "widths": [560, 540, 540],
           "rows": [["Model calls per turn", "3", "5"], ["Tool calls per step", "1", "2"], ["Tokens per turn", "~4,500", "14,000"]]},
     "say": "Stage six. Our step limit was six, picked by feel, and retries were hidden inside the HTTP adapter. Now every bound is a setting, and a ledger counts every model call, retry, tool call and token. I ran thirty eight offline scenarios with loose bounds and applied a written rule: two times the largest call counts, plus two, and three times the tokens. Max seen: three model calls, about four thousand five hundred tokens. Shipped: five calls and fourteen thousand tokens. Honest limit: a scripted model is efficient. A real model explores more, so you re-derive per model."},

    # Stage 7-8
    {"t": {"tpl": "section", "kicker": "Stages 7 and 8", "title": "Honest evals, fail-closed config"},
     "say": "Last two stages. These are the ones that keep you honest.",
     "chapter_name": "Stages 7-8: Honest evals and fail-closed config"},
    {"t": {"tpl": "bullets", "kicker": "Stage 7", "title": "Evals you can trust",
           "items": ["3 repeats; gate on pass^3, list flaky ids",
                     "Hash split: 18 dev, 12 held out",
                     "Judge must be a different model; advisory only",
                     "Evidence file: commit, models, clock, hashes, every result"]},
     "say": "Stage seven. One pass per question hides flakiness. So run each question three times and gate on pass to the power three: a question counts only if all three runs pass. A fixed hash puts twelve of thirty questions in a held-out split. Tune on the other eighteen. An optional LLM judge refuses to start if it is the same model as the one under test, and it never decides CI. And every run writes an evidence file, so a claim points to a run. Honest limit: offline, the model is deterministic, so all of this shows thirty out of thirty. It earns its keep with a live model."},
    {"t": {"tpl": "callout", "kicker": "Stage 8", "title": "Fail closed",
           "text": "Unset means prod", "sub": "One policy table. Every broken rule reported before start-up.", "color": "green"},
     "say": "Stage eight. Any mix of settings used to start the server, so a forgotten variable could turn on a test model in production. Now one setting says dev, staging or prod. Anything else stops the server, and unset means prod, the strictest row. One policy table, checked before start-up, reports every broken rule at once. A mistake can only make the system stricter."},
    {"t": {"tpl": "quiz", "q": "Your new agent scores lower than the old router. Ship it or not?",
           "answer": "Not yet. Keep the router as a baseline, test a real model on the held-out split with repeats, and ship only if it wins."},
     "say": "Quick check. Pause and answer. Your new agent scores lower than the old router. Do you ship it? Not yet. Keep the router as a baseline. Run a real model on the held-out split with repeats. Ship the agent only if it wins, and keep the number in the report either way."},

    {"t": {"tpl": "twocol", "kicker": "Starting tomorrow?", "title": "Which stage first",
           "left": {"head": "Day one", "items": ["Agent loop + typed tools", "An eval set with a held-out split", "Fail-closed config"]},
           "right": {"head": "When someone depends on it", "items": ["Verifier for numbers", "Pinned contracts", "Bounds from measured runs"]}},
     "say": "So if you start a new assistant tomorrow, where do you start? Not at stage one, and not at stage eight. On day one, I build the agent loop with typed tools, an eval set with a held-out split, and fail-closed config, because all three are cheap. The verifier, pinned contracts and measured bounds come the day someone depends on the numbers. And one exception: if your model is small and your intents are few and stable, measure a simple router first. It might win. Each stage is a response to a real failure. Add it when the failure shows up, and prove it helped with an eval."},

    {"t": {"tpl": "recap", "items": ["Routers are fast; they fail silently",
                                      "One agent loop: routing becomes model quality",
                                      "Model writes tokens; code checks and renders numbers",
                                      "Pin contracts; measure bounds",
                                      "Repeats, held-out split, evidence; unset means prod"],
           "next": "open the cheat sheet and the interview questions"},
     "say": "Let's recap. Routers are fast and cheap, but they fail silently. One agent loop fixes that, and makes routing your model's problem. The model writes tokens, and code checks and renders the numbers. Pin your contracts and measure your bounds. Run evals with repeats, a held-out split and evidence files, and treat unset as prod. And remember the number: sixty nine point six against ninety five point seven. Architecture alone is not a win.",
     "chapter_name": "Recap"},
    {"t": {"tpl": "end"},
     "say": "The verifier demo, a one-page cheat sheet, and fourteen interview questions with answers are linked in the description. If this helped, subscribe, and share it with someone building their first AI assistant."},
]
