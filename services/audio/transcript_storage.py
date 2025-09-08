#!/usr/bin/env python3
"""Transcript Storage Module for Audio Service"""

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TranscriptStorage:
    """Handle storage and retrieval of audio transcripts"""
    
    def __init__(self, db_path: str = "transcripts.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create transcripts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transcripts (
                    id TEXT PRIMARY KEY,
                    audio_filename TEXT,
                    content TEXT NOT NULL,
                    language TEXT,
                    segments TEXT,  -- JSON array of segments with timestamps
                    metadata TEXT,  -- JSON object with additional metadata
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON transcripts(created_at DESC)
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def save_transcript(
        self,
        content: str,
        audio_filename: Optional[str] = None,
        language: Optional[str] = None,
        segments: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None,
        speaker_segments: Optional[List[Dict]] = None,
        speaker_count: int = 2,
        processing_version: str = "1.0"
    ) -> str:
        """Save a transcript to the database"""
        transcript_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if new columns exist
            cursor.execute("PRAGMA table_info(transcripts)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'speaker_segments' in columns:
                # Use new schema with speaker detection
                cursor.execute("""
                    INSERT INTO transcripts (
                        id, audio_filename, content, language, segments, metadata,
                        speaker_segments, speaker_count, processing_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transcript_id,
                    audio_filename,
                    content,
                    language,
                    json.dumps(segments) if segments else None,
                    json.dumps(metadata) if metadata else None,
                    json.dumps(speaker_segments) if speaker_segments else None,
                    speaker_count,
                    processing_version
                ))
            else:
                # Use old schema (backward compatibility)
                cursor.execute("""
                    INSERT INTO transcripts (
                        id, audio_filename, content, language, segments, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    transcript_id,
                    audio_filename,
                    content,
                    language,
                    json.dumps(segments) if segments else None,
                    json.dumps(metadata) if metadata else None
                ))
            
            conn.commit()
            
        logger.info(f"Saved transcript {transcript_id} (version {processing_version})")
        return transcript_id
    
    def get_transcript(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a transcript by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM transcripts WHERE id = ?
            """, (transcript_id,))
            
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                # Parse JSON fields
                if result.get('segments'):
                    result['segments'] = json.loads(result['segments'])
                if result.get('metadata'):
                    result['metadata'] = json.loads(result['metadata'])
                # Parse new speaker fields if they exist
                if result.get('speaker_segments'):
                    result['speaker_segments'] = json.loads(result['speaker_segments'])
                return result
            
            return None
    
    def list_transcripts(
        self, 
        limit: int = 10, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List recent transcripts"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, audio_filename, 
                       substr(content, 1, 100) as preview,
                       language, created_at
                FROM transcripts
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def search_transcripts(self, query: str) -> List[Dict[str, Any]]:
        """Search transcripts by content"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, audio_filename,
                       substr(content, 1, 200) as preview,
                       language, created_at
                FROM transcripts
                WHERE content LIKE ?
                ORDER BY created_at DESC
                LIMIT 20
            """, (f"%{query}%",))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_transcript(self, transcript_id: str) -> bool:
        """Delete a transcript"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM transcripts WHERE id = ?
            """, (transcript_id,))
            
            conn.commit()
            
            return cursor.rowcount > 0
    
    def get_segments_at_time(
        self, 
        transcript_id: str, 
        timestamp: float
    ) -> Optional[Dict[str, Any]]:
        """Get the segment at a specific timestamp"""
        transcript = self.get_transcript(transcript_id)
        
        if not transcript or not transcript.get('segments'):
            return None
        
        for segment in transcript['segments']:
            if segment['start'] <= timestamp <= segment['end']:
                return segment
        
        return None
    
    def extract_time_range(
        self,
        transcript_id: str,
        start_time: float,
        end_time: float
    ) -> str:
        """Extract text from a specific time range"""
        transcript = self.get_transcript(transcript_id)
        
        if not transcript or not transcript.get('segments'):
            return ""
        
        extracted_text = []
        for segment in transcript['segments']:
            if segment['start'] >= start_time and segment['end'] <= end_time:
                extracted_text.append(segment['text'])
            elif segment['start'] < end_time and segment['end'] > start_time:
                # Partial overlap
                extracted_text.append(segment['text'])
        
        return " ".join(extracted_text)