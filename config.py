import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Supabase configuration (with checks for missing variables)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
CONTROL_UNIT_ID = os.getenv("CONTROL_UNIT_ID")

# Check if required environment variables are missing
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is not set in .env file")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY is not set in .env file")
if not CONTROL_UNIT_ID:
    raise ValueError("CONTROL_UNIT_ID is not set in .env file")

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "ERROR")
CONSOLE_LOGGING = os.getenv("CONSOLE_LOGGING", "True").lower() in ("true", "1", "t", "yes")

# Set up logging with rotation in case logs grow large
log_handler = logging.FileHandler("controller.log")
log_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log_handler.setFormatter(formatter)

# Set up console logging if enabled
console_handler = logging.StreamHandler() if CONSOLE_LOGGING else None
if console_handler:
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

# Initialize logging with handlers
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[log_handler, console_handler] if console_handler else [log_handler]
)

logger = logging.getLogger("raspberry-iot")  # before "rpi_controller"

# Log that the logging configuration is set up
logger.debug("Logging configured with level %s", LOG_LEVEL)
