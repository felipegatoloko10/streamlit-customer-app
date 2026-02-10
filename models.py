
import streamlit as st
import importlib
from sqlalchemy.orm import clear_mappers
from sqlmodel import SQLModel
from database_config import engine

# This file acts as a Singleton Proxy for the actual models definition.
# It ensures that models are defined safely per Streamlit server session.

@st.cache_resource
def get_models_module():
    """
    Initializes and returns the models_src module.
    We clear mappers and reload the module to ensure that SQLModel classes
    are correctly registered with the current metadata and registry.
    """
    # Clear any existing mappers to avoid conflicts across reloads
    clear_mappers()
    
    # Import and reload the source module to re-register classes
    import models_src
    importlib.reload(models_src)
    
    # Ensure tables exist
    SQLModel.metadata.create_all(engine)
    
    return models_src

# Get the cached module
_models = get_models_module()

# Re-export all model classes so other files can import from 'models' normally
ClienteBase = _models.ClienteBase
Cliente = _models.Cliente
ContatoBase = _models.ContatoBase
Contato = _models.Contato
EnderecoBase = _models.EnderecoBase
Endereco = _models.Endereco
AuditLog = _models.AuditLog
