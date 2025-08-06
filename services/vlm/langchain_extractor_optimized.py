"""
LangChain-based Bank Statement Extractor - Optimized Version
Performance optimizations for faster extraction
"""

import logging
import re
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.schema import HumanMessage, SystemMessage
import json
from functools import lru_cache

logger = logging.getLogger(__name__)

# Pre-compile regex patterns for better performance
REGEX_PATTERNS = {
    'json_block': re.compile(r'\{.*\}', re.DOTALL),
    'trailing_comma_brace': re.compile(r',\s*\}'),
    'trailing_comma_bracket': re.compile(r',\s*\]'),
    'markdown_json': re.compile(r'```json\s*(.*?)\s*```', re.DOTALL),
    'markdown_block': re.compile(r'```\s*(.*?)\s*```', re.DOTALL),
    'calculation_expr': re.compile(r'"(total_debits|total_credits)"\s*:\s*([0-9.\s+\-*/]+)'),
    'currency_clean': re.compile(r'[$,]'),
}


# Pydantic models remain the same
class BankTransaction(BaseModel):
    """Individual bank transaction"""
    date: str = Field(description="Transaction date in YYYY-MM-DD format")
    description: str = Field(description="Transaction description")
    category: Optional[str] = Field(default="Other", description="Transaction category")
    debit: Optional[float] = Field(default=None, description="Debit amount (money out)")
    credit: Optional[float] = Field(default=None, description="Credit amount (money in)")
    balance: float = Field(description="Account balance after transaction")
    
    @field_validator('date')
    def validate_date(cls, v):
        """Ensure date is in correct format"""
        try:
            if '/' in v:
                parts = v.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            elif '-' in v:
                return v
            else:
                return v
        except:
            return v
    
    @field_validator('debit', 'credit', 'balance')
    def validate_amounts(cls, v):
        """Clean amount values"""
        if v is None:
            return None
        if isinstance(v, str):
            cleaned = REGEX_PATTERNS['currency_clean'].sub('', v)
            try:
                return float(cleaned)
            except:
                return None
        return float(v)


class BankStatement(BaseModel):
    """Complete bank statement"""
    bank_name: Optional[str] = Field(default=None, description="Name of the bank")
    account_number: Optional[str] = Field(default=None, description="Account number (masked)")
    statement_period: Optional[str] = Field(default=None, description="Statement period")
    transactions: List[BankTransaction] = Field(description="List of transactions")
    total_debits: Optional[float] = Field(default=None, description="Sum of all debits")
    total_credits: Optional[float] = Field(default=None, description="Sum of all credits")
    
    def calculate_totals(self):
        """Calculate total debits and credits"""
        self.total_debits = sum(t.debit for t in self.transactions if t.debit)
        self.total_credits = sum(t.credit for t in self.transactions if t.credit)


class LangChainExtractorOptimized:
    """
    Optimized Bank statement extractor using LangChain
    """
    
    def __init__(self, llm):
        """
        Initialize with a LangChain LLM
        
        Args:
            llm: LangChain LLM instance (UnifiedLangChainLLM)
        """
        self.llm = llm
        
        # Create output parser
        self.parser = PydanticOutputParser(pydantic_object=BankStatement)
        
        # Skip fixing parser for VLM - not worth the overhead
        self.fixing_parser = None
        
        # Cache the prompt template
        self.prompt_template = self._create_prompt_template()
        
        logger.info("LangChainExtractorOptimized initialized")
    
    @lru_cache(maxsize=1)
    def _create_prompt_template(self) -> PromptTemplate:
        """Create and cache the prompt template"""
        return PromptTemplate(
            template="""Extract bank transaction data from the provided bank statement image/text.

{format_instructions}

IMPORTANT RULES:
1. Extract ALL transactions visible in the statement
2. For dates, convert to YYYY-MM-DD format
3. For amounts, remove currency symbols and convert to float
4. Understanding Debits and Credits:
   - Debit = money LEAVING the account
   - Credit = money ENTERING the account
   - Direct Credit/Deposit/Transfer from = CREDIT
   - Direct Debit/Payment/Transfer to = DEBIT
5. Categories: Groceries, Restaurant, Gas Station, Shopping, Transfer, ATM, Online Purchase, Bill Payment, Salary, Other
6. Return actual calculated numeric values for totals, not formulas

Bank statement content:
{content}

Extract the data carefully and return in the specified JSON format.""",
            input_variables=["content"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    async def extract_bank_statement(
        self, 
        content: str,
        image_data: Optional[str] = None,
        use_fixing_parser: bool = False  # Ignored for optimization
    ) -> Dict[str, Any]:
        """
        Extract bank statement data using LangChain
        
        Args:
            content: Text content or description
            image_data: Optional base64 encoded image data
            use_fixing_parser: Ignored (always False for performance)
            
        Returns:
            Extracted bank statement data as dictionary
        """
        try:
            # Get response from LLM
            if image_data:
                messages = [
                    {
                        "role": "system",
                        "content": "You are a bank statement extraction expert. Extract transaction data accurately."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self.prompt_template.format(content=content)},
                            {"type": "image", "image": image_data}
                        ]
                    }
                ]
                
                llm_response = await self.llm.unified_provider.generate(
                    messages=messages,
                    temperature=0.1,
                    max_tokens=4000
                )
                response = llm_response.content
            else:
                formatted_prompt = self.prompt_template.format(content=content)
                response = await self.llm._acall(formatted_prompt)
            
            # For VLM, skip straight to manual JSON parsing
            # This saves ~5-10s by avoiding the Pydantic parser attempt
            try:
                result = await self._fast_json_parse(response)
                logger.info("Fast JSON parsing succeeded")
            except Exception as e:
                logger.warning(f"Fast JSON parsing failed: {e}")
                # Fallback to full manual parse
                result = await self._manual_json_parse(response)
            
            # Post-process to fix classifications
            result = self._fix_transaction_classifications(result)
            
            # Calculate totals
            result.calculate_totals()
            
            # Convert to dictionary
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"LangChain extraction failed: {e}")
            return {
                "bank_name": None,
                "account_number": None,
                "statement_period": None,
                "transactions": [],
                "total_debits": 0,
                "total_credits": 0,
                "error": str(e)
            }
    
    async def _fast_json_parse(self, response: str) -> BankStatement:
        """Fast JSON extraction optimized for VLM responses"""
        # Quick check for JSON markers
        if '```json' in response:
            match = REGEX_PATTERNS['markdown_json'].search(response)
            if match:
                json_str = match.group(1)
            else:
                raise ValueError("JSON block not found")
        elif '{' in response:
            match = REGEX_PATTERNS['json_block'].search(response)
            if match:
                json_str = match.group()
            else:
                raise ValueError("No JSON object found")
        else:
            raise ValueError("No JSON content detected")
        
        # Quick cleanup
        json_str = REGEX_PATTERNS['trailing_comma_brace'].sub('}', json_str)
        json_str = REGEX_PATTERNS['trailing_comma_bracket'].sub(']', json_str)
        
        # Parse JSON
        data = json.loads(json_str)
        
        # Quick fix for categories
        if 'transactions' in data:
            for txn in data['transactions']:
                if not txn.get('category'):
                    txn['category'] = 'Other'
        
        return BankStatement(**data)
    
    async def _manual_json_parse(self, response: str) -> BankStatement:
        """Full manual JSON extraction with all fixes"""
        try:
            cleaned = response.strip()
            
            # Remove markdown blocks
            if '```json' in cleaned:
                match = REGEX_PATTERNS['markdown_json'].search(cleaned)
                if match:
                    cleaned = match.group(1)
            elif '```' in cleaned:
                match = REGEX_PATTERNS['markdown_block'].search(cleaned)
                if match:
                    cleaned = match.group(1)
            
            # Find JSON
            json_match = REGEX_PATTERNS['json_block'].search(cleaned)
            if json_match:
                json_str = json_match.group()
                
                # Fix common issues
                json_str = REGEX_PATTERNS['trailing_comma_brace'].sub('}', json_str)
                json_str = REGEX_PATTERNS['trailing_comma_bracket'].sub(']', json_str)
                
                # Fix calculations
                def fix_calculations(match):
                    field_name = match.group(1)
                    expr = match.group(2)
                    try:
                        result = eval(expr, {"__builtins__": {}})
                        return f'"{field_name}": {result}'
                    except:
                        return match.group(0)
                
                json_str = REGEX_PATTERNS['calculation_expr'].sub(fix_calculations, json_str)
                
                # Parse JSON
                data = json.loads(json_str)
                
                # Fix data
                if 'transactions' in data:
                    for txn in data['transactions']:
                        if not txn.get('category'):
                            txn['category'] = 'Other'
                        
                        for field in ['debit', 'credit', 'balance']:
                            if field in txn and isinstance(txn[field], str):
                                try:
                                    txn[field] = float(REGEX_PATTERNS['currency_clean'].sub('', txn[field]))
                                except:
                                    txn[field] = None
                
                return BankStatement(**data)
            
            # If no JSON, try direct parse
            data = json.loads(cleaned)
            return BankStatement(**data)
            
        except Exception as e:
            logger.error(f"Manual JSON parse failed: {e}")
            return BankStatement(transactions=[])
    
    def _fix_transaction_classifications(self, statement: BankStatement) -> BankStatement:
        """Fix common debit/credit misclassifications"""
        for txn in statement.transactions:
            desc_lower = txn.description.lower()
            
            # Skip balance entries
            if any(term in desc_lower for term in ['opening balance', 'closing balance', 'beginning balance']):
                txn.debit = None
                txn.credit = None
                continue
            
            # Fix known patterns
            if any(term in desc_lower for term in ['direct credit', 'deposit', 'transfer from', 'received', 'refund', 'salary', 'payroll']):
                if txn.debit and not txn.credit:
                    txn.credit = txn.debit
                    txn.debit = None
            elif any(term in desc_lower for term in ['direct debit', 'payment', 'purchase', 'transfer to', 'withdrawal', 'fee', 'charge']):
                if txn.credit and not txn.debit:
                    txn.debit = txn.credit
                    txn.credit = None
            
            # Ensure only one is set
            if txn.debit and txn.credit:
                if any(term in desc_lower for term in ['credit', 'deposit', 'from', 'received']):
                    txn.debit = None
                else:
                    txn.credit = None
        
        return statement