"""
Improved Bank Statement Parser using LangChain for structured output
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
import csv
import io
import json
from decimal import Decimal
import logging
import re

logger = logging.getLogger(__name__)


class BankTransaction(BaseModel):
    """Model for a single bank transaction"""
    date: str = Field(description="Transaction date in MM/DD/YYYY or DD/MM/YYYY format")
    description: str = Field(description="Transaction description or merchant name")
    category: Optional[str] = Field(default=None, description="Transaction category")
    debit: Optional[float] = Field(default=0.0, description="Debit amount (positive number)")
    credit: Optional[float] = Field(default=0.0, description="Credit amount (positive number)")
    balance: Optional[float] = Field(default=0.0, description="Account balance after transaction")
    
    @validator('debit', 'credit', 'balance')
    def validate_amounts(cls, v):
        """Ensure amounts are positive numbers"""
        if v is None:
            return 0.0
        return abs(float(v))
    
    @validator('date')
    def validate_date(cls, v):
        """Validate and normalize date format"""
        if not v:
            return ""
        
        # Try to parse common date formats
        date_formats = [
            "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d",
            "%m-%d-%Y", "%d-%m-%Y", "%Y/%m/%d",
            "%m/%d/%y", "%d/%m/%y"
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(v.strip(), fmt)
                # Return in consistent MM/DD/YYYY format
                return parsed_date.strftime("%m/%d/%Y")
            except ValueError:
                continue
        
        # If no format matches, return original
        return v
    
    @validator('category', pre=False, always=True)
    def auto_categorize(cls, v, values):
        """Auto-categorize based on description if not provided"""
        if v:
            return v
            
        description = values.get('description', '').lower()
        
        # Category mapping with more specific keywords
        categories = {
            'Groceries': ['grocery', 'food', 'market', 'supermarket', 'walmart', 'kroger', 'safeway'],
            'Transportation': ['gas station', 'fuel', 'petrol', 'uber', 'lyft', 'taxi', 'parking', 'shell', 'chevron', 'exxon'],
            'Dining': ['restaurant', 'cafe', 'coffee', 'dining', 'pizza', 'food', 'mcdonald', 'starbucks'],
            'Shopping': ['amazon', 'online', 'ebay', 'store', 'purchase', 'shop'],
            'Utilities': ['utility', 'electric', 'water bill', 'gas bill', 'internet', 'phone', 'bill payment'],
            'Housing': ['rent', 'mortgage', 'lease', 'housing'],
            'Income': ['salary', 'payroll', 'wage', 'deposit', 'direct deposit', 'income'],
            'Transfer': ['transfer', 'payment', 'zelle', 'venmo', 'savings'],
            'Healthcare': ['pharmacy', 'doctor', 'medical', 'hospital', 'cvs', 'walgreens'],
            'Entertainment': ['movie', 'netflix', 'spotify', 'game', 'subscription'],
            'Banking': ['service fee', 'bank fee', 'overdraft', 'interest', 'atm fee'],
            'Cash': ['atm withdrawal', 'cash withdrawal', 'atm']
        }
        
        # Check for income first (credits usually)
        if values.get('credit', 0) > 0 and values.get('debit', 0) == 0:
            if any(keyword in description for keyword in ['salary', 'payroll', 'wage', 'deposit']):
                return 'Income'
        
        # Check other categories
        for category, keywords in categories.items():
            if any(keyword in description for keyword in keywords):
                return category
            
        return "Other"


class BankStatement(BaseModel):
    """Model for a complete bank statement"""
    account_number: Optional[str] = Field(default="", description="Account number if available")
    statement_period: Optional[str] = Field(default="", description="Statement period")
    transactions: List[BankTransaction] = Field(description="List of all transactions")
    total_debits: Optional[float] = Field(default=0.0, description="Sum of all debits")
    total_credits: Optional[float] = Field(default=0.0, description="Sum of all credits")
    opening_balance: Optional[float] = Field(default=0.0, description="Opening balance")
    closing_balance: Optional[float] = Field(default=0.0, description="Closing balance")
    
    def calculate_totals(self):
        """Calculate total debits and credits"""
        self.total_debits = sum(t.debit for t in self.transactions)
        self.total_credits = sum(t.credit for t in self.transactions)
        return self
    
    def to_csv(self) -> str:
        """Convert transactions to CSV format"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Date', 'Description', 'Category', 'Debit', 'Credit', 'Balance'])
        
        # Write transactions
        for trans in self.transactions:
            writer.writerow([
                trans.date,
                trans.description,
                trans.category,
                f"{trans.debit:.2f}" if trans.debit > 0 else "",
                f"{trans.credit:.2f}" if trans.credit > 0 else "",
                f"{trans.balance:.2f}" if trans.balance > 0 else ""
            ])
        
        # Write summary
        writer.writerow([])  # Empty row
        writer.writerow(['Summary', '', '', '', '', ''])
        writer.writerow(['Total Debits', '', '', f"{self.total_debits:.2f}", '', ''])
        writer.writerow(['Total Credits', '', '', '', f"{self.total_credits:.2f}", ''])
        if self.opening_balance:
            writer.writerow(['Opening Balance', '', '', '', '', f"{self.opening_balance:.2f}"])
        if self.closing_balance:
            writer.writerow(['Closing Balance', '', '', '', '', f"{self.closing_balance:.2f}"])
        
        return output.getvalue()
    
    def to_json_pretty(self) -> str:
        """Convert to formatted JSON"""
        return json.dumps(self.dict(), indent=2, default=str)


class BankStatementParser:
    """Parser for extracting structured bank statement data"""
    
    def __init__(self):
        self.parser = PydanticOutputParser(pydantic_object=BankStatement)
        
        # Create prompt template with format instructions
        self.prompt_template = PromptTemplate(
            template="""Analyze the following bank statement and extract transaction data.

{format_instructions}

Important rules:
1. Extract ALL transactions found in the document
2. Use positive numbers for both debits and credits
3. Debits are withdrawals/expenses (money going out)
4. Credits are deposits/income (money coming in)
5. Include the running balance if available
6. Auto-categorize transactions based on description

Bank Statement:
{bank_statement}

{format_instructions}

Extracted Data:""",
            input_variables=["bank_statement"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    def parse(self, ai_response: str) -> BankStatement:
        """Parse AI response into structured format"""
        logger.info(f"Parsing AI response of length: {len(ai_response)}")
        logger.debug(f"First 500 chars of response: {ai_response[:500]}")
        
        try:
            # Try to parse the response directly
            logger.info("Attempting direct LangChain parse...")
            bank_statement = self.parser.parse(ai_response)
            bank_statement.calculate_totals()
            logger.info(f"Direct parse successful: {len(bank_statement.transactions)} transactions")
            return bank_statement
        except Exception as e:
            logger.warning(f"Direct parse failed: {e}")
            
            # If parsing fails, try to extract JSON from the response
            logger.info("Attempting JSON extraction...")
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    bank_statement = BankStatement(**data)
                    bank_statement.calculate_totals()
                    logger.info(f"JSON parse successful: {len(bank_statement.transactions)} transactions")
                    return bank_statement
                except Exception as je:
                    logger.warning(f"JSON parse failed: {je}")
            
            # If JSON parsing fails, try to parse table format manually
            logger.info("Attempting improved table format parse...")
            bank_statement = self.parse_table_format_v2(ai_response)
            if bank_statement.transactions:
                bank_statement.calculate_totals()
                logger.info(f"Table parse successful: {len(bank_statement.transactions)} transactions")
                return bank_statement
            
            # If all else fails, return empty statement
            logger.warning("All parsing methods failed, returning empty statement")
            return BankStatement(transactions=[])
    
    def parse_table_format_v2(self, text: str) -> BankStatement:
        """Improved table format parser"""
        transactions = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Look for date pattern
            date_pattern = r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}'
            date_match = re.search(date_pattern, line)
            
            if date_match:
                # Found a potential transaction line
                trans_data = {
                    'date': date_match.group(),
                    'description': '',
                    'debit': 0,
                    'credit': 0,
                    'balance': 0
                }
                
                # Extract the rest of the line after the date
                date_end = date_match.end()
                remaining = line[date_end:].strip()
                
                # Find all money amounts (with dollar signs)
                money_pattern = r'\$[\d,]+\.?\d*'
                money_matches = list(re.finditer(money_pattern, remaining))
                
                if money_matches:
                    # Description is everything before the first money amount
                    first_money_start = money_matches[0].start()
                    trans_data['description'] = remaining[:first_money_start].strip()
                    
                    # Process money amounts
                    amounts = []
                    for match in money_matches:
                        amt_str = match.group().replace('$', '').replace(',', '')
                        amounts.append(float(amt_str))
                    
                    # Determine what each amount represents
                    desc_lower = trans_data['description'].lower()
                    
                    # Special handling for opening/closing balance
                    if 'opening balance' in desc_lower:
                        trans_data['balance'] = amounts[0] if amounts else 0
                    elif 'closing balance' in desc_lower:
                        trans_data['balance'] = amounts[0] if amounts else 0
                    else:
                        # Regular transaction
                        if len(amounts) == 1:
                            # Single amount with balance on same line
                            trans_data['balance'] = amounts[0]
                        elif len(amounts) == 2:
                            # Amount and balance
                            if any(kw in desc_lower for kw in ['deposit', 'salary', 'income', 'credit']):
                                trans_data['credit'] = amounts[0]
                            else:
                                trans_data['debit'] = amounts[0]
                            trans_data['balance'] = amounts[1]
                        elif len(amounts) >= 3:
                            # Debit, Credit, Balance columns
                            # Check spacing between amounts to determine column assignment
                            debit_match = money_matches[0]
                            credit_match = money_matches[1] if len(money_matches) > 1 else None
                            balance_match = money_matches[-1]
                            
                            # If there's significant spacing between first and second amount,
                            # it likely means first is debit, second is credit
                            if credit_match and (credit_match.start() - debit_match.end()) > 5:
                                trans_data['debit'] = amounts[0]
                                # Credit column might be empty (represented by spacing)
                                trans_data['balance'] = amounts[-1]
                            else:
                                # Otherwise, check description for hints
                                if any(kw in desc_lower for kw in ['deposit', 'salary', 'income']):
                                    trans_data['credit'] = amounts[0]
                                else:
                                    trans_data['debit'] = amounts[0]
                                trans_data['balance'] = amounts[-1]
                else:
                    # No amounts found with $, try without
                    num_pattern = r'\b\d+[,.]?\d*\b'
                    nums = re.findall(num_pattern, remaining)
                    if nums:
                        # Take everything before first number as description
                        first_num_match = re.search(num_pattern, remaining)
                        if first_num_match:
                            trans_data['description'] = remaining[:first_num_match.start()].strip()
                
                # Clean up description
                trans_data['description'] = trans_data['description'].strip('|').strip()
                
                # Only add if we have a valid description
                if trans_data['description'] and not trans_data['description'].lower() in ['total debits', 'total credits', 'ending balance']:
                    trans = BankTransaction(**trans_data)
                    transactions.append(trans)
        
        return BankStatement(transactions=transactions)
    
    def create_prompt(self, bank_statement_text: str) -> str:
        """Create formatted prompt for the AI"""
        return self.prompt_template.format(bank_statement=bank_statement_text)


# Keep the same helper function
def parse_bank_statement_to_csv(ai_response: str) -> tuple[BankStatement, str]:
    """
    Parse AI response and return both structured data and CSV
    
    Returns:
        tuple: (BankStatement object, CSV string)
    """
    parser = BankStatementParser()
    bank_statement = parser.parse(ai_response)
    csv_content = bank_statement.to_csv()
    
    return bank_statement, csv_content