import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import httpx
import openai

# --- Configuration & Initialization ---
logging.basicConfig(level=logging.INFO)
load_dotenv()

API_KEY_STORE = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "etsy_api_key": os.getenv("ETSY_API_KEY"),
}
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
    text: str = ""
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


class EtsyListingRequest(BaseModel):
    image_path: str
    title: str
    description: str
    price: float
    quantity: int
    taxonomy_id: int


# --- Helper Functions ---
def create_directories():
    os.makedirs("data/outputs", exist_ok=True)

create_directories()


def resolve_output_image_path(image_path: str) -> str:
    if not image_path:
        return ""

    if os.path.isabs(image_path):
        return image_path

    normalized = image_path.lstrip("/")
    if normalized.startswith("images/"):
        normalized = normalized[len("images/") :]

    candidate = os.path.join("data", "outputs", normalized)
    if os.path.isfile(candidate):
        return candidate

    fallback = os.path.join("data", "outputs", os.path.basename(normalized))
    return fallback

MASTER_PROMPT_TEMPLATE_PRINT = """
You are an expert prompt generator for print artwork. Your task is to combine the input 'slots' into a single, coherent prompt string that describes a **print-ready image** exactly like the provided SVG references: bold vector lettering style, no background, clean edges, standalone composition.

Here are the input slots:
- Subject: {subject}
- Text: {text}
- Style: {style}
- Composition: {composition}
- Lighting: {lighting}
- Mood: {mood}
- Details: {details}
- Quality: {quality}

Always ensure the prompt includes the following explicit constraints:
- **It is a print** (sticker, shirt, or poster).
- **The exact text must be included**: render the word(s) from the {text} slot as bold vector letters in the described style.
- **No background**: transparent background only, no scenery, no gradients, no shadows, no posterization, no textures simulating a background.
- **Bold vector lettering style**: flat fills, solid colors, thick outline strokes, smooth clean edges, limited simple color palette.
- Composition must be standalone, centered, isolated, ready for print.
- Lighting must be flat/solid fills (no 3D shading).
- Details should highlight: HEX color palette, stroke thickness, uniform vector outlines, typography style (blocky, cartoon, handwritten, graffiti, minimal, etc.).
- Reinforce: "print-ready, transparent background, flat vector style, clean bold outline, solid fills, high resolution, no gradients, no shadows, no bevels, no photographic textures."

The final output must be **only the prompt string**, merging all slots into a continuous description. Never add JSON or explanations.
"""

# --- API Endpoints ---
@app.post("/api/settings/key")
async def set_api_key(key: ApiKey):
    if not key.api_key:
        raise HTTPException(status_code=400, detail="API key cannot be empty.")
    API_KEY_STORE["api_key"] = key.api_key
    initialize_openai_client()
    return {"message": "API key updated successfully."}


@app.post("/api/settings/etsy_key")
async def set_etsy_api_key(key: ApiKey):
    if not key.api_key:
        raise HTTPException(status_code=400, detail="API key cannot be empty.")
    API_KEY_STORE["etsy_api_key"] = key.api_key
    return {"message": "Etsy API key updated successfully."}


@app.post("/api/assemble", response_model=PromptDTO)
async def assemble_prompt(slots: Slots):
    if not client:
        raise HTTPException(status_code=400, detail="OpenAI client not initialized. Please set API key.")

    content = MASTER_PROMPT_TEMPLATE_PRINT.format(**slots.dict())

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


@app.post("/api/etsy/create_listing")
async def create_etsy_listing(listing: EtsyListingRequest):
    etsy_api_key = API_KEY_STORE.get("etsy_api_key")
    if not etsy_api_key:
        raise HTTPException(status_code=400, detail="Etsy API key not configured.")

    image_file_path = resolve_output_image_path(listing.image_path)
    if not image_file_path or not os.path.isfile(image_file_path):
        raise HTTPException(status_code=404, detail="Image file not found.")

    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            with open(image_file_path, "rb") as image_file:
                image_bytes = image_file.read()

            files = {
                "file": (
                    os.path.basename(image_file_path),
                    image_bytes,
                    "image/png",
                )
            }

            upload_response = await http_client.post(
                "https://openapi.etsy.com/v3/application/uploads/images",
                headers={"x-api-key": etsy_api_key},
                files=files,
            )

            if upload_response.status_code >= 400:
                logging.error(
                    "Etsy upload failed: %s", upload_response.text
                )
                raise HTTPException(
                    status_code=upload_response.status_code,
                    detail="Failed to upload image to Etsy.",
                )

            upload_data = upload_response.json()
            listing_image_id = (
                upload_data.get("listing_image_id")
                or upload_data.get("image_id")
                or upload_data.get("upload_id")
            )

            if not listing_image_id:
                logging.error("Unexpected Etsy upload response: %s", upload_data)
                raise HTTPException(
                    status_code=500,
                    detail="Etsy upload response missing listing image id.",
                )

            listing_payload = {
                "title": listing.title,
                "description": listing.description,
                "who_made": "i_did",
                "when_made": "made_to_order",
                "is_digital": True,
                "type": "download",
                "taxonomy_id": listing.taxonomy_id,
                "price": listing.price,
                "quantity": listing.quantity,
                "listing_image_id": listing_image_id,
            }

            create_response = await http_client.post(
                "https://openapi.etsy.com/v3/application/listings",
                headers={
                    "x-api-key": etsy_api_key,
                    "Content-Type": "application/json",
                },
                json=listing_payload,
            )

            if create_response.status_code >= 400:
                logging.error(
                    "Etsy listing creation failed: %s", create_response.text
                )
                raise HTTPException(
                    status_code=create_response.status_code,
                    detail="Failed to create Etsy listing.",
                )

            listing_data = create_response.json()
            listing_id = listing_data.get("listing_id") or listing_data.get(
                "data", {}
            ).get("listing_id")

            listing_url = (
                f"https://www.etsy.com/listing/{listing_id}" if listing_id else None
            )

            return {
                "message": "Listing created successfully.",
                "listing_id": listing_id,
                "listing_url": listing_url,
            }
    except httpx.HTTPError as exc:
        logging.error("Etsy API communication error: %s", exc)
        raise HTTPException(
            status_code=502, detail="Failed to communicate with Etsy API."
        )


from fastapi.staticfiles import StaticFiles
app.mount("/images", StaticFiles(directory="data/outputs"), name="images")
