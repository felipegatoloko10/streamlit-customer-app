import google.generativeai as genai
import sys

key = "AIzaSyC_SCVLKePU9_UUJ1vUCZouclXITYm4J4A"
genai.configure(api_key=key)

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Oi, teste de conexão.")
    print(f"Sucesso: {response.text}")
except Exception as e:
    print(f"Erro: {e}")
