import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

def get_env_var(key, default=None):
    return os.environ.get(key, default)

def clean_text(text):
    if not text:
        return ""
    # Remove excessive newlines and spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
