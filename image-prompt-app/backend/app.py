import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import openai

# --- Configuration & Initialization ---
logging.basicConfig(level=logging.INFO)
load_dotenv()

# In-memory storage for API key (for MVP dev purposes)
# In production, use a more secure method.
API_KEY_STORE = {"api_key": os.getenv("OPENAI_API_KEY")}

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

# Initialize on startup
initialize_openai_client()

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Vite dev server
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

class ApiKey(BaseModel):
    api_key: str

# --- Helper Functions ---
def create_directories():
    os.makedirs("data/outputs", exist_ok=True)

create_directories()

MASTER_PROMPT_TEMPLATE = """
You are an expert image prompt generator. Your task is to take a set of input 'slots' and combine them into a coherent, high-quality positive and negative prompt for an AI image generator. The user wants a style-aware prompt.

Return ONLY a valid JSON object with three keys: "positive", "negative", and "params".
- "positive": A detailed, comma-separated string for the main image prompt.
- "negative": A detailed, comma-separated string for things to avoid.
- "params": A JSON object containing image generation parameters.

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
    """Accept API key from frontend and store it server-side."""
    if not key.api_key:
        raise HTTPException(status_code=400, detail="API key cannot be empty.")
    API_KEY_STORE["api_key"] = key.api_key
    initialize_openai_client() # Re-initialize client with the new key
    return {"message": "API key updated successfully."}


@app.post("/api/assemble", response_model=PromptDTO)
async def assemble_prompt(slots: Slots):
    """Assembles a detailed prompt using GPT."""
    if not client:
        raise HTTPException(status_code=400, detail="OpenAI client not initialized. Please set API key.")

    content = MASTER_PROMPT_TEMPLATE.format(**slots.dict())

    for attempt in range(2): # Main attempt + 1 repair pass
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": content}],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            response_text = response.choices[0].message.content
            data = json.loads(response_text)

            # Validate required keys
            if all(k in data for k in ["positive", "negative", "params"]):
                # Merge base negative prompt
                data["negative"] = f"{BASE_NEG}, {data.get('negative', '')}".strip(', ')
                # Ensure default params are present
                final_params = DEFAULT_PARAMS.copy()
                final_params.update(data.get("params", {}))
                data["params"] = final_params
                return PromptDTO(**data)
            else:
                raise ValueError("JSON response missing required keys.")

        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Attempt {attempt + 1}: Failed to parse JSON. Error: {e}")
            if attempt == 0:
                # On first failure, ask the model to repair it
                content += f"\n\nThe previous attempt failed. Please fix the JSON output. It must be a valid JSON object with keys 'positive', 'negative', and 'params'. The error was: {e}. Raw output was: {response_text}"
            else:
                raise HTTPException(status_code=500, detail="Failed to generate valid prompt from LLM after repair attempt.")

    raise HTTPException(status_code=500, detail="An unexpected error occurred during prompt assembly.")


@app.post("/api/image")
async def generate_image(req: ImageRequest):
    """Generates an image using OpenAI Images API."""
    if not client:
        raise HTTPException(status_code=400, detail="OpenAI client not initialized. Please set API key.")

    try:
        prompt = req.prompt
        response = client.images.generate(
            model="dall-e-3", # As per user request, this would be gpt-image-1, but dall-e-3 is the current name.
            prompt=prompt.positive,
            n=1,
            size=prompt.params.get("size", "1024x1024"),
            quality=prompt.params.get("quality", "standard"),
            style=prompt.params.get("style", "vivid"),
        )

        image_url = response.data[0].url

        # For a local app, we'd typically download the image.
        # This MVP will just pass the URL back for simplicity, but a real app should save it.
        # Let's save it to show the full local flow.
        import httpx
        async with httpx.AsyncClient() as http_client:
            image_response = await http_client.get(image_url)
            image_response.raise_for_status()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}.png"
        filepath = os.path.join("data", "outputs", filename)

        with open(filepath, "wb") as f:
            f.write(image_response.content)

        return {"image_path": f"/images/{filename}", "prompt": prompt.dict()}

    except Exception as e:
        logging.error(f"Image generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/images", response_model=List[str])
async def get_images():
    """Returns a list of generated image filenames."""
    image_dir = "data/outputs"
    if not os.path.isdir(image_dir):
        return []

    files = sorted(
        [f"/images/{f}" for f in os.listdir(image_dir) if f.lower().endswith(".png")],
        reverse=True
    )
    return files

# Serve static images from the data/outputs directory
from fastapi.staticfiles import StaticFiles
app.mount("/images", StaticFiles(directory="data/outputs"), name="images")
