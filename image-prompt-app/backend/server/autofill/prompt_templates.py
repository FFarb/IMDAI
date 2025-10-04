"""Prompt templates for OpenAI research requests."""

SYSTEM_PROMPT = (
    "You are a design researcher. For the given TOPIC, AUDIENCE, and AGE RANGE, "
    "use public web search to identify popular print/sticker/poster design traits. "
    "Return strict JSON only. No brand names, logos, monograms, or trademarked terms. "
    "Focus on generic motifs, palettes (5–7 HEX with weights totaling ~1.0), line styles, "
    "outline quality, typography hints (generic), compositions, and mood. All outputs must "
    "be suitable for print-ready vector designs: transparent background, no shadows, no gradients, "
    "no textures, clean vector edges, centered standalone composition. Keep results kids-safe."
)

USER_PROMPT_TEMPLATE = """TOPIC: "{topic}"
AUDIENCE: "{audience}"
AGE RANGE: "{age}"

TASKS:
A) Build 6–10 precise search queries that combine the topic with audience & age, favoring terms like:
   "trending vector stickers", "print-ready", "minimal palette", "pastel", "kawaii", "nursery", "kids safe",
   "luxury-inspired geometric", "monogram grid (generic)", "thin outline", "clean outline", "centered composition",
   "die-cut", "sticker design", "popular motifs", "color hex", "palette".
B) Survey recent roundups/galleries (kids-safe). Extract:
   - PALETTE: 5–7 HEX with weights ~1.0
   - MOTIFS: 8–12 short generic tags (no brands)
   - LINE: "thin" | "regular" | "bold"
   - OUTLINE: "clean" | "rough"
   - TYPOGRAPHY: up to 3 generic hints (or [] to avoid text)
   - COMPOSITION: whitelist only ("centered","single character","subtle lattice","grid","minimal frame")
   - MOOD: up to 3 words
   - NEGATIVE: must include ["photo-realism","photographic textures","noise","background patterns","brand logos","trademark words"]
   - SEED_EXAMPLES: 2–3 short descriptions (no brands)
   - SOURCES: up to 10 {{title,url}} (links; no images)
C) Compose a final MASTER PROMPT (text) that **explicitly** includes:
   "transparent background, no shadows, no gradients, no textures, clean vector edges, centered standalone composition"
D) Provide a mirrored MASTER PROMPT JSON for programmatic use.

STRICT JSON SCHEMA:
{{
  "palette": [{{"hex":"#RRGGBB","weight":0.18}}, ... 5-7 items ...],
  "motifs": ["short tag","... (8-12) ..."],
  "line_weight": "thin|regular|bold",
  "outline": "clean|rough",
  "typography": ["rounded sans","minimal letterforms"],
  "composition": ["centered","single character","subtle lattice"],
  "audience": "{audience}",
  "age": "{age}",
  "mood": ["soft","cozy","premium minimal"],
  "seed_examples": ["...","..."],
  "negative": ["photo-realism","photographic textures","noise","background patterns","brand logos","trademark words"],
  "sources": [{{"title":"...","url":"..."}}],
  "master_prompt_text": "FULL TEXT PROMPT HERE",
  "master_prompt_json": {{
    "subject":"...",
    "palette":["#..."],
    "motifs":[...],
    "line":"thin|regular|bold",
    "outline":"clean|rough",
    "typography":[...],
    "composition":[...],
    "mood":[...],
    "negative":[...]
  }}
}}

REQUIREMENTS:
- Return JSON only (no prose).
- No brand/trademark words. Kids-safe.
- Ensure print-ready constraints are present in master_prompt_text.
"""
