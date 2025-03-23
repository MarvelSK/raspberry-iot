from supabase import create_client, Client
import logging
import time
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
        logger.info(f"Initialized Supabase client for control unit: {self.control_unit_id}")

    def connect(self):
        """Update control unit status to online and fetch initial data"""
        try:
            self.supabase.table("control_units").update({
                "is_online": True,
                "last_seen": "now()",
                "cpu_usage": 0,
                "memory_usage": 0,
                "storage_usage": 0
            }).eq("id", self.control_unit_id).execute()

            logger.info(f"Control unit {self.control_unit_id} is now online")
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Update control unit status to offline"""
        if not self.connected:
            return

        try:
            self.supabase.table("control_units").update({
                "is_online": False,
                "last_seen": "now()"
            }).eq("id", self.control_unit_id).execute()

            logger.info(f"Control unit {self.control_unit_id} is now offline")
            self.connected = False
        except Exception as e:
            logger.error(f"Failed to update offline status: {e}")

    def get_devices(self):
        """Fetch devices linked to this control unit via control_units_devices table"""
        try:
            response = self.supabase.table("control_units_devices").select(
                "device_id, devices(*)"
            ).eq("control_unit_id", self.control_unit_id).execute()

            if response.data:
                devices = [item["devices"] for item in response.data if item["devices"]]
                logger.info(f"Retrieved {len(devices)} devices for control unit {self.control_unit_id}")
                return devices
            else:
                logger.warning(f"No devices found for control unit {self.control_unit_id}")
                return []

        except Exception as e:
            logger.error(f"Failed to fetch devices: {e}")
            return []

    def update_device_status(self, device_id, is_active=None, value=None):
        """Update device status in Supabase and log the action"""
        try:
            update_data = {"last_updated": "now()"}
            if is_active is not None:
                update_data["is_active"] = is_active
            if value is not None:
                update_data["value"] = value

            response = self.supabase.table("devices").update(
                update_data
            ).eq("id", device_id).execute()

            device_data = response.data[0] if response.data else None
            if device_data:
                action = f"turned {'on' if is_active else 'off'}" if is_active is not None else ""
                if value is not None:
                    action += f" with value {value}" if action else f"value set to {value}"

                self.supabase.table("activity_log").insert({
                    "device_name": device_data.get("name", "Unknown"),
                    "device_type": device_data.get("type", "unknown").lower(),
                    "action": action,
                    "value": str(value) if value is not None else None,
                    "timestamp": "now()"
                }).execute()

            logger.info(f"Updated device {device_id}: active={is_active}, value={value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update device {device_id} status: {e}")
            return False

    def update_control_unit_metrics(self, cpu_usage, memory_usage, storage_usage, uptime=None):
        """Update control unit metrics in Supabase"""
        try:
            update_data = {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "storage_usage": storage_usage,
                "last_seen": "now()"
            }
            if uptime:
                update_data["uptime"] = uptime

            self.supabase.table("control_units").update(
                update_data
            ).eq("id", self.control_unit_id).execute()

            logger.debug(f"Updated control unit metrics: CPU={cpu_usage}%, MEM={memory_usage}%, STORAGE={storage_usage}%")
            return True

        except Exception as e:
            logger.error(f"Failed to update control unit metrics: {e}")
            return False
