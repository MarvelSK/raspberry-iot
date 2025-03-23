import threading
import logging
import json
from config import logger, SUPABASE_URL, SUPABASE_KEY, CONTROL_UNIT_ID
import websocket


class RealtimeManager:
    def __init__(self, on_device_update):
        """Initialize the realtime listener for Supabase

        Args:
            on_device_update: Callback function to handle device updates
        """
        self.on_device_update = on_device_update
        self.ws = None
        self.connected = False
        self.stop_requested = False
        self.thread = None

        # Create access token for Supabase Realtime
        # This is a simplified version - in a production app you'd generate a proper JWT
        self.access_token = SUPABASE_KEY

        logger.info("Realtime manager initialized")

    def start(self):
        """Start the realtime listener in a separate thread"""
        if self.thread and self.thread.is_alive():
            logger.warning("Realtime manager already running")
            return

        self.stop_requested = False
        self.thread = threading.Thread(target=self._connect_and_listen)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Realtime manager thread started")

    def stop(self):
        """Stop the realtime listener"""
        self.stop_requested = True
        if self.ws:
            self.ws.close()
        logger.info("Realtime manager stopping")

    def _connect_and_listen(self):
        """Connect to Supabase Realtime and listen for changes"""
        realtime_url = SUPABASE_URL.replace('https://', 'wss://').replace('.supabase.co',
                                                                          '.supabase.co/realtime/v1/websocket')
        realtime_url += f"?apikey={self.access_token}"

        websocket.enableTrace(logger.level <= logging.DEBUG)

        def on_message(ws, message):
            """Process realtime message from Supabase"""
            try:
                data = json.loads(message)

                event = data.get('event')
                schema = data.get('schema')
                table = data.get('table')

                # Check if 'schema' is present and valid
                if not schema or schema != 'public' or table != 'devices':
                    logger.warning(f"Invalid or missing schema/table in message: {data}")
                    return  # Skip processing

                # Handle different events
                if event == 'INSERT':
                    logger.info(f"New device detected: {data['record']['id']}")
                    self.on_device_update('device_created', data['record'])

                elif event == 'UPDATE':
                    logger.info(f"Device updated: {data['record']['id']}")
                    self.on_device_update('device_updated', data['record'])

                elif event == 'DELETE':
                    logger.info(f"Device deleted: {data['old_record']['id']}")
                    self.on_device_update('device_deleted', data['old_record'])

                else:
                    logger.warning(f"Unhandled event type: {event}")

            except json.JSONDecodeError:
                logger.error("Failed to parse realtime message")
            except Exception as e:
                logger.error(f"Error processing realtime message: {e}")

        def on_error(ws, error):
            logger.error(f"Realtime connection error: {error}")
            self.connected = False

        def on_close(ws, close_status_code, close_msg):
            logger.info(f"Realtime connection closed: {close_msg} ({close_status_code})")
            self.connected = False

            # Reconnect unless stop was requested
            if not self.stop_requested:
                logger.info("Attempting to reconnect in 5 seconds...")
                time.sleep(5)
                self._connect_and_listen()

        def on_open(ws):
            logger.info("Realtime connection established")
            self.connected = True

            # Subscribe to device changes for our control unit
            subscription_msg = {
                "topic": f"realtime:public:devices:controller_id=eq.{CONTROL_UNIT_ID}",
                "event": "phx_join",
                "payload": {},
                "ref": "1"
            }
            ws.send(json.dumps(subscription_msg))
            logger.info(f"Subscribed to device changes for control unit {CONTROL_UNIT_ID}")

        self.ws = websocket.WebSocketApp(
            realtime_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )

        try:
            # This will block until the connection is closed
            self.ws.run_forever()
        except Exception as e:
            logger.error(f"Error in realtime websocket: {e}")
            self.connected = False