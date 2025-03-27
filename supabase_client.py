from supabase import create_client, Client
import psutil
import socket
import uuid
import platform
import threading
import time
from datetime import datetime, UTC
from config import SUPABASE_URL, SUPABASE_KEY, CONTROL_UNIT_ID, logger


class SupabaseManager:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase URL and API key must be set in .env file")

        if not CONTROL_UNIT_ID:
            raise ValueError("Control unit ID must be set in .env file")

        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.control_unit_id = CONTROL_UNIT_ID
        self.connected = False
        self.keep_alive_thread = None  # Thread for updating is_online
        logger.info(f"Initialized Supabase client for control unit: {self.control_unit_id}")

    def get_system_info(self):
        """Retrieve system information (runs once at startup)"""
        try:
            ip_address = socket.gethostbyname(socket.gethostname())
            mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2*6, 8)][::-1])
            firmware = platform.release()
            model = platform.machine()

            return {
                "ip_address": ip_address,
                "mac_address": mac_address,
                "firmware": firmware,
                "model": model
            }
        except Exception as e:
            logger.error(f"Failed to retrieve system info: {e}")
            return {}

    def update_system_info(self):
        """Update Supabase with system information (runs once at startup)"""
        try:
            system_info = self.get_system_info()
            if system_info:
                self.supabase.table("control_units").update(system_info).eq("id", self.control_unit_id).execute()
                logger.info(f"Updated system info: {system_info}")
        except Exception as e:
            logger.error(f"Failed to update system info: {e}")

    def connect(self):
        """Update control unit status to online and start metrics updates"""
        try:
            # Update system information once on startup
            self.update_system_info()

            # Mark as online
            self.supabase.table("control_units").update({
                "is_online": True,
                "last_seen": datetime.now(UTC).isoformat(),
                "cpu_usage": 0,
                "memory_usage": 0,
                "storage_usage": 0
            }).eq("id", self.control_unit_id).execute()

            logger.info(f"Control unit {self.control_unit_id} is now online")
            self.connected = True

            # Start background thread to keep metrics updated
            self.keep_alive_thread = threading.Thread(target=self.keep_alive, daemon=True)
            self.keep_alive_thread.start()

            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            self.connected = False
            return False

    def keep_alive(self):
        """Continuously update metrics every 60 seconds"""
        while self.connected:
            try:
                update_data = {
                    "cpu_usage": psutil.cpu_percent(),
                    "memory_usage": psutil.virtual_memory().percent,
                    "storage_usage": psutil.disk_usage('/').percent,
                    "is_online": True,
                    "last_seen": datetime.now(UTC).isoformat()
                }

                self.supabase.table("control_units").update(update_data).eq("id", self.control_unit_id).execute()
                logger.debug(f"Updated control unit metrics: {update_data}")

            except Exception as e:
                logger.error(f"Failed to update control unit metrics: {e}")

            time.sleep(60)  # Wait 60 seconds before next update

    def disconnect(self):
        """Update control unit status to offline"""
        if not self.connected:
            return

        try:
            self.supabase.table("control_units").update({
                "is_online": False,
                "last_seen": datetime.now(UTC).isoformat()
            }).eq("id", self.control_unit_id).execute()

            logger.info(f"Control unit {self.control_unit_id} is now offline")
            self.connected = False
        except Exception as e:
            logger.error(f"Failed to update offline status: {e}")

    def get_devices(self):
        """Get devices associated with this control unit using the new controller_id field"""
        try:
            response = self.supabase.table("devices").select("*").eq(
                "controller_id", self.control_unit_id
            ).execute()

            if isinstance(response, dict) and "data" in response:
                devices = response["data"]
                logger.info(f"Retrieved {len(devices)} devices for control unit")
                return devices
            else:
                logger.warning("No data returned when fetching devices")
                return []

        except Exception as e:
            logger.error(f"Failed to fetch devices: {e}")
            return []

    def update_device_status(self, device_id, is_active=None, value=None):
        """Update device status in Supabase"""
        try:
            update_data = {"last_updated": datetime.now(UTC).isoformat()}

            if is_active is not None:
                update_data["is_active"] = is_active

            if value is not None:
                update_data["value"] = value

            response = self.supabase.table("devices").update(
                update_data
            ).eq("id", device_id).execute()

            if isinstance(response, dict) and "data" in response and response["data"]:
                device_data = response["data"][0]
                action = f"updated to {'on' if is_active else 'off'}" if is_active is not None else ""
                if value is not None:
                    if action:
                        action += f" with value {value}"
                    else:
                        action = f"value changed to {value}"

                self.supabase.table("activity_log").insert({
                    "device_name": device_data.get("name", "Unknown device"),
                    "device_type": device_data.get("type", "unknown").lower(),
                    "action": action,
                    "value": str(value) if value is not None else None,
                    "timestamp": datetime.now(UTC).isoformat()
                }).execute()

            logger.info(f"Updated device {device_id} status: active={is_active}, value={value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update device status: {e}")
            return False

    def update_control_unit_metrics(self, cpu_usage, memory_usage, storage_usage, uptime=None):
        """Update control unit metrics"""
        try:
            update_data = {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "storage_usage": storage_usage,
                "last_seen": datetime.now(UTC).isoformat()
            }

            if uptime:
                update_data["uptime"] = uptime

            self.supabase.table("control_units").update(
                update_data
            ).eq("id", self.control_unit_id).execute()

            logger.debug(
                f"Updated control unit metrics: CPU={cpu_usage}%, MEM={memory_usage}%, STORAGE={storage_usage}%")
            return True

        except Exception as e:
            logger.error(f"Failed to update control unit metrics: {e}")
            return False
