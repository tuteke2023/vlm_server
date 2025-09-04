# Speaker Detection Migration Plan

## Current Database Status

### SQLite Database (transcripts.db - 4.9 MB)
- **Table**: `transcripts`
- **Rows**: 66 transcripts
- **Key columns**: 
  - `id` (TEXT, Primary Key)
  - `audio_filename` (TEXT) 
  - `content` (TEXT, NOT NULL) - Full transcript text
  - `segments` (TEXT) - JSON array of timestamped segments
  - `metadata` (TEXT) - Additional metadata
  - `created_at`, `updated_at` (TIMESTAMP)

### Vector Database (ChromaDB)
- **Path**: `services/audio/transcript_vectors/`
- **Documents**: 1,133 chunks from 257 transcripts
- **Used for**: Semantic search and Q&A

## Migration Options

### Option 1: Preserve Existing + Add Speaker Detection for New (RECOMMENDED)
**What happens to existing database:**
- All 66 existing transcripts remain unchanged
- No re-processing required
- No downtime
- New transcripts get speaker detection automatically

**Implementation:**
1. Add new column: `speaker_segments` (JSON) to store speaker-labeled segments
2. Keep original `segments` column for backward compatibility
3. New transcripts populate both columns
4. UI can detect which format to use

**Pros:**
- ✅ No data loss or re-processing
- ✅ Instant deployment
- ✅ Backward compatible
- ✅ Low risk

**Cons:**
- ⚠️ Two different transcript formats in DB
- ⚠️ Old transcripts won't have speaker labels

### Option 2: Gradual Re-processing
**What happens to existing database:**
- Existing transcripts stay as-is initially
- Background job re-processes them one by one
- Database gradually upgrades

**Implementation:**
1. Add `speaker_segments` column
2. Add `processing_version` column (1.0 for old, 2.0 for speaker-detected)
3. Background script processes old transcripts when idle

**Pros:**
- ✅ Eventually all transcripts have speakers
- ✅ No immediate downtime
- ✅ Can prioritize important files

**Cons:**
- ⚠️ Requires original audio files
- ⚠️ Takes time (hours/days depending on GPU)
- ⚠️ More complex implementation

### Option 3: Full Re-processing
**What happens to existing database:**
- Backup current database
- Re-process all 66 audio files with speaker detection
- Replace old transcripts

**Pros:**
- ✅ Consistent format across all transcripts
- ✅ Best quality results

**Cons:**
- ❌ Requires all original audio files
- ❌ Significant downtime (2-3 hours)
- ❌ Risk of data loss if audio files missing

## Database Schema Changes

```sql
-- Add speaker detection columns
ALTER TABLE transcripts ADD COLUMN speaker_segments TEXT;
ALTER TABLE transcripts ADD COLUMN speaker_count INTEGER DEFAULT 2;
ALTER TABLE transcripts ADD COLUMN processing_version TEXT DEFAULT '1.0';

-- Index for version tracking
CREATE INDEX idx_processing_version ON transcripts(processing_version);
```

## Implementation Steps (Option 1 - Recommended)

### Step 1: Backup Current Database
```bash
cp services/audio/transcripts.db services/audio/transcripts_backup_$(date +%Y%m%d).db
cp -r services/audio/transcript_vectors services/audio/transcript_vectors_backup_$(date +%Y%m%d)
```

### Step 2: Update Database Schema
```python
# In migration script
def add_speaker_columns():
    conn = sqlite3.connect('transcripts.db')
    cursor = conn.cursor()
    
    # Add new columns
    cursor.execute("ALTER TABLE transcripts ADD COLUMN speaker_segments TEXT")
    cursor.execute("ALTER TABLE transcripts ADD COLUMN speaker_count INTEGER DEFAULT 2")
    cursor.execute("ALTER TABLE transcripts ADD COLUMN processing_version TEXT DEFAULT '1.0'")
    
    # Mark existing transcripts as v1.0
    cursor.execute("UPDATE transcripts SET processing_version = '1.0' WHERE processing_version IS NULL")
    
    conn.commit()
    conn.close()
```

### Step 3: Update Transcription Service
Integrate `PracticalSpeakerDetection` class into the transcription pipeline:
```python
# In transcription_server.py
def transcribe_with_speakers(audio_file):
    # Regular Whisper transcription
    segments = whisper_transcribe(audio_file)
    
    # Apply speaker detection
    detector = PracticalSpeakerDetection()
    speaker_segments, speaker_count = detector.detect_speakers_simple(segments)
    
    # Store both formats
    return {
        "segments": segments,  # Original format
        "speaker_segments": speaker_segments,  # New format with speakers
        "speaker_count": speaker_count
    }
```

### Step 4: Update UI to Handle Both Formats
```javascript
// In search.html
function displayTranscript(transcript) {
    if (transcript.speaker_segments) {
        // New format with speakers
        displayWithSpeakers(transcript.speaker_segments);
    } else {
        // Old format without speakers
        displayPlainTranscript(transcript.segments);
    }
}
```

## Testing Plan

1. **Backup verification**: Ensure backups are complete
2. **Schema update**: Test on copy of database first
3. **New transcription**: Test with 2-speaker and 3-speaker audio files
4. **UI compatibility**: Verify both old and new transcripts display correctly
5. **Search functionality**: Ensure vector search still works

## Rollback Plan

If issues arise:
1. Stop transcription service
2. Restore database backup:
```bash
mv services/audio/transcripts.db services/audio/transcripts_failed.db
cp services/audio/transcripts_backup_[date].db services/audio/transcripts.db
```
3. Restore vector database:
```bash
rm -rf services/audio/transcript_vectors
cp -r services/audio/transcript_vectors_backup_[date] services/audio/transcript_vectors
```
4. Restart services

## Summary

**For your existing 66 transcripts:**
- They will remain untouched and fully functional
- No re-processing needed immediately
- Can be gradually upgraded later if desired

**For new transcripts:**
- Automatic speaker detection (2-3+ speakers)
- Better action item tracking
- Improved summaries with speaker context

**Migration time:** ~30 minutes including backup and testing
**Risk level:** Low with Option 1
**Downtime:** None required