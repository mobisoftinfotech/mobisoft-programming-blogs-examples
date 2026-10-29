# Mobisoft Infotech AI Assistant

A website chat agent (a "digital twin" of Mobisoft Infotech) that answers visitor questions about the company's services, engagement models and contact details, and captures sales leads. It runs as a Gradio chat app on top of the OpenAI API.

## How it works

- **Knowledge base**: `knowledge_base/Mobisoft_Infotech_Services_Knowledge_Base.pdf` is parsed at startup and split into one section per service, plus Engagement Models and Contact Information. The company overview and contact details go into the system prompt.
- **Tools the agent can call**:
  - `get_service_details`: returns the full chapter for one service.
  - `search_knowledge_base`: BM25 keyword search across the whole knowledge base.
  - `record_user_details`: saves a lead (name, email, needs) to `logs/leads.md`.
  - `record_unknown_question`: logs questions the knowledge base can't answer to `logs/unknown_questions.jsonl`.
- **Guardrails**:
  - Input: messages over 2000 characters are rejected, and every message goes through OpenAI's moderation endpoint.
  - Output: a second LLM call (the evaluator) checks each reply against the knowledge retrieved that turn. A rejected reply is retried once with the evaluator's feedback; if the retry is also rejected, the visitor gets a fallback message pointing to the sales team.
- **Agent activity panel**: a live log next to the chat shows each step as it happens: moderation, tool calls and their results, the evaluator's verdict (and any rewrite), and the sales brief.
- **Sales brief**: when a lead is recorded, the agent writes a short brief for the sales team (who the visitor is, what they need, the best-fitting services with their official links, and questions to ask on the first call). It saves the brief to `logs/briefs.md` and pushes it to the sales team's phones with [Pushover](https://pushover.net). The model only picks the services; their names and links come from the knowledge base, so the links can't be made up.

All the code is in `main.py`.

## Prerequisites

- Python 3.12 (3.10+ should work)
- An OpenAI API key with access to the configured models

## Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API key
cp .env.example .env
# then edit .env and set OPENAI_API_KEY
```

### Environment variables

| Variable          | Required | Default        | Purpose                                   |
|-------------------|----------|----------------|-------------------------------------------|
| `OPENAI_API_KEY`  | Yes      | —              | OpenAI API key                            |
| `MODEL_NAME`      | No       | `gpt-5.4-mini` | Model that chats with visitors            |
| `EVALUATOR_MODEL` | No       | `MODEL_NAME`   | Model that reviews replies before sending |
| `PUSHOVER_USER`   | No       | —              | Pushover user key that receives sales briefs |
| `PUSHOVER_TOKEN`  | No       | —              | Pushover application API token            |

Without the Pushover variables, briefs are still written to `logs/briefs.md`.

## Run the agent

```bash
python main.py
```

Gradio starts a local server (by default at http://127.0.0.1:7860) and opens it in your browser. Pick one of the example questions or type your own, and watch the Agent activity panel on the right.

The terminal shows what the agent is doing: tool calls, new leads, unanswered questions, and replies rejected by moderation or the evaluator.

## Output files

The agent writes these under `logs/` (the folder is created if it's missing):

- `logs/leads.md`: a Markdown table of captured leads (date, name, email, notes)
- `logs/unknown_questions.jsonl`: one JSON record per question the agent couldn't answer
- `logs/briefs.md`: the sales brief written for each captured lead

These files hold visitor personal data, so don't commit or share them.

## Configuration

These limits are constants near the top of the "Chat app" section in `main.py`:

- `MAX_TOOL_ROUNDS = 6`: the most tool-call rounds allowed per reply
- `MAX_INPUT_CHARS = 2000`: the longest visitor message accepted
- `MAX_HISTORY_MESSAGES = 20`: how many past messages are sent to the model
- `MAX_REPLY_TOKENS = 4000`: the most tokens a reply can use

To update the agent's knowledge, replace the PDF in `knowledge_base/`. The parser expects the same layout: `Service: <name> | Category: <category>` lines that start each service chapter, followed by "Engagement Models" and "Contact Information" sections.

## Project structure

```
.
├── main.py               # Agent: KB loading, tools, guardrails, Gradio app
├── requirements.txt      # Python dependencies
├── .env.example          # Template for environment variables
├── knowledge_base/       # Source PDF the agent answers from
└── logs/                 # Leads and unanswered questions (generated, not committed)
```

## License

MIT License

## Author

Created by Mobisoft Infotech Pvt Ltd
