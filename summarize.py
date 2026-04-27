import os
from pathlib import Path

# from dotenv import load_dotenv
from google import genai
import streamlit as st
# load_dotenv()

# _API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
_API_KEY = st.secrets["GOOGLE_API_KEY"] or st.secrets["GEMINI_API_KEY"]
_CLIENT = None

MODEL = "gemini-2.5-pro"
PROMPT = (
    "From transcript, output EXACTLY these 10 lines in same order. "
    "If missing use N/A. "
    "For Caller Name, use the system name provided below as the agent is the caller. "
    "For Duration, use the last timestamp as call duration if no explicit duration is given. "
    "For Date & Time, extract from transcript file name and write EXACTLY as: MM-DD-YYYY HH-MM (24hr). Example: 04-22-2026 01-00 "
    "For Response, determine final state: "
    "If APPROVED (agent says approved/authorized/active/pharmacy can fill): '1-2 sentences. Approved. [Dates if given]. [Case ID if given].' "
    "If DENIED (agent says denied/rejected/not covered): 'Denied. [Date]. Reason: [reason]. Next Steps: [steps if given].' "
    "If OTHER (pending/transferred/info request/office closed): narrative 3-4 sentences covering what happened and outcome. "
    "Agent means insurance/PBM rep. Caller means our agent making the call. Include Reference/Case ID if agent provides it.\n"
    "For each field, extract only the exact value stated for that field (e.g., for Member_ID extract only Member_ID, for Insurance extract only Insurance, etc.). Do not mix values between fields. "
    "For Member_ID fill it like this: 13004951. Do not add any extra text or space etc.\n"
    "Date_&_Time: \n"
    "Caller_Name: \n"
    "Duration: \n"
    "Patient_Name: \n"
    "Medication: \n"
    "Pharmacy: \n"
    "Insurance: \n"
    "Member_ID: \n"
    "Prescriber: \n"
    "Status: \n"
    "Response: "
)

def _get_client():
    global _CLIENT
    if _CLIENT is None:
        if not _API_KEY:
            raise RuntimeError("Missing GOOGLE_API_KEY or GEMINI_API_KEY in .env")
        _CLIENT = genai.Client(api_key=_API_KEY)
    return _CLIENT


def summarize(transcript: str, filename: str = "") -> str:
    """
    Takes transcript as a string and optional filename for date extraction.
    Returns summary as a string.
    """
    client = _get_client()

    full_prompt = (
        f"{PROMPT}\n\n"
        f"Transcript file name: {filename}\n"
        f"Transcript:\n{transcript}"
    )

    response = client.models.generate_content(model=MODEL, contents=full_prompt)
    return (response.text or "").strip()
