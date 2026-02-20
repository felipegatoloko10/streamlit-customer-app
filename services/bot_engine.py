import time
import json
import logging
import os
import sys

# Add parent directory to path to import database and services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from services.evolution_service import EvolutionService
from services.bot_intelligence import BotIntelligence

# Configuration File Path
CONFIG_FILE = "bot_config.json"
LOG_FILE = "bot.log"

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading config: {e}")
    return {}

import threading

class BotRunner(threading.Thread):
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()
        self.daemon = True # Daemon thread ensuring it dies when main app dies
        
    def stop(self):
        self._stop_event.set()
        logging.info("Stopping Bot Engine...")

    def run(self):
        logging.info("Starting Bot Engine (Threaded)...")
        
        # Initialize Services (load config first to get keys)
        config = load_config()
        evolution_api_url = config.get("evolution_api_url")
        evolution_api_token = config.get("evolution_api_token")
        evolution_instance_name = config.get("evolution_instance_name", "cactvs")
        gemini_key = config.get("gemini_key")
        
        evolution_service = EvolutionService(evolution_api_url, evolution_api_token, instance_name=evolution_instance_name)
        bot_intelligence = BotIntelligence(gemini_key)

        while not self._stop_event.is_set():
            try:
                # Reload config every loop to check for changes (e.g. toggle ON/OFF)
                # In threaded mode, we might want to respect the toggle differently 
                # but reading from file is safe enough for low frequency.
                config = load_config()
                # If "bot_active" is false in config, we pause but don't kill thread
                is_active = config.get("bot_active", False)
                
                if not is_active:
                    logging.debug("Bot is inactive in config. Sleeping...")
                    time.sleep(5)
                    continue

                # Update service credentials if changed
                current_url = config.get("evolution_api_url")
                current_token = config.get("evolution_api_token")
                current_instance = config.get("evolution_instance_name", "cactvs")

                if current_url and current_url.rstrip('/') != evolution_service.base_url or \
                   current_token != evolution_service.api_token or \
                   current_instance != evolution_service.instance_name:
                    evolution_service = EvolutionService(current_url, current_token, instance_name=current_instance)
                
                if config.get("gemini_key") != bot_intelligence.api_key:
                    bot_intelligence = BotIntelligence(config.get("gemini_key"))
                
                # 1. Fetch recent messages
                data = evolution_service.get_recent_messages(count=10)
                
                # Evolution API v2 returns {"findMessages": {"messages": []}}
                # Evolution API v1 returns [] directly
                if isinstance(data, dict):
                    # Robust nested lookup for Evolution API v2 and v1
                    find_messages_obj = data.get("findMessages")
                    if isinstance(find_messages_obj, dict):
                        messages = find_messages_obj.get("messages", [])
                    else:
                        messages = data.get("messages", [])
                elif isinstance(data, list):
                    messages = data
                else:
                    messages = []
                
                # Ensure messages is a list of dicts
                if not isinstance(messages, list):
                    messages = []
                
                messages = [m for m in messages if isinstance(m, dict)]

                for msg in messages:
                    if self._stop_event.is_set(): break

                    # Structure of message depends on Evolution API version
                    key = msg.get("key", {})
                    remote_jid = key.get("remoteJid")
                    from_me = key.get("fromMe", False)
                    
                    # Check if it's a text message
                    message_content = msg.get("message", {})
                    text_content = message_content.get("conversation") or message_content.get("extendedTextMessage", {}).get("text")
                    
                    if not text_content or from_me:
                        continue 

                    phone_number = remote_jid.split("@")[0] if remote_jid else "unknown"

                    # Deduplication (Simple)
                    history = database.get_chat_history(phone_number, limit=1)
                    if history and history[-1]['parts'][0] == text_content and history[-1]['role'] == 'user':
                            continue

                    logging.info(f"Processing message from {phone_number}: {text_content}")

                    # 2. Save User Message to DB
                    database.save_chat_message(phone_number, "user", text_content)

                    # 3. Generate Reply
                    context_history = database.get_chat_history(phone_number, limit=10)
                    reply_text = bot_intelligence.generate_response(text_content, context_history)

                    # 4. Send Reply
                    if reply_text:
                        logging.info(f"Sending reply to {phone_number}: {reply_text}")
                        result = evolution_service.send_message(phone_number, reply_text)
                        
                        if result:
                            # 5. Save Bot Reply to DB
                            database.save_chat_message(phone_number, "model", reply_text)
                        else:
                            logging.error("Failed to send reply via API.")

                time.sleep(5) # Poll interval if active

            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                time.sleep(10)
        
        logging.info("Bot Engine Stopped.")

# Global instance manager for Streamlit
def get_bot_runner():
    # Helper to check if a thread is already running
    for thread in threading.enumerate():
        if isinstance(thread, BotRunner) and thread.is_alive():
            return thread
    return None

if __name__ == "__main__":
    # Standalone run
    runner = BotRunner()
    runner.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        runner.stop()
        runner.join()
