import threading
import logging
import json
import time
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

        # Use Supabase API key as access token
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
            self.ws.close()  # Close WebSocket connection
            logger.info("WebSocket connection closed.")
        if self.thread:
            self.thread.join()  # Ensure the thread has finished
        logger.info("Realtime manager stopped.")

    def _connect_and_listen(self):
        """Connect to Supabase Realtime and listen for device changes"""
        realtime_url = SUPABASE_URL.replace(
            "https://", "wss://"
        ).replace(".supabase.co", ".supabase.co/realtime/v1/websocket")
        realtime_url += f"?apikey={self.access_token}"

        websocket.enableTrace(logger.level <= logging.DEBUG)

        def on_message(ws, message):
            try:
                data = json.loads(message)
                event = data.get("event")
                topic = data.get("topic")
                payload = data.get("payload", {})

                if event in {"INSERT", "UPDATE", "DELETE"}:
                    record = payload.get("record") if event != "DELETE" else payload.get("old_record")
                    if record:
                        logger.info(f"Device {event.lower()}: {record.get('id')}")
                        self.on_device_update(f"device_{event.lower()}", record)
                    else:
                        logger.warning(f"Record missing in {event} event: {data}")

                elif event in {"phx_reply", "system", "presence_state"}:
                    logger.debug(f"Control message: {data}")

                else:
                    logger.warning(f"Unhandled message: {data}")

            except json.JSONDecodeError:
                logger.error("Failed to decode realtime message")
            except Exception as e:
                logger.error(f"Error processing message: {e}")

        def on_error(ws, error):
            logger.error(f"Realtime connection error: {error}")
            self.connected = False

        def on_close(ws, close_status_code, close_msg):
            logger.info(f"Realtime connection closed: {close_msg} (Code: {close_status_code})")
            self.connected = False

            if not self.stop_requested:
                retry_delay = 5
                attempt = 0
                while not self.stop_requested and attempt < 5:
                    attempt += 1
                    logger.info(f"Reconnecting in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    self._connect_and_listen()

        def on_open(ws):
            logger.info("Realtime connection established")
            self.connected = True

            # Send a ping message every 30 seconds to keep the connection alive
            def send_ping():
                while self.connected:
                    time.sleep(30)
                    if self.ws:
                        self.ws.send(json.dumps({"event": "ping"}))
                        logger.debug("Ping sent to keep connection alive")

            threading.Thread(target=send_ping, daemon=True).start()

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
            on_close=on_close,
        )

        try:
            self.ws.run_forever()
        except Exception as e:
            logger.error(f"Error in websocket connection: {e}")
            self.connected = False