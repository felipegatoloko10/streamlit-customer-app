
import streamlit as st

# This file acts as a Singleton Proxy for the actual models definition.
# It ensures that models are defined ONLY ONCE per Streamlit server session,
# preventing "Table already defined" errors and Mapper Configuration issues on reloads.

@st.cache_resource
def get_models_module():
    """
    Imports and returns the models_src module.
    Because this function is cached with st.cache_resource,
    it executes only once. Subsequent calls return the same module object,
    preserving the identity of SQLModel classes and avoiding re-registration errors.
    """
    from sqlalchemy.orm import clear_mappers
    from sqlmodel import SQLModel
    from database_config import engine
    
    # Clear any existing mappers to avoid "Mapper already exists" errors on reload
    clear_mappers()
    
    # Reset metadata to avoid duplicate table definitions in memory
    SQLModel.metadata.clear()
    
    import models_src
    
    # Ensure tables exist. This is the best place because it runs once per session
    # and after models are defined.
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
