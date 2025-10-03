import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import openai

from discovery.router import router as discovery_router

# --- Configuration & Initialization ---
logging.basicConfig(level=logging.INFO)
load_dotenv()

API_KEY_STORE = {"api_key": os.getenv("OPENAI_API_KEY")}
PRESETS_FILE = "../presets.json" # Path to presets file in the root folder

app = FastAPI()
client = None

def initialize_openai_client():
    global client
    if API_KEY_STORE["api_key"]:
        try:
            client = openai.OpenAI(api_key=API_KEY_STORE["api_key"])
            logging.info("OpenAI client initialized successfully.")
        except Exception as e:
            client = None
            logging.error(f"Failed to initialize OpenAI client: {e}")
    else:
        client = None
        logging.warning("OpenAI client not initialized. API key is missing.")

initialize_openai_client()

app.include_router(discovery_router, prefix="/api/discover")

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Constants & Data Models ---
BASE_NEG = "ugly, tiling, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, extra limbs, disfigured, deformed, body out of frame, bad anatomy, watermark, signature, cut off, low contrast, underexposed, overexposed, bad art, beginner, amateur, distorted face"

DEFAULT_PARAMS = {
    "size": "1024x1024",
    "quality": "standard",
    "style": "vivid"
}

class Slots(BaseModel):
    subject: str = ""
    style: str = ""
    composition: str = ""
    lighting: str = ""
    mood: str = ""
    details: str = ""
    quality: str = "best quality, 4k"

class PromptDTO(BaseModel):
    positive: str
    negative: str
    params: Dict[str, Any]

class ImageRequest(BaseModel):
    prompt: PromptDTO
    n: int = Field(1, ge=1, le=4) # Number of images to generate

class ApiKey(BaseModel):
    api_key: str

class PresetSaveRequest(BaseModel):
    name: str
    slots: Slots

class ImageWithPrompt(BaseModel):
    image_path: str
    prompt: Optional[PromptDTO] = None


# --- Helper Functions ---
def create_directories():
    os.makedirs("data/outputs", exist_ok=True)

create_directories()

MASTER_PROMPT_TEMPLATE = """
You are an expert image prompt generator. Your task is to take a set of input 'slots' and combine them into a coherent, high-quality positive and negative prompt for an AI image generator. The user wants a style-aware prompt.

Return ONLY a valid JSON object with three keys: "positive", "negative", and "params".
- "positive": A detailed, comma-separated string for the main image prompt. Integrate the user's 'Quality' input (e.g., '4k, best quality') directly into this positive prompt string.
- "negative": A detailed, comma-separated string for things to avoid.
- "params": A JSON object for technical settings. This object should ONLY contain keys for 'size' and 'style' if specified. Do NOT include a 'quality' key in this params object.

Do not include any other text, explanations, or markdown.

Here are the input slots:
- Subject: {subject}
- Style: {style}
- Composition: {composition}
- Lighting: {lighting}
- Mood: {mood}
- Details: {details}
- Quality: {quality}
"""

# --- API Endpoints ---
@app.post("/api/settings/key")
async def set_api_key(key: ApiKey):
    if not key.api_key:
        raise HTTPException(status_code=400, detail="API key cannot be empty.")
    API_KEY_STORE["api_key"] = key.api_key
    initialize_openai_client()
    return {"message": "API key updated successfully."}


@app.post("/api/assemble", response_model=PromptDTO)
async def assemble_prompt(slots: Slots):
    if not client:
        raise HTTPException(status_code=400, detail="OpenAI client not initialized. Please set API key.")

    content = MASTER_PROMPT_TEMPLATE.format(**slots.dict())

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": content}],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            response_text = response.choices[0].message.content
            data = json.loads(response_text)

            if all(k in data for k in ["positive", "negative", "params"]):
                data["negative"] = f"{BASE_NEG}, {data.get('negative', '')}".strip(', ')
                final_params = DEFAULT_PARAMS.copy()
                final_params.update(data.get("params", {}))

                # --- Defensive Check ---
                # Ensure size is valid, otherwise default it.
                valid_sizes = ["1024x1024", "1024x1792", "1792x1024"]
                if final_params.get("size") not in valid_sizes:
                    final_params["size"] = "1024x1024"

                data["params"] = final_params
                return PromptDTO(**data)
            else:
                raise ValueError("JSON response missing required keys.")

        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Attempt {attempt + 1}: Failed to parse JSON. Error: {e}")
            if attempt == 0:
                content += f"\n\nThe previous attempt failed. Please fix the JSON output. It must be a valid JSON object with keys 'positive', 'negative', and 'params'. The error was: {e}. Raw output was: {response_text}"
            else:
                raise HTTPException(status_code=500, detail="Failed to generate valid prompt from LLM after repair attempt.")

    raise HTTPException(status_code=500, detail="An unexpected error occurred during prompt assembly.")


@app.post("/api/image")
async def generate_image(req: ImageRequest):
    if not client:
        raise HTTPException(status_code=400, detail="OpenAI client not initialized. Please set API key.")

    try:
        prompt = req.prompt
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt.positive,
            n=req.n,
            size=prompt.params.get("size", "1024x1024"),
            quality=prompt.params.get("quality", "standard"),
            style=prompt.params.get("style", "vivid"),
        )

        saved_files = []
        import httpx
        async with httpx.AsyncClient() as http_client:
            for i, image_data in enumerate(response.data):
                image_url = image_data.url
                image_response = await http_client.get(image_url)
                image_response.raise_for_status()

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_filename = f"{timestamp}_{i+1}"
                image_filename = f"{base_filename}.png"
                json_filename = f"{base_filename}.json"

                image_filepath = os.path.join("data", "outputs", image_filename)
                json_filepath = os.path.join("data", "outputs", json_filename)

                with open(image_filepath, "wb") as f:
                    f.write(image_response.content)

                with open(json_filepath, "w") as f:
                    json.dump(prompt.dict(), f, indent=2)

                saved_files.append({"image_path": f"/images/{image_filename}", "prompt": prompt.dict()})

        return saved_files

    except Exception as e:
        logging.error(f"Image generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/images", response_model=List[ImageWithPrompt])
async def get_images():
    image_dir = "data/outputs"
    results = []
    if not os.path.isdir(image_dir):
        return []

    filenames = sorted(os.listdir(image_dir), reverse=True)

    for filename in filenames:
        if filename.lower().endswith(".png"):
            image_path = f"/images/{filename}"
            json_path = os.path.join(image_dir, filename.replace(".png", ".json"))

            prompt_data = None
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r") as f:
                        prompt_data = json.load(f)
                except json.JSONDecodeError:
                    logging.error(f"Could not decode JSON for {filename}")

            results.append(ImageWithPrompt(image_path=image_path, prompt=prompt_data))

    return results

@app.post("/api/presets")
async def save_preset(req: PresetSaveRequest):
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Preset name cannot be empty.")

    try:
        presets = {}
        if os.path.exists(PRESETS_FILE):
            with open(PRESETS_FILE, "r", encoding='utf-8') as f:
                presets = json.load(f)

        presets[req.name] = req.slots.dict()

        with open(PRESETS_FILE, "w", encoding='utf-8') as f:
            json.dump(presets, f, indent=2)

        return {"message": "Preset saved successfully."}
    except Exception as e:
        logging.error(f"Failed to save preset: {e}")
        raise HTTPException(status_code=500, detail="Failed to save preset.")


from fastapi.staticfiles import StaticFiles
app.mount("/images", StaticFiles(directory="data/outputs"), name="images")
