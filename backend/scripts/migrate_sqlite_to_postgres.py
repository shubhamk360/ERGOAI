import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from posture_detector.storage.models import Base

# Configuration
SQLITE_URL = "sqlite:///data/posture.db"
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://localhost/ergoai")

print(f"Migrating from {SQLITE_URL} to {POSTGRES_URL}")

# Engines
sqlite_engine = create_engine(SQLITE_URL)
postgres_engine = create_engine(POSTGRES_URL)

# Get all table metadata
tables = Base.metadata.sorted_tables

with postgres_engine.connect() as pg_conn:
    with sqlite_engine.connect() as sq_conn:
        for table in tables:
            table_name = table.name
            print(f"Migrating table: {table_name}")
            
            # Clear existing postgres data first
            pg_conn.execute(table.delete())
            pg_conn.commit()
            
            # Read from sqlite
            result = sq_conn.execute(table.select()).fetchall()
            
            if not result:
                print(f"  No data found in {table_name}, skipping.")
                continue
            
            print(f"  Found {len(result)} rows.")
            
            # Insert into postgres
            # using mapping to handle Row objects in sqlalchemy 2.0+
            pg_conn.execute(table.insert(), [row._mapping for row in result])
            pg_conn.commit()
            print(f"  Successfully inserted {len(result)} rows into {table_name}.")
            
            # Update sequence
            try:
                if 'id' in table.columns:
                    seq_name = f"{table_name}_id_seq"
                    pg_conn.execute(text(f"SELECT setval('{seq_name}', coalesce(max(id), 0) + 1, false) FROM {table_name};"))
                    pg_conn.commit()
                    print(f"  Updated sequence for {table_name}.")
            except Exception as e:
                print(f"  Warning: Could not update sequence for {table_name}: {e}")
                pg_conn.rollback()

print("Migration completed successfully!")
