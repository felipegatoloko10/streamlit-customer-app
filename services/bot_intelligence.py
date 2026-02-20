import google.generativeai as genai
import logging
import os

class BotIntelligence:
    """
    Handles interaction with Google Gemini API for intelligent responses.
    """
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = None
        self.configure_model()

    def configure_model(self):
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Using gemini-pro or gemini-1.5-flash if available/preferred
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e:
                logging.error(f"Failed to configure Gemini: {e}")

    def format_history_for_context(self, chat_history_list):
        """
        Formats the list of chat messages (dicts) into a string or list for the model.
        Expects history items to have 'role' ('user' or 'model') and 'parts' (list of text).
        """
        formatted = ""
        for msg in chat_history_list:
            role = "Cliente" if msg.get("role") == "user" else "Assistente"
            content = " ".join(msg.get("parts", [])) if isinstance(msg.get("parts"), list) else str(msg.get("parts", ""))
            formatted += f"{role}: {content}\n"
        return formatted

    def generate_response(self, user_message, chat_history_list=None):
        if not self.model:
            if self.api_key: 
                self.configure_model() # Try to reconfigure if key was set later
            
            if not self.model:
                return "Erro: Chave API do Gemini não configurada ou inválida."

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
            logging.error(f"Erro na geração de resposta IA: {e}")
            return "Desculpe, tive um problema técnico. Um humano irá atendê-lo em breve."
