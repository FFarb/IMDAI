import re, json
FENCE_RE = re.compile(r"^\s*```(?:json)?\s*([\s\S]*?)\s*```\s*$", re.I)
def extract_json_text(raw:str)->str:
    if not raw: return ""
    m = FENCE_RE.match(raw.strip())
    return m.group(1) if m else raw
def parse_model_json(raw:str):
    txt = extract_json_text(raw).replace("\ufeff","").replace("\x00","").strip()
    return json.loads(txt)
