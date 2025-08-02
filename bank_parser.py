"""
Bank Statement Parser using LangChain for structured output
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
            'Groceries': ['grocery', 'food', 'market', 'supermarket', 'walmart'],
            'Transportation': ['gas station', 'fuel', 'petrol', 'uber', 'lyft', 'taxi', 'parking'],
            'Dining': ['restaurant', 'cafe', 'coffee', 'dining', 'pizza', 'food'],
            'Shopping': ['amazon', 'online shop', 'ebay', 'store', 'purchase'],
            'Utilities': ['utility', 'electric', 'water bill', 'gas bill', 'internet', 'phone'],
            'Housing': ['rent', 'mortgage', 'lease'],
            'Income': ['salary', 'payroll', 'wage', 'deposit', 'direct deposit'],
            'Transfer': ['transfer', 'payment', 'zelle', 'venmo', 'atm'],
            'Healthcare': ['pharmacy', 'doctor', 'medical', 'hospital'],
            'Entertainment': ['movie', 'netflix', 'spotify', 'game'],
            'Banking': ['service fee', 'bank fee', 'overdraft', 'interest']
        }
        
        # Check for income first (credits usually)
        if values.get('credit', 0) > 0 and values.get('debit', 0) == 0:
            if any(keyword in description for keyword in ['salary', 'payroll', 'wage', 'deposit']):
                return 'Income'
        
        # Check other categories
        for category, keywords in categories.items():
            if any(keyword in description for keyword in keywords):
                return category
        
        # Special case for ATM
        if 'atm' in description and values.get('debit', 0) > 0:
            return 'Cash'
            
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
            logger.info("Attempting table format parse...")
            bank_statement = self.parse_table_format(ai_response)
            if bank_statement.transactions:
                bank_statement.calculate_totals()
                logger.info(f"Table parse successful: {len(bank_statement.transactions)} transactions")
                return bank_statement
            
            # If all else fails, return empty statement
            logger.warning("All parsing methods failed, returning empty statement")
            return BankStatement(transactions=[])
    
    def parse_table_format(self, text: str) -> BankStatement:
        """Parse table format from AI response"""
        transactions = []
        lines = text.split('\n')
        in_table = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for table headers
            if 'date' in line.lower() and ('description' in line.lower() or 'transaction' in line.lower()):
                in_table = True
                continue
            
            # Skip separator lines
            if line.startswith('-') or line.startswith('='):
                continue
                
            if in_table:
                # Try to parse transaction line
                parts = re.split(r'\s{2,}|\t|\|', line)
                parts = [p.strip() for p in parts if p.strip()]
                
                if len(parts) >= 3:
                    # Look for date pattern
                    date_pattern = r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}'
                    date_match = re.search(date_pattern, line)
                    
                    if date_match:
                        trans_data = {
                            'date': date_match.group(),
                            'description': '',
                            'debit': 0,
                            'credit': 0,
                            'balance': 0
                        }
                        
                        # Extract description (text between date and amounts)
                        remaining = line[date_match.end():].strip()
                        
                        # Find amounts
                        amount_pattern = r'[-+]?\$?\d+[,.]?\d*'
                        amounts = re.findall(amount_pattern, remaining)
                        
                        if amounts:
                            # Description is text before first amount
                            first_amount_pos = remaining.find(amounts[0])
                            if first_amount_pos > 0:
                                trans_data['description'] = remaining[:first_amount_pos].strip()
                            
                            # Parse amounts
                            for i, amt in enumerate(amounts):
                                amt_clean = amt.replace('$', '').replace(',', '')
                                amt_val = float(amt_clean)
                                
                                # Determine if debit or credit
                                desc_lower = trans_data['description'].lower()
                                if amt.startswith('-') or (i == 0 and amt_val > 0 and 'deposit' not in desc_lower and 'salary' not in desc_lower):
                                    trans_data['debit'] = abs(amt_val)
                                elif amt.startswith('+') or 'deposit' in desc_lower or 'salary' in desc_lower:
                                    trans_data['credit'] = abs(amt_val)
                                elif i == len(amounts) - 1:  # Last amount is likely balance
                                    trans_data['balance'] = abs(amt_val)
                        
                        if trans_data['description']:  # Only add if we found a description
                            trans = BankTransaction(**trans_data)
                            transactions.append(trans)
        
        return BankStatement(transactions=transactions)
    
    def create_prompt(self, bank_statement_text: str) -> str:
        """Create formatted prompt for the AI"""
        return self.prompt_template.format(bank_statement=bank_statement_text)


# Example usage function
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