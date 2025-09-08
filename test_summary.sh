#!/bin/bash

# Get Stanley search results
SEARCH_RESULT=$(curl -s -X POST "http://localhost:8001/transcripts/search" \
  -F "query=Stanley" \
  -F "n_results=3" | jq -r '.results[0].text' | head -c 500)

# Create context and ask for summary
QUESTION="CONVERSATION EXCERPTS:

[From ATOTekeStanleyOng.m4a]: $SEARCH_RESULT

Summarize these conversation excerpts. What are the main topics and key points discussed?"

# Send to Q&A
curl -s -X POST "http://localhost:8001/qa/ask" \
  -F "question=$QUESTION" \
  -F "max_context_length=1" \
  -F "n_chunks=1" | jq -r '.answer'
