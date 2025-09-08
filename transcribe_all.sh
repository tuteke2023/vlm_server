#!/bin/bash
# Direct batch transcription using curl

API_URL="http://localhost:8001/transcribe"
AUDIO_DIR="/mnt/c/Users/tekee/Documents/Sound Recordings"
COUNT=0
TOTAL=$(find "$AUDIO_DIR" -name "*.m4a" | wc -l)

echo "🎙️ Starting batch transcription of $TOTAL files"
echo "📊 Using GPU-accelerated Whisper model"
echo "=================================="

# Loop through all m4a files
for file in "$AUDIO_DIR"/*.m4a; do
    if [ -f "$file" ]; then
        COUNT=$((COUNT + 1))
        filename=$(basename "$file")
        filesize=$(du -h "$file" | cut -f1)
        
        echo ""
        echo "[$COUNT/$TOTAL] Processing: $filename ($filesize)"
        
        # Transcribe using API
        response=$(curl -X POST "$API_URL" \
            -F "file=@$file" \
            -F "language=en" \
            -F "task=transcribe" \
            -F "metadata={\"filename\": \"$filename\"}" \
            -s -w "\n%{http_code}")
        
        http_code=$(echo "$response" | tail -1)
        
        if [ "$http_code" = "200" ]; then
            echo "✅ Success - Transcribed and added to vector database"
            # Extract preview from response
            preview=$(echo "$response" | head -n -1 | jq -r '.transcription.text' 2>/dev/null | head -c 100)
            if [ -n "$preview" ]; then
                echo "📝 Preview: ${preview}..."
            fi
        else
            echo "❌ Failed (HTTP $http_code)"
        fi
        
        # Small delay between files
        sleep 2
    fi
done

echo ""
echo "=================================="
echo "✨ Batch transcription complete!"
echo ""

# Check final stats
echo "📊 Checking vector database stats..."
curl -s http://localhost:8001/vector/stats | jq .