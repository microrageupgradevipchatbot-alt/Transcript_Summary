import os
import time
import tempfile
from pathlib import Path

# from dotenv import load_dotenv
from google import genai

# load_dotenv()
import streamlit as st

# _API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
_API_KEY = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
_CLIENT = None

MODEL = "gemini-2.5-flash"
PROMPT = (
    "Transcribe the entire audio file verbatim, from start to finish, without skipping any part. "
    "Format every line as: [MM:SS] Speaker: text. "
    "Label speakers as Caller or Insurance Agent. No commentary. "
    "Clean up 'umms', 'ahhs', and transcription glitches, but keep every detail of the conversation."
    "Ensure the transcript covers the full duration of the audio, including the ending."
)


def _get_client():
    global _CLIENT
    if _CLIENT is None:
        if not _API_KEY:
            raise RuntimeError("Missing GOOGLE_API_KEY or GEMINI_API_KEY in .env")
        _CLIENT = genai.Client(api_key=_API_KEY)
    return _CLIENT


def transcribe(uploaded_file) -> str:
    """
    Takes a Streamlit UploadedFile object.
    Uploads it to Gemini, transcribes, returns transcript as a string.
    """
    client = _get_client()

    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        f = client.files.upload(file=tmp_path)

        while getattr(f.state, "name", None) == "PROCESSING":
            time.sleep(2)
            f = client.files.get(name=f.name)

        if getattr(f.state, "name", None) == "FAILED":
            raise RuntimeError("Gemini file upload failed.")

        for attempt in range(5):
            try:
                res = client.models.generate_content(model=MODEL, contents=[PROMPT, f])
                break
            except Exception as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    time.sleep(5 * (attempt + 1))
                else:
                    raise
        else:
            raise RuntimeError("Transcription failed after 5 retries.")

        return (res.text or "").strip()

    finally:
        os.unlink(tmp_path)
