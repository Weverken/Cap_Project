# CookMate

The virtual recipe book that turns into your sous chef.

## Overview

Most recipe apps are just a place to store text. CookMate is built around the idea that a cooking assistant should be able to act on what you're cooking, not just answer generic questions about it. You can chat with it while you cook and it will actually scale a recipe, convert a measurement, look up a substitution, or tell you what to make with what's in your fridge, because it has real tools wired into your actual saved recipes and database, not just a general knowledge base.

It's built for anyone who cooks from recipes they've collected, especially the kind of person with a shoebox of handwritten recipe cards or a dozen browser tabs open to recipes they never got around to saving properly.

## Features

- **A chatbot that can actually cook with you.** Scale a recipe to a different serving size, convert between units, get a substitution for something you're out of, or ask what you can make with the ingredients you already have. All of it backed by real function calling against your own recipe book, not the model guessing.
- **Cooking Mode.** Start cooking a recipe and the app tracks which step you're on. Ask the assistant something like "the sauce looks too thick" without naming the recipe or the step, it already knows both.
- **Import recipes from a photo or a link.** Take a picture of a handwritten recipe card, even messy handwriting, or paste a link to a recipe online, and review the extracted result before saving it. Both paths go through the same edit screen, so you can fix anything that came out wrong.
- **Discover new recipes from the web.** Describe what you're in the mood for and the assistant searches the web for real recipes that match, skipping anything you've already saved.
- **Your own account.** Recipes, cooking sessions, and everything else are scoped to your login, not shared with whoever else happens to be using the deployed app.
- **Full observability.** Every call to Gemini, whether it's a chat message, a recipe extraction, or a web search, is traced in Langfuse.

## Tech Stack

**Backend:**
- Python
- Streamlit
- Google Gemini API, via the `google-genai` SDK

**Database:**
- Postgres (hosted on Supabase or Neon)
- `psycopg2`

**AI/ML:**
- Gemini function calling for the chat agent
- Structured output (Pydantic schemas) for recipe extraction from images and web pages
- Google Search grounding for recipe discovery
- Langfuse for tracing, via OpenInference's instrumentation for the `google-genai` SDK

**Other:**
- `bcrypt` for password hashing
- `trafilatura` for pulling clean article text out of recipe web pages

## Architecture

The short version: Streamlit pages call either the chat agent, the recipe importer, or the recipe discovery module, and all three eventually talk to Gemini and log to Postgres and Langfuse. The chat agent has its own set of tools it can call mid-conversation, split between plain deterministic functions and thin wrappers that give those functions access to the database on the model's behalf.

Full writeup, including the reasoning behind a few decisions that changed partway through the project, is in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Every tool the chat agent can call is documented individually in [`docs/TOOLS.md`](docs/TOOLS.md).

## Installation & Setup

### Prerequisites

- Python 3.12 or newer
- A Google API key for Gemini, from [Google AI Studio](https://aistudio.google.com/apikey)
- A Postgres database (a free Supabase or Neon project works fine)
- Optionally, a free [Langfuse](https://cloud.langfuse.com) account for tracing

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/Weverken/Cap_Project
cd Cap_Project
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

Then fill in `.env` with your actual values:
```
DATABASE_URL=your_postgres_connection_string
GOOGLE_API_KEY=your_gemini_api_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

If you're using Supabase, grab the "Session pooler" connection string from Project Settings > Database, not the Project URL shown on the main dashboard, those are two different things.

The Langfuse keys are optional. Leave them blank and the app still runs, it just won't send traces.

4. Run the application:
```bash
streamlit run streamlit_app.py
```

The database tables get created automatically on first run, there's no separate migration step to run.

## Usage

1. Open the app and create an account on the sign up tab.
2. Add a recipe, either manually from My Recipes, or by importing a photo or a link from the Import Recipe page.
3. From a recipe's page, click Start Cooking to begin a cooking session.
4. Head to the Cooking Assistant page and chat with it. Try something like "scale this to 6 servings" or "I'm out of buttermilk, what can I use instead."
5. Use Discover Recipes any time you want ideas for something you haven't made before.

## Deployment

**Live Application:** [https://cookmateproject.streamlit.app/]

**Deployment Platform:** Streamlit Community Cloud

The database is hosted separately on Postgres rather than as a local file, specifically so recipes and accounts survive a redeploy or restart. 

## Project Structure

```
Cap_Project/
├── streamlit_app.py           # Entry point, auth gate, navigation
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── config.toml            # App theme
├── pages/
│   ├── login.py                # Landing page, login and signup
│   ├── cooking_assistant.py    # Chat + cooking mode
│   ├── my_recipes.py           # Recipe book
│   ├── import_recipe.py        # Import from photo or URL
│   └── discover_recipes.py     # Web recipe search
├── src/
│   ├── config.py                # Centralized settings
│   ├── auth.py                  # Signup/login logic
│   ├── observability.py         # Langfuse setup
│   ├── database/                 # Postgres access, one file per table
│   ├── agent/                    # The chat agent and its tools
│   ├── tools/                    # Plain, deterministic functions
│   ├── importer/                 # Recipe extraction from images/URLs
│   ├── discovery/                # Web recipe search
│   └── prompts/                  # All prompt text, kept out of the code
├── docs/
│   ├── ARCHITECTURE.md
│   └── TOOLS.md
└── tests/
```

## Known Limitations

- URL import needs a page that renders without JavaScript, since the fetch doesn't run a browser.
- A couple of the assistant's behaviors (not repeating already-saved recipes in Discover, distinguishing a permanent recipe change from a one-off substitution) are guided by the system prompt rather than enforced in code. Covered in more detail in the architecture doc.

## Author

Lowie De Wever - 20231733

## License

Not applicable for this project.
