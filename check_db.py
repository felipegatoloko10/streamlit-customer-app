from sqlmodel import create_engine, text

DATABASE_URL = "postgresql+psycopg2://postgres.nayxxppiufxpdghtlgki:Tomati%402412@aws-0-us-west-2.pooler.supabase.com:5432/postgres?sslmode=require"
engine = create_engine(DATABASE_URL)

def count_records():
    with engine.connect() as conn:
        print("Counting records in chat_history...")
        result = conn.execute(text("SELECT COUNT(*) FROM chat_history")).scalar()
        print(f"Total messages: {result}")
        
        print("\nLast 5 records (if any):")
        result = conn.execute(text("SELECT role, SUBSTRING(content, 1, 30) as content, timestamp FROM chat_history ORDER BY timestamp DESC LIMIT 5"))
        for row in result:
            print(f"- [{row.timestamp}] {row.role}: {row.content}")

if __name__ == "__main__":
    count_records()
