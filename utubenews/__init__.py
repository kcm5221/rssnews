"""Core modules for the utubenews RSS pipeline."""

try:
    from dotenv import load_dotenv
except ImportError:  # ``python-dotenv`` may be optional
    def load_dotenv(*_args, **_kwargs):
        return False

# Load environment variables from a .env file if present. This must happen
# before other modules import configuration values via ``os.getenv``.
load_dotenv()
