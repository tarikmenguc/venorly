# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## 5. Verifiable Execution (Run, Don't Guess)
**Test the reality, not your assumption of it.**
- LLMs hallucinate success. Don't assume code works just because it looks correct.
- If making complex logic changes, suggest intermediate print statements or logs to observe state.
- Make changes in small, executable increments rather than large monolithic blocks.

## 6. Systematic Debugging
**Don't guess the fix. Prove the bug.**
- When encountering an error, do not blindly alter the code.
- Analyze the stack trace. If the cause is invisible, add instrumentation (logging/prints) to expose it first before attempting a fix.
- Fix the root cause, not just the symptom.

## 7. Context Strictness (No Hallucinations)
**Stick to what exists. Don't invent APIs.**
- Use only the provided files, existing project dependencies, and standard libraries.
- Do not import random third-party packages unless explicitly requested.
- Before writing a new utility function, check if the codebase already has one that does the job.

## 8. Output Economy
**Respect token limits and developer time.**
- Do not output the entire file if you only changed a few lines.
- Provide targeted diffs or precise instructions on exactly where to replace/insert the code.
- Omit long-winded apologies or boilerplate explanations; keep responses strictly technical.

---

## Project: Venorly

B2B SaaS AI market research platform. LangGraph multi-node pipeline that takes a category string and produces a structured startup feasibility report.

**Entry point:** `api/main.py` (FastAPI) — pipeline triggered via POST `/scan`

**Language:** All user-facing prompts and report output are in Turkish (TÜRKÇE).

### Key Files

| File | Role |
|---|---|
| `agent/idea_agent.py` | Main 13-node LangGraph StateGraph + `AgentState` TypedDict |
| `agent/validator.py` | Graveyard check, market sizing, idea scorecard |
| `agent/auditor.py` | Hybrid Trust Index (0.4×S + 0.6×X), Tavily claim verification |
| `agent/competition_matrix.py` | Competitor feature matrix node |
| `lib/schemas.py` | `FeasibilityReport` Pydantic model — do not change field names without updating all consumers |
| `lib/llm.py` | `get_llm(provider, temp)` — Groq primary, Gemini fallback |
| `lib/tavily_client.py` | `get_tavily_client()` — wraps Tavily search |
| `lib/supabase_client.py` | `supabase` singleton — reports + audit_trail tables |
| `lib/source_routing.py` | `get_confidence(source_name)` — per-source trust scores |

### Node Order (linear, no branches)

```
expand_query → fetch_market_data → fetch_trending_models → match_to_market
→ scrape_competitor_reviews → cluster_complaints → find_store_app
→ scrape_store_reviews → cluster_store_problems → competition_matrix
→ generate_opportunity → validate_idea → auditor → END
```

### AgentState — key fields

```python
user_category: str       # raw user input
target_category: str     # refined by expand_query_node
trending_models: list    # from fetch_trending_models_node
report_json: dict        # FeasibilityReport as dict, built by generate_opportunity_node
final_report: str        # markdown string, assembled across nodes
```

### Installed libraries (requirements.txt)
langgraph, langchain-groq, langchain-google-genai, langchain-community,
tavily-python, supabase, fastapi, uvicorn, pydantic, pytrends,
beautifulsoup4, fpdf2, feedparser, python-dotenv, pyjwt, resend

### Trust Index formula
`confidence_index = 0.4 × S (source quality) + 0.6 × X (cross-validation)`
Bands: ≥0.75 green, ≥0.50 yellow, <0.50 red. Below 0.25 forces "Go"→"Hold".

---

## 9. Windows/CRLF Warning — CRITICAl

All `.py` files in this project use CRLF (`\r\n`) line endings (Windows).

**The Edit tool introduces null bytes when making multi-line edits on CRLF files.**

Rules:
- For **single short replacements** (1-2 lines, unique string): Edit tool is safe.
- For **multi-line or structural edits**: use a bash Python script instead:
  ```python
  content = subprocess.check_output(['git','show','HEAD:path/to/file']).decode('utf-8').replace('\r\n', '\n')
  content = content.replace(old, new)
  ast.parse(content)  # always validate before writing
  with open(path, 'w', encoding='utf-8', newline='\n') as f:
      f.write(content)
  ```
- Always run `ast.parse()` + null byte check before writing any modified file.
- Always get the original from `git show HEAD:...` — never trust a previously edited in-memory copy.