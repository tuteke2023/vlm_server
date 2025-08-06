"""
LangChain-based Bank Statement Extractor
Increment 4: Structured extraction using LangChain
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.schema import HumanMessage, SystemMessage
import json
import re

logger = logging.getLogger(__name__)


# Pydantic models for structured output
class BankTransaction(BaseModel):
    """Individual bank transaction"""
    date: str = Field(description="Transaction date in YYYY-MM-DD format")
    description: str = Field(description="Transaction description")
    category: Optional[str] = Field(default="Other", description="Transaction category (e.g., Groceries, Restaurant, Transfer)")
    debit: Optional[float] = Field(default=None, description="Debit amount (money out)")
    credit: Optional[float] = Field(default=None, description="Credit amount (money in)")
    balance: float = Field(description="Account balance after transaction")
    
    @field_validator('date')
    def validate_date(cls, v):
        """Ensure date is in correct format"""
        try:
            # Try to parse the date
            if '/' in v:
                # Handle MM/DD/YYYY format
                parts = v.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    # Convert to YYYY-MM-DD
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            elif '-' in v:
                # Already in correct format
                return v
            else:
                # Try to parse other formats
                return v
        except:
            return v
    
    @field_validator('debit', 'credit', 'balance')
    def validate_amounts(cls, v):
        """Clean amount values"""
        if v is None:
            return None
        if isinstance(v, str):
            # Remove currency symbols and commas
            cleaned = re.sub(r'[$,]', '', v)
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


class LangChainExtractor:
    """
    Bank statement extractor using LangChain
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
        
        # Create fixing parser for error recovery (only if LLM is a proper LangChain LLM)
        try:
            self.fixing_parser = OutputFixingParser.from_llm(
                parser=self.parser,
                llm=self.llm
            )
        except Exception as e:
            logger.warning(f"Could not create fixing parser: {e}")
            self.fixing_parser = None
        
        # Create extraction prompt
        self.prompt_template = PromptTemplate(
            template="""Extract bank transaction data from the provided bank statement image/text.

{format_instructions}

IMPORTANT RULES:
1. Extract ALL transactions visible in the statement
2. For dates, convert to YYYY-MM-DD format
3. For amounts, remove currency symbols and convert to float
4. Understanding Debits and Credits:
   - Debit = money LEAVING the account (withdrawals, purchases, transfers out)
   - Credit = money ENTERING the account (deposits, salary, transfers in)
   - "Direct Credit" or "Credit" in description = CREDIT transaction
   - "Direct Debit" or "Debit" in description = DEBIT transaction
   - "Transfer to" = DEBIT (money going out)
   - "Transfer from" = CREDIT (money coming in)
   - "Payment", "Purchase", "Withdrawal" = DEBIT
   - "Deposit", "Received", "Refund" = CREDIT
5. If a transaction shows in "Withdrawals" column, it's a debit
6. If a transaction shows in "Deposits" column, it's a credit
7. Opening Balance is NOT a transaction - skip it or set both debit and credit to null
8. Balance should reflect the running balance after each transaction
9. Assign appropriate categories based on transaction descriptions
10. If bank name or account info is visible, include it (mask sensitive parts)

Common categories: Groceries, Restaurant, Gas Station, Shopping, Transfer, ATM, Online Purchase, Bill Payment, Salary, Other

Bank statement content:
{content}

Extract the data carefully and return in the specified JSON format.

IMPORTANT: For total_debits and total_credits, provide the actual calculated numeric value, not a formula.
For example: "total_debits": 303.38 (not "1500.00 + 67.89 + ...")""",
            input_variables=["content"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        logger.info("LangChainExtractor initialized")
    
    async def extract_bank_statement(
        self, 
        content: str,
        image_data: Optional[str] = None,
        use_fixing_parser: bool = True
    ) -> Dict[str, Any]:
        """
        Extract bank statement data using LangChain
        
        Args:
            content: Text content or description of the bank statement
            image_data: Optional base64 encoded image data
            use_fixing_parser: Whether to use the fixing parser for error recovery
            
        Returns:
            Extracted bank statement data as dictionary
        """
        try:
            # If we have image data, create a multimodal prompt
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
                
                # Use the unified provider directly for multimodal
                llm_response = await self.llm.unified_provider.generate(
                    messages=messages,
                    temperature=0.1,
                    max_tokens=4000
                )
                response = llm_response.content
            else:
                # Text-only extraction
                formatted_prompt = self.prompt_template.format(content=content)
                response = await self.llm._acall(formatted_prompt)
            
            # Parse the response
            try:
                # Try regular parser first
                result = self.parser.parse(response)
            except Exception as e:
                logger.warning(f"Initial parsing failed: {e}")
                # Try manual JSON extraction as primary fallback
                try:
                    result = await self._manual_json_parse(response)
                    logger.info("Manual JSON parsing succeeded")
                except Exception as e2:
                    logger.warning(f"Manual parsing failed: {e2}")
                    # Try fixing parser as last resort if available
                    if use_fixing_parser and self.fixing_parser:
                        try:
                            result = await self._async_fixing_parse(response)
                            logger.info("Fixing parser succeeded")
                        except Exception as e3:
                            logger.error(f"All parsing methods failed: {e3}")
                            raise
            
            # Post-process to fix common classification errors
            result = self._fix_transaction_classifications(result)
            
            # Calculate totals
            result.calculate_totals()
            
            # Convert to dictionary
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"LangChain extraction failed: {e}")
            # Return empty result on failure
            return {
                "bank_name": None,
                "account_number": None,
                "statement_period": None,
                "transactions": [],
                "total_debits": 0,
                "total_credits": 0,
                "error": str(e)
            }
    
    async def _async_fixing_parse(self, response: str) -> BankStatement:
        """Async wrapper for fixing parser"""
        # The fixing parser might need async support
        # For now, we'll try to fix common issues manually
        
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                return BankStatement(**data)
        except:
            pass
        
        # If that fails, try the fixing parser if available
        if self.fixing_parser:
            return self.fixing_parser.parse(response)
        else:
            raise ValueError("Could not parse response")
    
    async def _manual_json_parse(self, response: str) -> BankStatement:
        """Manually extract JSON from response"""
        try:
            # Remove markdown code block markers if present
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                
                # Fix common JSON issues
                # 1. Remove trailing commas before closing braces/brackets
                json_str = re.sub(r',\s*\}', '}', json_str)
                json_str = re.sub(r',\s*\]', ']', json_str)
                
                # 2. Fix calculation expressions in total_debits and total_credits
                def fix_calculations(match):
                    field_name = match.group(1)
                    expr = match.group(2)
                    try:
                        # Safely evaluate the arithmetic expression
                        result = eval(expr, {"__builtins__": {}})
                        return f'"{field_name}": {result}'
                    except Exception as e:
                        logger.warning(f"Failed to evaluate {field_name} expression: {expr}, error: {e}")
                        return match.group(0)
                
                json_str = re.sub(r'"(total_debits|total_credits)"\s*:\s*([0-9.\s+\-*/]+)', fix_calculations, json_str)
                
                # Parse JSON
                data = json.loads(json_str)
                
                # 3. Ensure all transactions have valid categories
                if 'transactions' in data and data['transactions']:
                    for txn in data['transactions']:
                        # Fix category field
                        if 'category' not in txn or txn['category'] is None or txn['category'] == '':
                            txn['category'] = 'Other'
                        
                        # Ensure numeric fields are proper types
                        for field in ['debit', 'credit', 'balance']:
                            if field in txn and isinstance(txn[field], str):
                                try:
                                    txn[field] = float(txn[field].replace('$', '').replace(',', ''))
                                except:
                                    txn[field] = None
                
                # Create BankStatement object
                statement = BankStatement(**data)
                logger.info(f"Manual JSON parsing succeeded with {len(statement.transactions)} transactions")
                return statement
            
            # If no JSON found, try to parse as direct JSON
            data = json.loads(cleaned)
            return BankStatement(**data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error at position {e.pos}: {e.msg}")
            logger.debug(f"Failed JSON preview: ...{json_str[max(0, e.pos-50):e.pos+50]}...")
            # Return empty statement
            return BankStatement(transactions=[])
        except Exception as e:
            logger.error(f"Manual JSON parse failed: {e}")
            # Return empty statement
            return BankStatement(transactions=[])
    
    def extract_from_table_format(self, table_text: str) -> Dict[str, Any]:
        """
        Fallback method to extract from table format
        Compatible with existing bank_parser_v3.py logic
        """
        try:
            lines = table_text.strip().split('\n')
            transactions = []
            
            for line in lines:
                # Skip header lines
                if any(header in line.lower() for header in ['date', 'description', 'withdrawals', 'deposits', 'balance']):
                    continue
                
                # Try pipe-delimited format
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 5:
                        date, desc, withdrawals, deposits, balance = parts[:5]
                        
                        # Parse amounts
                        debit = self._parse_amount(withdrawals) if withdrawals else None
                        credit = self._parse_amount(deposits) if deposits else None
                        balance_amt = self._parse_amount(balance)
                        
                        if date and desc and balance_amt is not None:
                            transaction = BankTransaction(
                                date=date,
                                description=desc,
                                category=self._categorize_transaction(desc),
                                debit=debit,
                                credit=credit,
                                balance=balance_amt
                            )
                            transactions.append(transaction)
            
            # Create bank statement
            statement = BankStatement(transactions=transactions)
            statement.calculate_totals()
            
            return statement.model_dump()
            
        except Exception as e:
            logger.error(f"Table format extraction failed: {e}")
            return {
                "transactions": [],
                "error": str(e)
            }
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float"""
        if not amount_str or amount_str.strip() in ['-', '']:
            return None
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[$,]', '', amount_str.strip())
        
        try:
            return float(cleaned)
        except:
            return None
    
    def _categorize_transaction(self, description: str) -> str:
        """Categorize transaction based on description"""
        desc_lower = description.lower()
        
        # Category mapping
        categories = {
            'grocery': ['grocery', 'supermarket', 'market', 'food'],
            'restaurant': ['restaurant', 'cafe', 'coffee', 'pizza', 'burger'],
            'gas': ['gas', 'fuel', 'petrol', 'shell', 'exxon'],
            'shopping': ['amazon', 'walmart', 'target', 'store', 'shop'],
            'transfer': ['transfer', 'wire', 'zelle', 'venmo'],
            'atm': ['atm', 'cash', 'withdrawal'],
            'bill': ['bill', 'utility', 'electric', 'water', 'internet'],
            'salary': ['salary', 'payroll', 'direct deposit']
        }
        
        for category, keywords in categories.items():
            if any(keyword in desc_lower for keyword in keywords):
                return category.title()
        
        return 'Other'
    
    def _fix_transaction_classifications(self, statement: BankStatement) -> BankStatement:
        """Fix common debit/credit misclassifications based on transaction descriptions"""
        for txn in statement.transactions:
            desc_lower = txn.description.lower()
            
            # Skip opening/closing balance
            if any(term in desc_lower for term in ['opening balance', 'closing balance', 'beginning balance']):
                txn.debit = None
                txn.credit = None
                continue
            
            # Force credit for known credit patterns
            if any(term in desc_lower for term in ['direct credit', 'deposit', 'transfer from', 'received', 'refund', 'salary', 'payroll']):
                if txn.debit and not txn.credit:
                    # Move debit to credit
                    txn.credit = txn.debit
                    txn.debit = None
            
            # Force debit for known debit patterns
            elif any(term in desc_lower for term in ['direct debit', 'payment', 'purchase', 'transfer to', 'withdrawal', 'fee', 'charge']):
                if txn.credit and not txn.debit:
                    # Move credit to debit
                    txn.debit = txn.credit
                    txn.credit = None
            
            # Ensure only one of debit/credit is set (not both)
            if txn.debit and txn.credit:
                # If both are set, determine based on description
                if any(term in desc_lower for term in ['credit', 'deposit', 'from', 'received']):
                    txn.debit = None
                else:
                    txn.credit = None
        
        return statement