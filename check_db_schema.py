#!/usr/bin/env python3
import sqlite3
import json
from pathlib import Path

def check_database_schema():
    db_path = "services/audio/transcripts.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("=== DATABASE SCHEMA ===")
    print(f"Database: {db_path}")
    print(f"Size: {Path(db_path).stat().st_size / 1024 / 1024:.1f} MB")
    print()
    
    for table_name in tables:
        table = table_name[0]
        print(f"Table: {table}")
        print("-" * 40)
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"  {col[1]:20} {col[2]:15} {'NOT NULL' if col[3] else 'NULL'} {'PK' if col[5] else ''}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"\n  Total rows: {count}")
        
        # Sample data for transcripts table
        if table == 'transcripts':
            cursor.execute(f"SELECT id, audio_filename, created_at FROM {table} LIMIT 3")
            samples = cursor.fetchall()
            print(f"\n  Sample entries:")
            for sample in samples:
                print(f"    ID: {sample[0][:20]}..., File: {sample[1][:30] if sample[1] else 'None'}...")
        
        print()
    
    conn.close()
    
    # Check vector database
    vector_path = "services/audio/transcript_vectors"
    if Path(vector_path).exists():
        print("=== VECTOR DATABASE ===")
        print(f"Path: {vector_path}")
        print("ChromaDB collection present")

if __name__ == "__main__":
    check_database_schema()