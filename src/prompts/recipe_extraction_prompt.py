"""
Prompt used for AI recipe extraction from images.

Kept separate from the extractor logic so it can be reviewed/
tuned independently — same pattern as src/prompts/system_prompt.py
for the chat agent.
"""

RECIPE_EXTRACTION_PROMPT = """\
You are extracting a recipe from an image into structured data.
The image may be a screenshot of an online recipe, a photo of a
cookbook page, or a photo of a handwritten recipe card.

Guidelines:
- Extract exactly what's in the image. Do not invent ingredients,
  steps, quantities, or times that aren't shown or clearly implied.
- If handwriting or a quantity is illegible, make your best
  reasonable guess but note it in extraction_notes, and lower
  extraction_confidence accordingly.
- Split instructions into individual steps where the source has
  clear step boundaries (numbered steps, separate lines/
  paragraphs). If the source is one dense paragraph with no clear
  breaks, use your judgment to split it into logical steps rather
  than returning one giant block of text.
- For ingredients with no explicit unit (e.g. "3 eggs", "2 cloves
  garlic"), leave the unit field as an empty string and put the
  counting noun in the name instead (e.g. name="garlic cloves").
- Some ingredients have a vague amount instead of a number (e.g.
  "a little onion", "salt to taste", "a pinch of pepper"). For
  these, set quantity to 0 and put the vague phrase itself in the
  unit field (e.g. unit="a little", or unit="to taste") — don't
  just discard the phrase. This preserves what the card actually
  says instead of silently leaving no signal at all.
- If an ingredient is listed with genuinely no quantity language
  at all — not even a vague phrase — set quantity to 0 and leave
  unit empty. The app will flag quantity=0 rows for the user to
  fill in themselves; it does not mean "zero of this ingredient."
- If servings, prep time, or cook time aren't stated anywhere in
  the image, use 0 rather than guessing a plausible-sounding number.
"""