#!/bin/bash

# Backup script for transcription database before speaker detection migration
# Creates timestamped backups of both SQLite and ChromaDB vector database

BACKUP_DIR="services/audio/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== Database Backup Script ==="
echo "Creating backup directory if it doesn't exist..."
mkdir -p "$BACKUP_DIR"

# Backup SQLite database
echo "Backing up SQLite database..."
if [ -f "services/audio/transcripts.db" ]; then
    cp "services/audio/transcripts.db" "$BACKUP_DIR/transcripts_${TIMESTAMP}.db"
    echo "✓ SQLite backup created: $BACKUP_DIR/transcripts_${TIMESTAMP}.db"
    
    # Check backup size
    SIZE=$(du -h "$BACKUP_DIR/transcripts_${TIMESTAMP}.db" | cut -f1)
    echo "  Size: $SIZE"
else
    echo "✗ SQLite database not found!"
    exit 1
fi

# Backup ChromaDB vector database
echo "Backing up ChromaDB vector database..."
if [ -d "services/audio/transcript_vectors" ]; then
    tar -czf "$BACKUP_DIR/transcript_vectors_${TIMESTAMP}.tar.gz" -C "services/audio" "transcript_vectors"
    echo "✓ Vector DB backup created: $BACKUP_DIR/transcript_vectors_${TIMESTAMP}.tar.gz"
    
    # Check backup size
    SIZE=$(du -h "$BACKUP_DIR/transcript_vectors_${TIMESTAMP}.tar.gz" | cut -f1)
    echo "  Size: $SIZE"
else
    echo "⚠ Vector database not found (may be okay if using different storage)"
fi

# List all backups
echo ""
echo "=== All Backups ==="
ls -lh "$BACKUP_DIR"/*.db 2>/dev/null | tail -5
ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null | tail -5

echo ""
echo "Backup completed successfully!"
echo "To restore, use: ./restore_database.sh ${TIMESTAMP}"