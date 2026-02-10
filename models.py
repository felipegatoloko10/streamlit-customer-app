
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
    # We must ensure models_src is imported fresh the first time, 
    # but since this function runs once, standard import is fine.
    # If the user edits models_src.py, they must clear cache or restart app.
    import models_src
    
    # Ensure tables exist. This is the best place because it runs once per session
    # and after models are defined.
    from database_config import create_db_and_tables
    create_db_and_tables()
    
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
