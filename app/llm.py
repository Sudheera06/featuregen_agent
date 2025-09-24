import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# one-line helper so nodes stay clean
def generate_text(model_name: str, prompt: str) -> str:
    model = genai.GenerativeModel(model_name)
    resp = model.generate_content(prompt)
    return resp.text or ""
