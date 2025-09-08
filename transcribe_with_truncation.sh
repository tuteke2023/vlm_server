#!/bin/bash
# Batch transcription with automatic truncation for files >1 hour

API_URL="http://localhost:8001/transcribe"
AUDIO_DIR="/mnt/c/Users/tekee/Documents/Sound Recordings"
MAX_DURATION_SECONDS=3600  # 1 hour in seconds
TEMP_DIR="/tmp/audio_truncated"
COUNT=0

# Create temp directory for truncated files
mkdir -p "$TEMP_DIR"

echo "🎙️ Batch Transcription with 1-hour Truncation"
echo "📊 Using GPU-accelerated Whisper model"
echo "⏱️ Files >1 hour will be truncated"
echo "=================================="

# Function to get audio duration in seconds
get_duration() {
    local file="$1"
    ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$file" 2>/dev/null | cut -d. -f1
}

# Function to truncate audio file
truncate_audio() {
    local input="$1"
    local output="$2"
    local duration="$3"
    
    ffmpeg -i "$input" -t "$duration" -acodec copy -y "$output" 2>/dev/null
    return $?
}

# Get list of files not yet processed
TOTAL=$(find "$AUDIO_DIR" -name "*.m4a" | wc -l)
echo "Found $TOTAL total audio files"

# Check which files are already transcribed
echo "Checking for already transcribed files..."
TRANSCRIBED_COUNT=$(curl -s http://localhost:8001/transcripts | jq '. | length' 2>/dev/null || echo "0")
echo "Already transcribed: $TRANSCRIBED_COUNT files"
echo ""

# Process each file
for file in "$AUDIO_DIR"/*.m4a; do
    if [ -f "$file" ]; then
        COUNT=$((COUNT + 1))
        filename=$(basename "$file")
        filesize=$(du -h "$file" | cut -f1)
        
        echo "[$COUNT/$TOTAL] Processing: $filename ($filesize)"
        
        # Check if already transcribed (simple name check)
        EXISTS=$(curl -s http://localhost:8001/transcripts | jq -r ".[].filename" 2>/dev/null | grep -c "^$filename$" || echo "0")
        if [ "$EXISTS" -gt "0" ]; then
            echo "⏭️  Already transcribed, skipping..."
            continue
        fi
        
        # Get duration and check if truncation needed
        duration=$(get_duration "$file")
        file_to_process="$file"
        truncated=false
        
        if [ -n "$duration" ] && [ "$duration" -gt "$MAX_DURATION_SECONDS" ]; then
            duration_minutes=$((duration / 60))
            echo "  ⏱️  Duration: ${duration_minutes} minutes - truncating to 60 minutes..."
            
            # Create truncated version
            truncated_file="$TEMP_DIR/$(basename "$file")"
            if truncate_audio "$file" "$truncated_file" "$MAX_DURATION_SECONDS"; then
                file_to_process="$truncated_file"
                truncated=true
                echo "  ✂️  Truncated successfully"
            else
                echo "  ⚠️  Truncation failed, processing full file"
            fi
        elif [ -n "$duration" ]; then
            duration_minutes=$((duration / 60))
            echo "  ⏱️  Duration: ${duration_minutes} minutes - no truncation needed"
        fi
        
        # Prepare metadata
        METADATA="{\"filename\": \"$filename\", \"truncated\": $truncated, \"original_duration_seconds\": \"$duration\"}"
        
        # Transcribe using API
        response=$(curl -X POST "$API_URL" \
            -F "file=@$file_to_process" \
            -F "language=en" \
            -F "task=transcribe" \
            -F "metadata=$METADATA" \
            -s -w "\n%{http_code}")
        
        http_code=$(echo "$response" | tail -1)
        
        if [ "$http_code" = "200" ]; then
            echo "  ✅ Success - Transcribed and added to vector database"
            # Extract preview
            preview=$(echo "$response" | head -n -1 | jq -r '.transcription.text' 2>/dev/null | head -c 100)
            if [ -n "$preview" ]; then
                echo "  📝 Preview: ${preview}..."
            fi
        else
            echo "  ❌ Failed (HTTP $http_code)"
        fi
        
        # Clean up truncated file if created
        if [ "$truncated" = true ] && [ -f "$truncated_file" ]; then
            rm -f "$truncated_file"
        fi
        
        # Small delay between files
        sleep 2
    fi
done

# Clean up temp directory
rm -rf "$TEMP_DIR"

echo ""
echo "=================================="
echo "✨ Batch transcription complete!"
echo ""

# Check final stats
echo "📊 Final vector database stats:"
curl -s http://localhost:8001/vector/stats | jq .