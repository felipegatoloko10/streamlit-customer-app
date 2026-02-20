import google.generativeai as genai
import logging
import os
import time
import re
import datetime
from collections import deque

class BotIntelligence:
    """
    Handles interaction with Google Gemini API.
    Includes rate limiting (per-minute and per-day) and intelligent backoff.
    """

    # Limites do plano GRATUITO do Google AI
    MAX_CALLS_PER_MINUTE = 10   # limite real: 15/min, ficamos em 10 para segurança
    MAX_CALLS_PER_DAY = 150     # limite real: 200/dia (conservador: 150)

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = None

        # Rate limit: controle por minuto (janela deslizante)
        self._calls_timestamps = deque()  # timestamps das últimas chamadas

        # Rate limit: controle por dia
        self._daily_count = 0
        self._daily_reset_date = datetime.date.today()

        # Cooldown após 429 da API
        self._rate_limited_until = 0

        self.configure_model()

    def configure_model(self):
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                logging.info("✅ Gemini configurado com modelo gemini-2.0-flash")
            except Exception as e:
                logging.error(f"Failed to configure Gemini: {e}")

    def _reset_daily_if_needed(self):
        """Reseta contador diário à meia-noite."""
        today = datetime.date.today()
        if today != self._daily_reset_date:
            self._daily_count = 0
            self._daily_reset_date = today
            logging.info(f"🔄 Contador diário do Gemini resetado. Nova data: {today}")

    def _can_call_api(self):
        """
        Verifica limites antes de chamar a API.
        Retorna (pode_chamar: bool, motivo: str)
        """
        # 1. Cooldown ativo (erro 429 recente)
        wait_remaining = self._rate_limited_until - time.time()
        if wait_remaining > 0:
            return False, f"cooldown ativo por mais {wait_remaining:.0f}s"

        # 2. Limite diário
        self._reset_daily_if_needed()
        if self._daily_count >= self.MAX_CALLS_PER_DAY:
            return False, f"limite diário atingido ({self._daily_count}/{self.MAX_CALLS_PER_DAY} chamadas)"

        # 3. Limite por minuto (janela deslizante de 60s)
        now = time.time()
        # Remove timestamps com mais de 60 segundos
        while self._calls_timestamps and (now - self._calls_timestamps[0]) > 60:
            self._calls_timestamps.popleft()

        if len(self._calls_timestamps) >= self.MAX_CALLS_PER_MINUTE:
            oldest = self._calls_timestamps[0]
            wait = 60 - (now - oldest)
            return False, f"limite por minuto atingido ({len(self._calls_timestamps)}/{self.MAX_CALLS_PER_MINUTE}), aguardar {wait:.0f}s"

        return True, "ok"

    def _register_call(self):
        """Registra uma chamada bem-sucedida nos contadores."""
        self._calls_timestamps.append(time.time())
        self._daily_count += 1
        logging.info(
            f"📊 Gemini: {len(self._calls_timestamps)} calls/min | "
            f"{self._daily_count}/{self.MAX_CALLS_PER_DAY} calls/dia"
        )

    def get_usage_stats(self):
        """Retorna estatísticas de uso para o Dashboard."""
        self._reset_daily_if_needed()
        now = time.time()
        while self._calls_timestamps and (now - self._calls_timestamps[0]) > 60:
            self._calls_timestamps.popleft()
        return {
            "calls_per_minute": len(self._calls_timestamps),
            "max_per_minute": self.MAX_CALLS_PER_MINUTE,
            "calls_today": self._daily_count,
            "max_per_day": self.MAX_CALLS_PER_DAY,
            "cooldown_remaining": max(0, self._rate_limited_until - now),
        }

    def format_history_for_context(self, chat_history_list):
        """Formata histórico do chat para contexto do modelo."""
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

        # Verifica limites antes de chamar
        can_call, reason = self._can_call_api()
        if not can_call:
            logging.warning(f"⚠️ Gemini bloqueado: {reason}. Mensagem ignorada.")
            return None  # None = não responde ao cliente (evita spam)

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
            self._register_call()
            return response.text.strip()
        except Exception as e:
            error_str = str(e)
            logging.error(f"Erro na geração de resposta IA: {e}")

            # Rate limit da API (429 / RESOURCE_EXHAUSTED) → aplica cooldown
            if "429" in error_str or "quota" in error_str.lower() or "RESOURCE_EXHAUSTED" in error_str:
                match = re.search(r'retry_delay\s*\{\s*seconds:\s*(\d+)', error_str)
                wait_seconds = int(match.group(1)) if match else 60
                wait_seconds = max(wait_seconds, 60)
                self._rate_limited_until = time.time() + wait_seconds
                logging.warning(
                    f"🚫 Rate limit da API! Cooldown de {wait_seconds}s "
                    f"(até {time.strftime('%H:%M:%S', time.localtime(self._rate_limited_until))})"
                )
                return None  # Não manda mensagem de erro ao cliente

            return "Desculpe, tive um problema técnico. Um humano irá atendê-lo em breve."
