from uuid import UUID
from datetime import datetime

class SupabaseHandler:
    def __init__(self, supabase, controller_id):
        self.supabase = supabase
        try:
            self.controller_id = str(UUID(controller_id))
        except ValueError:
            raise ValueError(f"Invalid UUID format: {controller_id}")

    def get_controller_devices(self):
        response = self.supabase.table('control_units_devices')\
            .select('device_id, devices:device_id(*)')\
            .eq('control_unit_id', self.controller_id).execute()
        if response.error:
            print(f"Error fetching devices: {response.error.message}")
            return {}
        return {item['devices']['id']: item['devices'] for item in response.data if item['devices']}

    def update_controller_status(self, **status):
        self.supabase.table('control_units')\
            .update(status).eq('id', self.controller_id).execute()

    def update_device_value(self, device_id, value):
        self.supabase.table('devices')\
            .update({
                'value': value,
                'last_updated': datetime.utcnow().isoformat()
            }).eq('id', device_id).execute()

    async def subscribe_to_devices(self, callback):
        try:
            self.supabase.realtime.channel('device-changes')\
                .on('postgres_changes',
                    {'event': 'UPDATE', 'schema': 'public', 'table': 'devices'},
                    callback)\
                .subscribe()
        except NotImplementedError:
            print("Realtime features aren't available in the sync client.")

    def check_connection(self):
        try:
            self.supabase.table('control_units').select('id').limit(1).execute()
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def reconnect(self):
        print("Reconnecting to Supabase...")
        # Supabase client reconnection logic if necessary
