#!/usr/bin/env python3
"""
Database migration script for adding speaker detection support
Adds new columns while preserving all existing data
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def migrate_database():
    """Add speaker detection columns to existing database"""
    
    db_path = "services/audio/transcripts.db"
    
    # Check if database exists
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    print("=== Starting Database Migration ===")
    print(f"Database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(transcripts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        changes_made = False
        
        # Add speaker_segments column if not exists
        if 'speaker_segments' not in columns:
            print("Adding column: speaker_segments...")
            cursor.execute("ALTER TABLE transcripts ADD COLUMN speaker_segments TEXT")
            changes_made = True
            print("✓ Added speaker_segments column")
        else:
            print("✓ speaker_segments column already exists")
        
        # Add speaker_count column if not exists  
        if 'speaker_count' not in columns:
            print("Adding column: speaker_count...")
            cursor.execute("ALTER TABLE transcripts ADD COLUMN speaker_count INTEGER DEFAULT 2")
            changes_made = True
            print("✓ Added speaker_count column")
        else:
            print("✓ speaker_count column already exists")
        
        # Add processing_version column if not exists
        if 'processing_version' not in columns:
            print("Adding column: processing_version...")
            cursor.execute("ALTER TABLE transcripts ADD COLUMN processing_version TEXT DEFAULT '1.0'")
            changes_made = True
            print("✓ Added processing_version column")
        else:
            print("✓ processing_version column already exists")
        
        # Mark all existing transcripts as version 1.0
        if changes_made:
            print("Marking existing transcripts as version 1.0...")
            cursor.execute("UPDATE transcripts SET processing_version = '1.0' WHERE processing_version IS NULL")
            updated = cursor.rowcount
            print(f"✓ Updated {updated} existing transcripts to version 1.0")
        
        # Create index for version tracking
        print("Creating index for processing_version...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processing_version ON transcripts(processing_version)")
        print("✓ Index created/verified")
        
        # Commit changes
        conn.commit()
        
        # Show summary
        print("\n=== Migration Summary ===")
        cursor.execute("SELECT COUNT(*) FROM transcripts")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transcripts WHERE processing_version = '1.0'")
        v1_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transcripts WHERE processing_version = '2.0'")
        v2_count = cursor.fetchone()[0]
        
        print(f"Total transcripts: {total}")
        print(f"Version 1.0 (without speakers): {v1_count}")
        print(f"Version 2.0 (with speakers): {v2_count}")
        
        conn.close()
        
        print("\n✅ Migration completed successfully!")
        print("Existing transcripts preserved as version 1.0")
        print("New transcripts will be created as version 2.0 with speaker detection")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    if not success:
        print("\n⚠️  Migration failed. You can restore the backup using:")
        print("   ./restore_database.sh [TIMESTAMP]")