#!/bin/bash

# Restore script for transcription database
# Usage: ./restore_database.sh [TIMESTAMP]

BACKUP_DIR="services/audio/backups"

if [ $# -eq 0 ]; then
    echo "Usage: $0 [TIMESTAMP]"
    echo ""
    echo "Available backups:"
    ls -lh "$BACKUP_DIR"/*.db 2>/dev/null
    ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null
    exit 1
fi

TIMESTAMP=$1

echo "=== Database Restore Script ==="
echo "Restoring from backup: ${TIMESTAMP}"

# Check if backup files exist
SQLITE_BACKUP="$BACKUP_DIR/transcripts_${TIMESTAMP}.db"
VECTOR_BACKUP="$BACKUP_DIR/transcript_vectors_${TIMESTAMP}.tar.gz"

if [ ! -f "$SQLITE_BACKUP" ]; then
    echo "✗ SQLite backup not found: $SQLITE_BACKUP"
    exit 1
fi

echo "Found backups to restore:"
[ -f "$SQLITE_BACKUP" ] && echo "  ✓ $SQLITE_BACKUP"
[ -f "$VECTOR_BACKUP" ] && echo "  ✓ $VECTOR_BACKUP"

# Confirm restore
echo ""
read -p "⚠️  This will overwrite current databases. Continue? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 1
fi

# Create safety backup of current state
SAFETY_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "Creating safety backup of current state..."
cp "services/audio/transcripts.db" "$BACKUP_DIR/transcripts_pre_restore_${SAFETY_TIMESTAMP}.db" 2>/dev/null

# Restore SQLite database
echo "Restoring SQLite database..."
cp "$SQLITE_BACKUP" "services/audio/transcripts.db"
echo "✓ SQLite database restored"

# Restore ChromaDB vector database if backup exists
if [ -f "$VECTOR_BACKUP" ]; then
    echo "Restoring ChromaDB vector database..."
    rm -rf "services/audio/transcript_vectors"
    tar -xzf "$VECTOR_BACKUP" -C "services/audio"
    echo "✓ Vector database restored"
else
    echo "⚠ No vector database backup found for this timestamp"
fi

echo ""
echo "Restore completed successfully!"
echo "Safety backup created: transcripts_pre_restore_${SAFETY_TIMESTAMP}.db"
echo ""
echo "Please restart the transcription service:"
echo "  cd services/audio && python transcription_server.py"