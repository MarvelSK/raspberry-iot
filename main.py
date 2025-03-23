import os
import time
import asyncio
import schedule
import RPi.GPIO as GPIO
from dotenv import load_dotenv
from supabase import create_client_async, ClientOptions
from controller_service import ControllerService
from gpio_handler import GPIOHandler
from supabase_handler import SupabaseHandler

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
CONTROLLER_ID = os.getenv("CONTROLLER_ID")

options = ClientOptions(postgrest_client_timeout=10, realtime={"timeout": 30})


async def main():
    # Create async Supabase client
    supabase = await create_client_async(SUPABASE_URL, SUPABASE_KEY, options=options)

    gpio_handler = GPIOHandler()
    supabase_handler = SupabaseHandler(supabase, CONTROLLER_ID)
    controller_service = ControllerService(supabase_handler, gpio_handler, CONTROLLER_ID)

    controller_service.initialize()

    # Subscribe to device changes asynchronously
    await controller_service.subscribe_to_device_changes()

    # Schedule periodic tasks
    schedule.every(10).seconds.do(controller_service.update_controller_status)
    schedule.every(5).seconds.do(controller_service.update_sensor_readings)
    schedule.every(1).minutes.do(controller_service.check_connection)

    print(f"Controller {CONTROLLER_ID} is running...")

    try:
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)  # Async sleep
    except KeyboardInterrupt:
        print("Controller shutting down...")
    finally:
        controller_service.cleanup()
        GPIO.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
