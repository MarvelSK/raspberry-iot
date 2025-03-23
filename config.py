import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
CONTROL_UNIT_ID = os.getenv("CONTROL_UNIT_ID")

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "ERROR")
CONSOLE_LOGGING = os.getenv("CONSOLE_LOGGING", "True").lower() in ("true", "1", "t", "yes")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("controller.log"),
        *([] if not CONSOLE_LOGGING else [logging.StreamHandler()])
    ]
)
logger = logging.getLogger("raspberry-iot") # before "rpi_controller"