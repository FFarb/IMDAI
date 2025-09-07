# AI Image Prompt Engineer

This is a local browser app to assemble a style-aware image prompt with GPT and render images via the OpenAI Images API.

## Features

-   **Style-Aware Prompting**: Uses a powerful GPT model to turn simple keywords into detailed, effective prompts.
-   **Local Generation**: Runs a local backend and frontend for privacy and control.
-   **Image Gallery**: Stores and displays all your generated images locally.
-   **Generate up to 4 Images**: Create multiple image variations from a single prompt in one go.
-   **Download Images**: Save your favorite creations directly to your computer.
-   **Preset Management**: Save your favorite slot combinations as named presets and load them anytime.
-   **View Prompts**: See the exact prompt used to generate any image in your gallery.
-   **Color Palette**: A handy color picker to find and copy HEX codes for your prompts.

## Tech Stack

-   **Frontend**: React, Vite, TypeScript, Axios
-   **Backend**: FastAPI (Python)
-   **AI**: OpenAI API (Chat Completions & Images)

## Quickstart

### Prerequisites

-   Python 3.8+ and `pip`
-   Node.js 18+ and `npm`

### 1. Setup Backend

Navigate to the `backend` directory and set up the environment.

```bash
# Navigate to the backend folder
cd backend

# Create and activate a virtual environment (optional but recommended)
# On Mac/Linux
python3 -m venv venv
source venv/bin/activate
# On Windows
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create your environment file
# On Mac/Linux
cp .env.example .env
# On Windows
copy .env.example .env
```

Now, **edit the `.env` file** and add your OpenAI API key.

### 2. Setup Frontend

Open a **new terminal window**. Navigate to the `frontend` directory.

```bash
# Navigate to the frontend folder
cd frontend

# Install dependencies
npm install
```

### 3. Run the Application

You need to have both the backend and frontend servers running.

**In your first terminal (backend):**

```bash
# Make sure you are in the backend/ directory with venv active
uvicorn app:app --reload
```

The backend server will start on `http://127.0.0.1:8000`.

**In your second terminal (frontend):**

```bash
# Make sure you are in the frontend/ directory
npm run dev
```

The frontend development server will start on `http://localhost:5173`. Open this URL in your browser.

### How to Use

1.  The app will open. Click the **settings icon (⚙️)** in the top right.
2.  Enter your OpenAI API Key and click **Save**. The key is stored securely on the backend only.
3.  Fill in the different "slots" on the left panel, or select a pre-made preset from the dropdown.
4.  Use the **Color Palette** to find the perfect color and copy its HEX code into your prompt slots.
5.  To save your current slots for later, type a name in the "Save Current as Preset" field and click **Save**.
6.  Click **Assemble Prompt**. The backend GPT model will generate a detailed JSON prompt.
7.  Select the **Number of Images** you'd like to create (1-4).
8.  Click **Generate Image(s)**.
9.  Your new images will appear in the gallery. Hover over any image to see buttons to **View Prompt** or **Download** it.
10. All images and their prompt data are saved locally in `backend/data/outputs/`.
