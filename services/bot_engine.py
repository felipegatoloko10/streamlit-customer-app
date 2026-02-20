import time
import json
import logging
import os
import sys
import threading

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
        evolution_instance_name = config.get("evolution_instance_name", "BotFeh")
        gemini_key = config.get("gemini_key")
        
        evolution_service = EvolutionService(evolution_api_url, evolution_api_token, instance_name=evolution_instance_name)
        bot_intelligence = BotIntelligence(gemini_key)

        while not self._stop_event.is_set():
            try:
                # Reload config every loop to check for changes
                config = load_config()
                is_active = config.get("bot_active", False)
                
                if not is_active:
                    logging.info("Bot is inactive in config. Sleeping...")
                    time.sleep(5)
                    continue

                # Update service credentials if changed
                current_url = config.get("evolution_api_url", "").strip()
                current_token = config.get("evolution_api_token", "").strip()
                current_instance = config.get("evolution_instance_name", "BotFeh").strip()

                if current_url and current_url.rstrip('/') != evolution_service.base_url or \
                   current_token != evolution_service.api_token or \
                   current_instance != evolution_service.instance_name:
                    evolution_service = EvolutionService(current_url, current_token, instance_name=current_instance)
                
                if config.get("gemini_key") != bot_intelligence.api_key:
                    bot_intelligence = BotIntelligence(config.get("gemini_key"))

                # --- 1. Self-Diagnostics ---
                # Check instance connection
                is_connected, conn_msg = evolution_service.check_connection()
                if not is_connected:
                    logging.info(f"⚠️ ATENCAO: Instancia '{evolution_service.instance_name}' NAO ESTA CONECTADA. {conn_msg}")
                    # Try to derive the IP for the QR scan link
                    server_ip = evolution_service.base_url.split('//')[-1].split(':')[0]
                    logging.info(f"👉 Por favor, acesse http://{server_ip} e escaneie o QR Code.")
                    time.sleep(10)
                    continue

                # Check Gemini Key
                if not bot_intelligence.api_key:
                    logging.info("⚠️ ATENCAO: Chave API do Gemini esta FALTANDO. O bot nao conseguira responder.")
                    # We don't continue because we want to at least log messages, but it won't reply.

                # 2. Fetch recent messages
                url_debug = f"{evolution_service.base_url}/chat/findMessages/{evolution_service.instance_name}"
                logging.info(f"Polling URL: {url_debug}")
                data = evolution_service.get_recent_messages(count=10)
                
                if not data and not isinstance(data, (dict, list)):
                    logging.debug(f"Polled {url_debug} but got empty/null response")
                
                # DEBUG: Log the keys in the response to help diagnosis in Dashboard
                if isinstance(data, dict):
                    logging.info(f"Response keys: {list(data.keys())}")
                    # Log first item of messages if present
                    raw_msgs = data.get('messages', data.get('data', []))
                    if isinstance(raw_msgs, list):
                        logging.info(f"Total de mensagens brutas na resposta: {len(raw_msgs)}")
                        if raw_msgs:
                            import json as _json
                            logging.info(f"Primeira mensagem (bruta): {_json.dumps(raw_msgs[0], default=str)[:500]}")
                elif isinstance(data, list):
                    logging.info(f"Response is a list of {len(data)} items.")
                    if data:
                        import json as _json
                        logging.info(f"Primeiro item: {_json.dumps(data[0], default=str)[:500]}")

                # Evolution API v2.3.0 real structure:
                # {"messages": {"total": N, "pages": N, "currentPage": N, "records": [...]}}
                if isinstance(data, dict):
                    messages_val = data.get("messages") or data.get("findMessages") or data.get("data")
                    if isinstance(messages_val, dict):
                        # v2.3.0 paginado: records é a lista real
                        messages = messages_val.get("records") or messages_val.get("messages") or []
                        logging.info(f"Estrutura paginada detectada. Total na API: {messages_val.get('total', '?')}, registros nesta pagina: {len(messages)}")
                    elif isinstance(messages_val, list):
                        messages = messages_val
                    else:
                        messages = []
                elif isinstance(data, list):
                    messages = data
                else:
                    messages = []
                
                if not isinstance(messages, list):
                    messages = []
                
                messages = [m for m in messages if isinstance(m, dict)]
                
                # Filtrar apenas mensagens RECENTES (últimos 120 segundos)
                # A API retorna histórico completo; sem filtro de tempo, reprocessa tudo
                import time as _time
                now_ts = _time.time()
                WINDOW_SECONDS = 120  # só processa mensagens dos últimos 2 minutos
                recent_messages = []
                for m in messages:
                    msg_ts = m.get("messageTimestamp") or m.get("timestamp")
                    if msg_ts:
                        try:
                            msg_ts = int(msg_ts)
                            if (now_ts - msg_ts) <= WINDOW_SECONDS:
                                recent_messages.append(m)
                        except (ValueError, TypeError):
                            pass  # ignora mensagem sem timestamp válido
                
                logging.info(f"Mensagens válidas para processar: {len(recent_messages)} (de {len(messages)} recentes na página, janela={WINDOW_SECONDS}s)")
                
                for msg in recent_messages:
                    if self._stop_event.is_set(): break

                    # Metadata Extraction
                    key = msg.get("key", {})
                    message_id = key.get("id")
                    remote_jid = key.get("remoteJid")
                    from_me = key.get("fromMe", False)
                    phone_number = remote_jid.split("@")[0] if remote_jid else "unknown"

                    if from_me:
                        continue
                    
                    # Deduplication (using Message ID)
                    if message_id and database.check_message_exists(message_id):
                        logging.debug(f"Message {message_id} already processed. Skipping.")
                        continue
                    
                    # Content Extraction
                    message_content = msg.get("message", {})
                    text_content = message_content.get("conversation") or \
                                  message_content.get("extendedTextMessage", {}).get("text")
                    
                    if not text_content:
                        text_content = message_content.get("text") or \
                                      msg.get("content", {}).get("text")
                    
                    if not text_content:
                        continue

                    logging.info(f"Processing message {message_id} from {phone_number}: {text_content[:50]}...")

                    try:
                        # 4. Save User Message to DB
                        database.save_chat_message(phone_number, "user", text_content, external_id=message_id)

                        # 5. Generate Reply
                        if not bot_intelligence.api_key:
                            reply_text = "Erro: Chave Gemini não configurada no Dashboard."
                        else:
                            context_history = database.get_chat_history(phone_number, limit=10)
                            reply_text = bot_intelligence.generate_response(text_content, context_history)

                        # 6. Send Reply
                        if reply_text:
                            logging.info(f"Sending reply to {phone_number}: {reply_text[:50]}...")
                            result = evolution_service.send_message(remote_jid, reply_text)
                            
                            if result:
                                # 7. Save Bot Reply to DB
                                database.save_chat_message(phone_number, "model", reply_text)
                            else:
                                logging.error(f"Failed to send reply to {phone_number} via API.")
                    except Exception as loop_e:
                        logging.error(f"Error processing single message {message_id}: {loop_e}")

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
    runner = BotRunner()
    runner.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        runner.stop()
        runner.join()
