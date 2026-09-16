# Architecture

**Project Name:** CookMate

**Team Members:**
1. Lowie De Wever - 20231733

**Project Domain:** Other: Food / Personal Productivity

---

## Part 1: Project Overview

### What problem are you solving?

Most recipe apps are just a place to store text. You save a recipe, you look it up later, and that's about it. If you want to scale it, substitute an ingredient, or figure out what to cook with what's already in your kitchen, you're on your own, or you're back in a general chatbot that has no idea what recipes you actually have saved.

CookMate is built around the idea that a cooking assistant should be able to act on your recipes, not just talk about them. It has real tools wired into your own saved recipe book and database, so it can scale a recipe, convert a measurement, suggest a substitution, or track which step of a recipe you're currently on, instead of guessing at all of it from scratch every time.

### Who will use your application?

Home cooks who collect recipes from more than one place: a shoebox of handwritten cards, screenshots, a dozen browser tabs of recipes that never got properly saved. Basically anyone who wants their recipes organized in one place and wants help actually cooking from them.

### What's your core value proposition? (In one sentence)

CookMate is a cooking assistant that can actually act on your saved recipes while you're cooking, scaling them, tracking your progress through them, adjusting them for what you have, rather than just answering generic questions about food.

---

## Part 2: Define Your Layers

### UI Layer (Streamlit)

**Pages:**

1. Login / landing page (`pages/login.py`)
   - Purpose: sign up or log in, and for anyone who hasn't signed in yet, explain what the app actually does before asking for an account.

2. Cooking Assistant (`pages/cooking_assistant.py`)
   - Purpose: the chat interface, plus a "Currently Cooking" panel that shows the active recipe and step when a cooking session is running.

3. My Recipes (`pages/my_recipes.py`)
   - Purpose: the personal recipe book. Add, edit, delete, search, and start a cooking session from a saved recipe.

4. Import Recipe (`pages/import_recipe.py`)
   - Purpose: turn a photo or a URL into a saved recipe, with a review screen before anything is written to the database.

5. Discover Recipes (`pages/discover_recipes.py`)
   - Purpose: describe what you want and get real recipe suggestions pulled from the web, skipping anything already saved.

**User Inputs:**

- File upload (images)
  - File types: PNG, JPG, JPEG (photos of recipe cards or screenshots)
- Text input (questions, search, forms)
  - For: chat messages, recipe fields when adding or editing, search terms, recipe URLs, login and signup fields, the "what are you in the mood for" discovery query
- Numeric inputs
  - For: servings, prep time, cook time, ingredient quantities
- Other: buttons for step navigation (previous/next), starting or ending a cooking session, add/remove rows when editing ingredients or instructions

**What do you display to users?**

- Extracted structured data (the recipe review screen after an image or URL import)
- Chat conversations
- Tables and lists (recipe cards, search results, ingredient/instruction lists)
- Other: source links for discovered recipes, current step and progress during cooking mode, extraction confidence and notes after an import

---

### Service Layer (Business Logic)

**Service 1:** Database Service (`src/database/`)

Purpose: persist and retrieve everything the app needs to remember, recipes, cooking sessions, and user accounts.

Main responsibilities:
- Run the actual CRUD queries against Postgres for each table
- Create tables on first run if they don't exist yet
- Keep every query scoped to the right user, so one account never sees another's data

**Service 2:** Agent Service (`src/agent/service.py` and `src/agent/context.py`)

Purpose: run the conversational cooking assistant.

Main responsibilities:
- Hold the Gemini chat session and its history for a given browser session
- Register the available tools and hand them to the model
- Retry on transient failures and fail gracefully on ones that won't fix themselves
- Track which user's request is currently being handled, safely, even if more than one person is using the deployed app at the same time

**Service 3:** Import and Discovery Service (`src/importer/` and `src/discovery/`)

Purpose: turn outside content into usable recipe data.

Main responsibilities:
- Fetch and clean web page content before it reaches the model
- Extract a structured recipe from either an image or cleaned web text
- Search the web for recipe suggestions that match a plain language request

---

### AI Layer (Gemini Operations)

- [x] **Extract structured data from documents**
  - Extract what fields: recipe name, description, servings, prep time, cook time, ingredients (quantity, unit, name), instructions, tags, plus a confidence rating and a note about anything uncertain in the source

- [x] **Chat/Q&A with context**
  - About what: the user's own saved recipes and, when a cooking session is active, exactly what they're cooking and which step they're on

- [ ] **Summarization**

- [ ] **Classification/Categorization**

- [x] **Text generation**
  - Generate what: the write-up for each suggested recipe on the Discover Recipes page

- [ ] **Comparison**

- [ ] **Analysis**

- [x] **Other:** function calling / tool orchestration (the chat agent deciding when and how to call a tool), and Google Search grounding for pulling real recipes from the web

**Will you need multi-turn conversations?**

[x] Yes
[ ] No

If yes, for what purpose: the cooking assistant needs to remember what recipe someone is cooking and what's already been discussed, so they can say something like "the sauce looks too thick" without repeating the recipe name or which step they're on.

---

### Tools Layer (Function Calling)

Nine tools total, registered with the agent in `src/agent/tools.py`. Full detail on each one, including exact parameters and return values, is in `docs/TOOLS.md`. Summarized here:

**Tool 1:** scale_recipe_tool

- Purpose: scale a saved recipe's ingredients to a different serving size
- Inputs: recipe name, target servings
- Output: scaled ingredient list and the scale factor used

**Tool 2:** convert_measurement_tool

- Purpose: convert a quantity between units in the same category (volume to volume, or weight to weight)
- Inputs: quantity, source unit, target unit
- Output: the converted quantity, or an error if the units aren't compatible

**Tool 3:** find_recipe_substitution_tool

- Purpose: look up a tested substitution ratio for a short list of ratio-sensitive ingredients (mostly leavening agents and baking staples)
- Inputs: the ingredient to substitute
- Output: one or more substitution options with ratios, or a clear "not found" so the model knows to fall back on general knowledge instead

Six more tools cover finding recipes by available ingredients, searching saved recipes, reading and advancing the current cooking session, logging a one-off substitution for that session only, and permanently saving a substitution to a recipe. All documented in `docs/TOOLS.md`.

**Will AI call these automatically?**

[x] Yes, using function calling
[ ] No, services will call them directly

---

## Part 3: Data Flow

**User Action:** someone who's actively cooking says "I don't have soy sauce, what can I use instead," then later says "save that substitution."

**Step-by-Step Flow:**

```
1. User types the message into the chat input
        ↓
2. Streamlit (cooking_assistant.py) calls: CookingAgent.send_message
        ↓
3. Which service: Agent Service
   What does it do:
   a. Sends the message plus conversation history to Gemini
   b. Gemini decides find_recipe_substitution_tool is needed and the SDK calls it
   c. The tool checks the substitution table, doesn't find soy sauce, returns found: false
        ↓
4. AI service called for: a final answer once the tool result comes back
   Input: the tool's "not found" result, plus the system prompt's instruction to fall back
          on general knowledge and say so when that happens
   Output: a plain language suggestion, clearly framed as a general suggestion rather
           than a tested substitution
        ↓
5. Tools called: find_recipe_substitution_tool on the first message,
   save_recipe_change_tool on the follow-up once the user says "save that"
        ↓
6. Data returned to UI: the assistant's reply is added to the chat, and on the
   save step, the recipe's ingredient list in Postgres is permanently updated
        ↓
7. User sees: the suggestion in chat, and afterward, the recipe in My Recipes
   reflects the swapped ingredient
```

---

## Part 4: Data Schema

### What structured data do you extract?

This is the schema used for recipes extracted from either a photo or a URL (`src/importer/schema.py`), and it matches the shape recipes are stored in once saved.

**Your Actual Schema:**

```json
{
  "name": "string, the recipe title",
  "description": "string, short description, can be empty",
  "servings": "integer, 0 if not stated in the source",
  "prep_time": "integer, minutes, 0 if not stated",
  "cook_time": "integer, minutes, 0 if not stated",
  "ingredients": [
    {
      "quantity": "number, 0 if no amount was given",
      "unit": "string, empty for countable items with no unit",
      "name": "string"
    }
  ],
  "instructions": ["list of strings, one per step"],
  "tags": ["list of strings, optional"],
  "extraction_confidence": "string, one of high, medium, low",
  "extraction_notes": "string, notes on anything uncertain or guessed, can be empty"
}
```

**Required fields (must have):**
- name
- ingredients
- instructions

**Optional fields (nice to have):**
- description
- servings, prep_time, cook_time (default to 0 when not stated rather than being left out, so the review screen has something to show and edit)
- tags
- extraction_confidence and extraction_notes (these exist specifically so a messy or uncertain extraction is flagged rather than silently guessed at)

---

## Key Technical Decisions

The worksheet above covers the plan. This section covers the reasoning behind a few choices that aren't obvious from the plan alone, some of which changed partway through building.

**Postgres instead of SQLite.** The project started on SQLite, since that's what was covered in class and it's the obvious choice for local development. It got swapped to Postgres before deployment for one specific reason: most free hosting platforms run apps in containers that get wiped on restart or redeploy. A SQLite file sitting on local disk would lose every saved recipe the moment the app restarted. Postgres, hosted separately through Supabase or Neon's free tier, keeps that data outside the app's own container.

**Thread-local storage for the current user, not a global variable.** The agent's tools are plain Python functions, not methods tied to a specific request, but they need to know which user they're acting on behalf of. A single global variable would work for one person using the app at a time, but Streamlit can run more than one person's session concurrently in the same process, each in its own thread. A global would let one person's request leak into another's mid-conversation. `src/agent/context.py` uses `threading.local()` instead, which gives each thread its own isolated copy. This was tested directly: two threads set different user ids with a deliberate delay between them to force overlap, and the values didn't cross.

**Two layers of tools.** `src/tools/` holds plain, deterministic functions with no AI involved, and `src/agent/tools.py` wraps each one in a version the model can call. The reason for the split: the model can only pass along simple values like strings and numbers, not a full recipe object pulled from the database, and it shouldn't have raw database access either. The wrapper takes the simple value the model provides, does the database lookup itself, and only then calls the underlying pure function.

**Structured output for extraction, not a JSON-shaped prompt.** Both the image importer and the URL importer use Gemini's structured output mode, where a Pydantic schema is set as `response_schema`, rather than asking the model to reply in JSON and hoping it listens. The response comes back already validated against the schema.

**Structured output and Google Search grounding are never combined in the same call.** That combination is documented as unreliable on the specific model this project uses, with reports of it silently returning no text on longer prompts. Recipe discovery instead gets plain text back from a grounded call, formatted through prompt instructions, and the source links shown separately come from the response's grounding metadata rather than the model's own writing.

**A domain blocklist enforced in code.** Gemini's search tool has an `exclude_domains` option, but its own documentation states it isn't supported outside Vertex AI, so it does nothing on the API key based access this project uses. Keeping social media links out of the suggested sources needed an actual blocklist checked in code after the search results come back.

**Web page text gets cross-checked against the page's own structured data.** URL import runs page content through `trafilatura` to strip navigation, ads, and footers before anything reaches the model. That stripping had a side effect worth catching: many recipe sites show prep time, cook time, and servings in a small metadata widget separate from the main article text, and trafilatura's boilerplate detection was removing that widget along with the actual boilerplate. The fix was to also parse the page's `schema.org/Recipe` structured data, the same JSON-LD data Google uses for its own recipe search results, and hand those numbers to the model directly instead of relying on it to infer them from text that might not contain them anymore.

---

**Who builds what:**

**Member 1:** Lowie De Wever → Responsible for: Everything

---

## Part 6: Next Steps

This section was originally meant for planning ahead before building. Since this document is being finalized close to submission, it's written instead as a note on what's left, in case there's time to keep going after this is turned in.

**Would harden if there were more time:**
- A couple of the assistant's behaviors are currently enforced through the system prompt rather than in code: not repeating already-saved recipes in Discover Recipes, and telling apart a permanent recipe change from a one-off substitution. Both work well in practice but aren't a hard guarantee the way a database constraint would be.

**Deliberately left out:**
- PDF import was considered early on but dropped. A recipe uploaded as a PDF is a less natural case than a photo of a card or a link to a recipe site, those two already cover how people actually have recipes lying around. The placeholder for it never had real extraction logic behind it, so rather than ship a non-functional third option, it was removed and the importer stayed focused on the two paths that actually work.

**Already handled but worth knowing about:**
- The database moved from SQLite to Postgres before deployment, specifically because most free hosting platforms wipe local files on restart. Full reasoning is in the Key Technical Decisions section above.
- User accounts were not part of the original plan and got added once it became clear the deployed app needed to keep different people's recipes separate.