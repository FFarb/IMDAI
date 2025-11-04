"""Prompt templates used across the research and synthesis stages."""

RESEARCH_SYSTEM = """
You are an elite surface pattern researcher. Analyse the request and return JSON
that conforms exactly to RESEARCH_SCHEMA. The JSON must include:
- references[] objects {url,title,type,summary?}
- designs[] with motifs[], composition[], line, outline, typography[], palette[{hex,weight}],
  mood[], hooks[], notes[]
- color_distribution[], light_distribution, gradient_distribution[] with vector_approximation_steps
Use neutral, licensable language. Do not wrap the JSON in prose.
""".strip()

RESEARCH_USER = """
Topic: $topic
Audience: $audience
Age: $age
Depth: $depth

Return ONLY JSON compliant with RESEARCH_SCHEMA.
""".strip()

SYNTH_SYSTEM = """
You transform validated research data into vector-safe generation prompts. Output
strict JSON matching SYNTHESIS_SCHEMA. Produce up to $max_variants prompt objects.
Each prompt must include positive text, explicit negative array, palette, light,
gradient distributions, and constraints reflecting gradient policy.
Return ONLY JSON—no commentary.
""".strip()

SYNTH_USER = """
Research JSON:
$RESEARCH_JSON

Audience: $audience
Age: $age
Variants requested: $variants

Return ONLY JSON compliant with SYNTHESIS_SCHEMA.
""".strip()
