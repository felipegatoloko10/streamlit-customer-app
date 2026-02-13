
import streamlit as st
from sqlalchemy.orm import clear_mappers
from sqlmodel import SQLModel
from database_config import engine

# This file acts as a Singleton Proxy for the actual models definition.
# It ensures that models are defined safely per Streamlit server session.

@st.cache_resource
def get_models():
    """
    Imports models_src and ensures they are registered only once.
    Using clear_mappers() before import to ensure a clean state.
    """
    clear_mappers()
    
    # Reset metadata to avoid duplicate table definitions in memory
    # but keep the same registry if possible.
    import models_src
    
    # Ensure tables exist
    SQLModel.metadata.create_all(engine)
    
    return {
        "Cliente": models_src.Cliente,
        "Contato": models_src.Contato,
        "Endereco": models_src.Endereco,
        "AuditLog": models_src.AuditLog,
        "ClienteBase": models_src.ClienteBase,
        "ContatoBase": models_src.ContatoBase,
        "EnderecoBase": models_src.EnderecoBase,
        "ChatHistory": models_src.ChatHistory
    }

# Get the cached models dictionary
_m = get_models()

# Re-export all model classes
Cliente = _m["Cliente"]
Contato = _m["Contato"]
Endereco = _m["Endereco"]
AuditLog = _m["AuditLog"]
ClienteBase = _m["ClienteBase"]
ContatoBase = _m["ContatoBase"]
EnderecoBase = _m["EnderecoBase"]
ChatHistory = _m["ChatHistory"]
