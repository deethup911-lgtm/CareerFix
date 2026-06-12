import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_env_var(key, default=None):
    return os.environ.get(key, default)
