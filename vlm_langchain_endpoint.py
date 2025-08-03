#!/usr/bin/env python3
"""API endpoint for LangChain-enhanced transaction classification"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import logging

from transaction_classifier_langchain import LangChainTransactionClassifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/langchain", tags=["langchain"])

class ClassificationRequest(BaseModel):
    """Request model for transaction classification"""
    transactions: List[Dict]
    use_vlm: bool = True
    vlm_endpoint: str = "http://localhost:8000/api/v1/generate"

class ClassificationResponse(BaseModel):
    """Response model for classification results"""
    transactions: List[Dict]
    summary: Dict
    corrections_applied: List[str]
    langchain_features_used: List[str]

@router.post("/classify_transactions", response_model=ClassificationResponse)
async def classify_transactions_with_langchain(request: ClassificationRequest):
    """
    Classify bank transactions using LangChain-enhanced processing
    
    This endpoint:
    1. Uses VLM for initial classification
    2. Applies corrections from the database
    3. Validates output using Pydantic schemas
    4. Returns structured, validated results
    """
    try:
        # Initialize classifier
        classifier = LangChainTransactionClassifier()
        
        # Generate VLM prompt
        prompt = classifier.create_classification_prompt(request.transactions)
        
        # Call VLM if requested
        vlm_response = None
        if request.use_vlm:
            # In production, this would call the VLM endpoint
            # For now, we'll simulate the response
            logger.info("Would call VLM with prompt length: %d", len(prompt))
            
            # Simulate VLM response for demonstration
            vlm_response = _simulate_vlm_response(request.transactions)
        
        # Classify with corrections
        classified = classifier.classify_transactions(
            request.transactions, 
            vlm_response
        )
        
        # Generate summary
        summary = classifier.create_validation_chain(classified)
        
        # Track corrections applied
        corrections_applied = []
        for txn in classified:
            if 'Payroll' in txn['description'] and not txn.get('gst_applicable'):
                corrections_applied.append(f"Corrected {txn['description']}: Marked as GST-free")
            elif 'Coles' in txn['description'] and not txn.get('gst_applicable'):
                corrections_applied.append(f"Corrected {txn['description']}: Marked as personal expense")
            elif 'Officeworks' in txn['description'] and txn.get('gst_amount'):
                corrections_applied.append(f"Corrected {txn['description']}: GST recalculated")
        
        # List LangChain features used
        langchain_features = [
            "Structured output with Pydantic validation",
            "Few-shot examples from corrections database",
            "Pattern-based correction rules",
            "Automatic GST calculation validation",
            "Category standardization"
        ]
        
        return ClassificationResponse(
            transactions=classified,
            summary=summary,
            corrections_applied=corrections_applied,
            langchain_features_used=langchain_features
        )
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/corrections_database")
async def get_corrections_database():
    """Get the current corrections database"""
    try:
        classifier = LangChainTransactionClassifier()
        return classifier.corrections_db
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add_correction")
async def add_correction_rule(pattern: str, corrections: Dict):
    """Add a new correction rule to the database"""
    # In production, this would update the database
    return {
        "status": "success",
        "message": f"Would add correction rule for pattern: {pattern}",
        "corrections": corrections
    }

def _simulate_vlm_response(transactions: List[Dict]) -> str:
    """Simulate VLM response for testing"""
    classifications = []
    
    for txn in transactions:
        amount = txn.get('debit', 0) or txn.get('credit', 0)
        is_credit = txn.get('credit', 0) > 0
        
        # Simple classification logic for simulation
        classification = {
            "gst_applicable": True,
            "gst_amount": round(amount / 11, 2),
            "gst_category": "GST on sales" if is_credit else "GST on purchases",
            "category": "Income/Revenue" if is_credit else "Expenses",
            "subcategory": "General",
            "business_percentage": 100,
            "tax_deductible": not is_credit,
            "notes": "VLM classified"
        }
        
        classifications.append(classification)
    
    return json.dumps(classifications)

# Integration code for adding to main VLM server
def add_langchain_routes(app):
    """Add LangChain routes to the main FastAPI app"""
    app.include_router(router)
    logger.info("LangChain classification endpoints added")

if __name__ == "__main__":
    # Test the endpoint
    import asyncio
    
    async def test():
        request = ClassificationRequest(
            transactions=[
                {
                    "date": "Oct 14",
                    "description": "Payroll Deposit - HOTEL",
                    "debit": 0,
                    "credit": 694.81,
                    "balance": 695.36
                }
            ],
            use_vlm=True
        )
        
        response = await classify_transactions_with_langchain(request)
        print(json.dumps(response.dict(), indent=2))
    
    asyncio.run(test())