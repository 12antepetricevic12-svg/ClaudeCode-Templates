# n8n Workflow Debugging — Hard-Won Lessons

If your n8n workflow is misbehaving — especially with AI nodes — start here. These are real bugs I hit while building the Jelsa Nautica Speed-to-Lead workflow. Most of them look like *different* bugs at first but they're all about the same thing: **data not flowing where you think it's flowing**.

---

## Quick reference

| What you're seeing | Most likely cause | Section |
|---|---|---|
| AI returns the same useless answer every time (e.g. empty fields, default category) regardless of input | Expressions in the prompt aren't being evaluated — missing `=` prefix on the field | [Bug #1](#bug-1-the-prefix-bug-the-most-important-one) |
| AI errors with "Unexpected token 'I', \"I'm ready \"... is not valid JSON" | Same thing — AI received literal `{{ ... }}` placeholder text and hallucinated a chatty reply | [Bug #1](#bug-1-the-prefix-bug-the-most-important-one) |
| AI prompt sees `undefined` for some fields | Wrong case on field names (Gmail Trigger uses `From`, not `from`) | [Bug #2](#bug-2-case-sensitive-field-names) |
| "Model output doesn't fit required format" | Output Parser strict mode + Claude/Anthropic = unreliable; Output Parser's auto-fix needs its own LLM connection | [Bug #3](#bug-3-ai-agent--output-parser-failing-with-claude) |
| Workflow runs but always routes to the wrong branch | One of the above — your IF condition is reading from a field that's `undefined` because the upstream AI saw garbage | All three |

---

## Bug #1 — The `=` prefix bug (the most important one)

### Symptom

The AI behaves as if it received an empty or malformed prompt. Common shapes:

- **GPT-4o-mini with `responseFormat: json_object`**: returns the most generic possible JSON every time, regardless of input. We saw `{ "classification": "not_lead", "lead_name": "", "inquiry_summary": "" }` over and over for completely different incoming emails.
- **Claude / models without strict JSON mode**: returns conversational filler like *"I'm ready to help! Please provide the email content."* or *"Sure! Here's the JSON: ..."*. If a downstream `JSON.parse()` is waiting for that, it fails with `Unexpected token 'I', "I'm ready "... is not valid JSON`.
- The AI's response is **identical or near-identical across multiple different runs**. That's the giveaway.

### Diagnosis

Pull the Gmail Trigger output for one of the failed executions. Confirm the trigger genuinely has the data — `From`, `Subject`, `snippet`, etc. are populated. Then look at the AI's raw output and ask: *"Could the AI have produced this if it actually saw the email?"* If the answer is no — the AI did **not** see what you think it saw.

### Root cause

In n8n, **a parameter value only gets treated as an expression if the entire string starts with `=`**.

This is a value with no `=` — n8n treats every character as literal text:

```
Read this email carefully.

From: {{ $('Gmail Trigger').item.json.From }}
Subject: {{ $('Gmail Trigger').item.json.Subject }}
```

This is a value with `=` — n8n evaluates the `{{ ... }}` parts:

```
=Read this email carefully.

From: {{ $('Gmail Trigger').item.json.From }}
Subject: {{ $('Gmail Trigger').item.json.Subject }}
```

Without the `=`, the AI literally gets the string `{{ $('Gmail Trigger').item.json.From }}` in its prompt — gibberish. With strict JSON mode on, the model still has to return JSON, so it returns the safest default (empty fields, `not_lead`, etc.) — same answer every time. Without strict JSON mode, the model gets confused and writes conversational text, which then crashes the downstream `JSON.parse`.

### Fix

Open the AI/LLM node, find the prompt field. **The first character must be `=`.**

In the n8n UI, you can toggle "Expression mode" on a field — that adds the `=` for you. If you see `{{ ... }}` rendered as plain text in the field (no syntax highlighting, no resolved values shown below), you're in **fixed-string** mode and expressions are NOT being evaluated. Click the gear icon → switch to expression mode.

If you're updating the workflow via the n8n MCP API or the JSON editor, your value strings need to look like `"=...{{ ... }}..."` exactly.

### Why this is so easy to miss

- The field looks normal in the UI. The expressions even highlight in syntax color in some places.
- Other nodes in the same workflow may have correct `=` prefixes (because n8n auto-adds it when you drag-drop a field), so the workflow seems to mostly work.
- The AI's output looks plausible — *"not_lead"* with empty fields could be a legitimate classification of a weird email. You won't realize it's a bug until you see the same output across radically different inputs.

### Rule of thumb

**Whenever an AI node returns suspiciously consistent output across runs, the prompt is broken — not the AI.** Always check the `=` prefix first.

---

## Bug #2 — Case-sensitive field names

### Symptom

Some expressions resolve correctly, others come up `undefined`. The AI gets a partial prompt with some `undefined` values mixed in.

### Diagnosis

Pull the upstream node's output (e.g. Gmail Trigger) and **look at the actual JSON keys**. n8n's Gmail Trigger in `simple: true` mode returns keys with email-header capitalization:

```json
{
  "id": "19dd...",
  "threadId": "19dd...",
  "snippet": "Hi, I want to rent a boat...",
  "From": "ante <ante@example.com>",     <-- capital F
  "Subject": "rent a boat",              <-- capital S
  "To": "blaholdings@gmail.com"          <-- capital T
}
```

`$json.from` and `$json.subject` (lowercase) → `undefined`. You need `$json.From` and `$json.Subject` (capital).

### Fix

Match the case exactly. JS object property access is case-sensitive — `obj.From` and `obj.from` are different keys.

### Prevention tip

When you first wire up a new node, **click the upstream node and look at the actual output JSON in the panel on the right** before writing expressions. Don't assume field names from documentation or memory — read what's actually there.

---

## Bug #3 — AI Agent + Output Parser failing with Claude

### Symptom

You get an error like:

```
Problem in node 'Classify Email'
Model output doesn't fit required format
```

…even though the AI's underlying response *looks* like reasonable JSON.

### Root cause

n8n's **AI Agent** node (v3.1) uses LangChain's "Tools Agent" mode under the hood. It tells the LLM *"don't reply directly — call this `format_response` tool with structured arguments."* OpenAI's GPT models do this reliably; Claude (Anthropic) via OpenRouter often **ignores the tool and just writes the JSON in the message body as plain text**. The Structured Output Parser then can't read it because it was looking for tool-call format, not raw text.

A separate sub-issue: if you turn on **Auto-Fix Format** on the parser, the parser tries to call *another* LLM to fix bad output. That requires a language model sub-node connected to the parser itself — without one, you get a separate failure.

### Fix options

| Option | When to use |
|---|---|
| **Switch from AI Agent to Basic LLM Chain** *(simplest)* | Almost always. Basic LLM Chain doesn't use tool-calling — it just sends the prompt and parses the response. Works reliably with Claude. Same sub-node connections (`ai_languageModel`, `ai_outputParser`). |
| **Keep AI Agent, switch model to GPT-4o-mini** | If you need agent-like tool use elsewhere in the same node. |
| **Drop the Output Parser entirely + use `responseFormat: json_object` on the chat model + parse JSON manually in expressions** | If you want minimum nodes. Works great with OpenAI models. Anthropic via OpenRouter treats `responseFormat` as a soft hint — less reliable. |

### Why "AI Agent" sounds right but isn't always what you want

- **AI Agent** is for agents that take actions: search the web, send emails, query a DB, use tools.
- **Basic LLM Chain** is for "send a prompt, get a response back."
- For pure classification or text generation, you almost always want Basic LLM Chain. The name "AI Agent" is more impressive but the simpler node is the right tool.

---

## Bonus: `responseFormat: json_object` on OpenRouter Chat Model

This is a useful option but has subtle behavior:

- **Strictly enforced by OpenAI models** (`openai/gpt-4o-mini`, `openai/gpt-4-turbo`, etc.). The API will not return non-JSON.
- **Treated as a soft hint by Anthropic models** through OpenRouter. Claude will *try* to return JSON but may add prose. If you need guaranteed JSON, use a GPT model OR drop `responseFormat` and parse defensively.
- **The word "json" must appear in the prompt** when `responseFormat: json_object` is on. The OpenRouter node enforces this.

**Useful side effect:** when `responseFormat: json_object` is set on the chat model attached to a Basic LLM Chain, n8n auto-parses the JSON. Downstream nodes get the parsed object directly at the top level (e.g. `$json.classification`), **not** wrapped under `$json.text`. So:

- Without `responseFormat`: `$json.text` is the AI's response string.
- With `responseFormat: json_object`: `$json.classification`, `$json.lead_name`, etc. are direct properties.

This caught me out — I had downstream `IF` nodes doing `JSON.parse($json.text).classification` when the value was already at `$json.classification`. The `JSON.parse(undefined)` failed silently and the IF defaulted to false.

---

## General debugging methodology for n8n + AI

When an n8n workflow with an AI node misbehaves, work through these in order:

1. **Pull the actual execution log** (in n8n UI: click an execution; via MCP: `n8n_executions` with `mode=full`). Don't guess — see what each node received and emitted.
2. **Check the AI's raw output**. Is it what you'd expect given the input? If not, the AI saw different input than you think.
3. **Look at the upstream node's output JSON**. Are the field names exactly what your expressions reference? Case sensitivity matters.
4. **Verify every prompt field has the `=` prefix**. This is the #1 silent killer.
5. **If the AI's output is identical across radically different inputs**, the prompt isn't being substituted — go back to step 4.
6. **If you're using AI Agent + Output Parser + a non-OpenAI model**, switch to Basic LLM Chain or to a GPT model.
7. **Check downstream expressions for `JSON.parse($json.text)`** when the upstream AI has `responseFormat: json_object` set — if it does, drop the `JSON.parse` and the `.text`, and use `$json.fieldName` directly.
8. **`itemsInput: 0` on an AI node is NOT a reliable signal of empty input** — the metric counts something else for AI nodes. Don't chase it. Trust the actual JSON output instead.

---

## The meta-lesson

Almost every "the AI is broken" or "the AI is being stupid" complaint with n8n turns out to be **a data-flow bug, not an AI bug**. The model is doing exactly what it was told — your job is to verify that what it was told is what you intended to say. Always trace the data backwards from the misbehaving node before blaming the AI.
