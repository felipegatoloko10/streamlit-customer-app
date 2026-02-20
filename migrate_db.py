from sqlmodel import create_engine, text
import logging

DATABASE_URL = "postgresql+psycopg2://postgres.nayxxppiufxpdghtlgki:Tomati%402412@aws-0-us-west-2.pooler.supabase.com:5432/postgres?sslmode=require"
engine = create_engine(DATABASE_URL)

def migrate():
    with engine.connect() as conn:
        print("Checking chat_history table...")
        # Add external_id column if not exists
        try:
            conn.execute(text("ALTER TABLE chat_history ADD COLUMN external_id VARCHAR(255)"))
            conn.commit()
            print("Added external_id column.")
        except Exception as e:
            if "already exists" in str(e):
                print("Column external_id already exists.")
            else:
                print(f"Error adding column: {e}")
        
        # Add index
        try:
            conn.execute(text("CREATE INDEX ix_chat_history_external_id ON chat_history (external_id)"))
            conn.commit()
            print("Created index.")
        except Exception as e:
            if "already exists" in str(e):
                print("Index ix_chat_history_external_id already exists.")
            else:
                print(f"Error creating index: {e}")

if __name__ == "__main__":
    migrate()
