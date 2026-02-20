import google.generativeai as genai
import logging
import os
import time
import re

class BotIntelligence:
    """
    Handles interaction with Google Gemini API for intelligent responses.
    """
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = None
        self._rate_limited_until = 0  # timestamp até quando aguardar (rate limit)
        self.configure_model()

    def configure_model(self):
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash')
            except Exception as e:
                logging.error(f"Failed to configure Gemini: {e}")

    def format_history_for_context(self, chat_history_list):
        """
        Formats the list of chat messages (dicts) into a string for the model.
        Expects history items to have 'role' ('user' or 'model') and 'parts' (list of text).
        """
        formatted = ""
        for msg in chat_history_list:
            role = "Cliente" if msg.get("role") == "user" else "Assistente"
            parts = msg.get("parts", [])
            content = " ".join(parts) if isinstance(parts, list) else str(parts)
            formatted += f"{role}: {content}\n"
        return formatted

    def generate_response(self, user_message, chat_history_list=None):
        if not self.model:
            if self.api_key:
                self.configure_model()
            if not self.model:
                return "Erro: Chave API do Gemini não configurada ou inválida."

        # Verifica cooldown de rate limit
        wait_remaining = self._rate_limited_until - time.time()
        if wait_remaining > 0:
            logging.warning(f"⏳ Gemini em cooldown por mais {wait_remaining:.0f}s. Mensagem não enviada.")
            return None  # None = bot não responde (evita spam ao cliente e gasto de cota)

        context_str = self.format_history_for_context(chat_history_list or [])

        system_prompt = """
        Você é um assistente virtual presencial (recepcionista) da empresa.
        Seu tom é profissional, acolhedor e eficiente.

        Diretrizes:
        1. Responda apenas o que for perguntado ou necessário para o atendimento.
        2. Se não souber a resposta, peça para o cliente aguardar um atendente humano.
        3. Não invente informações sobre produtos ou preços que não estão no contexto.
        4. Mantenha as respostas curtas e objetivas, adequadas para WhatsApp.

        Contexto da conversa anterior:
        """

        prompt = f"{system_prompt}\n{context_str}\n\nCliente: {user_message}\nAssistente:"

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            error_str = str(e)
            logging.error(f"Erro na geração de resposta IA: {e}")

            # Detecta rate limit (429) e aplica cooldown inteligente
            if "429" in error_str or "quota" in error_str.lower() or "RESOURCE_EXHAUSTED" in error_str:
                # Extrai retry_delay da mensagem de erro
                match = re.search(r'retry_delay\s*\{\s*seconds:\s*(\d+)', error_str)
                wait_seconds = int(match.group(1)) if match else 60
                wait_seconds = max(wait_seconds, 60)  # mínimo 60 segundos
                self._rate_limited_until = time.time() + wait_seconds
                logging.warning(
                    f"🚫 Rate limit atingido! Gemini pausado por {wait_seconds}s "
                    f"(até {time.strftime('%H:%M:%S', time.localtime(self._rate_limited_until))})"
                )
                return None  # Não manda mensagem de erro ao cliente

            return "Desculpe, tive um problema técnico. Um humano irá atendê-lo em breve."
