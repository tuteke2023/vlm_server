"""
Improved Bank Statement Parser v3 - handles various table formats
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
            'Shopping': ['amazon', 'online', 'ebay', 'store', 'purchase', 'shop', 'electronics'],
            'Utilities': ['utility', 'electric', 'water bill', 'gas bill', 'internet', 'phone', 'bill payment'],
            'Housing': ['rent', 'mortgage', 'lease', 'housing'],
            'Income': ['salary', 'payroll', 'wage', 'deposit', 'direct deposit', 'income'],
            'Transfer': ['transfer', 'payment', 'zelle', 'venmo', 'savings'],
            'Healthcare': ['pharmacy', 'doctor', 'medical', 'hospital', 'cvs', 'walgreens'],
            'Entertainment': ['movie', 'netflix', 'spotify', 'game', 'subscription'],
            'Banking': ['service fee', 'bank fee', 'overdraft', 'interest', 'atm fee', 'fees'],
            'Cash': ['atm withdrawal', 'cash withdrawal', 'atm'],
            'Bills': ['bill payment', 'mastercard', 'visa', 'amex', 'credit card']
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
            logger.info("Attempting improved table format parse v3...")
            bank_statement = self.parse_table_format_v3(ai_response)
            if bank_statement.transactions:
                bank_statement.calculate_totals()
                logger.info(f"Table parse successful: {len(bank_statement.transactions)} transactions")
                return bank_statement
            
            # If all else fails, return empty statement
            logger.warning("All parsing methods failed, returning empty statement")
            return BankStatement(transactions=[])
    
    def parse_table_format_v3(self, text: str) -> BankStatement:
        """Enhanced table format parser that handles various formats"""
        transactions = []
        lines = text.split('\n')
        
        # Try to detect table header to understand column layout
        header_line = None
        header_idx = -1
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if ('date' in line_lower and 
                ('description' in line_lower or 'transaction' in line_lower) and
                ('debit' in line_lower or 'withdrawal' in line_lower or 'deposits' in line_lower)):
                header_line = line
                header_idx = i
                break
        
        # Determine column mapping from header
        column_map = self._analyze_header(header_line) if header_line else None
        logger.debug(f"Column mapping: {column_map}")
        
        # Parse transactions
        for i, line in enumerate(lines):
            if i <= header_idx + 1:  # Skip header and separator lines
                continue
                
            line = line.strip()
            if not line or line.startswith('-') or line.startswith('='):
                continue
            
            # Look for date pattern
            date_pattern = r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}'
            date_match = re.search(date_pattern, line)
            
            if date_match:
                # Parse based on whether it's pipe-delimited or space-delimited
                if '|' in line:
                    trans = self._parse_pipe_delimited_line(line, column_map)
                else:
                    trans = self._parse_space_delimited_line(line)
                
                if trans and trans.description and 'balance' not in trans.description.lower():
                    transactions.append(trans)
        
        return BankStatement(transactions=transactions)
    
    def _analyze_header(self, header: str) -> dict:
        """Analyze header to determine column positions"""
        header_lower = header.lower()
        columns = {}
        
        # Split by pipe if present
        if '|' in header:
            parts = [p.strip() for p in header.split('|')]
            for i, part in enumerate(parts):
                part_lower = part.lower()
                if 'date' in part_lower:
                    columns['date'] = i
                elif 'description' in part_lower or 'transaction' in part_lower:
                    columns['description'] = i
                elif 'debit' in part_lower or 'withdrawal' in part_lower:
                    columns['debit'] = i
                elif 'credit' in part_lower or 'deposit' in part_lower:
                    columns['credit'] = i
                elif 'balance' in part_lower:
                    columns['balance'] = i
                elif 'ref' in part_lower:
                    columns['ref'] = i
        
        return columns
    
    def _parse_pipe_delimited_line(self, line: str, column_map: dict) -> Optional[BankTransaction]:
        """Parse a pipe-delimited transaction line"""
        parts = [p.strip() for p in line.split('|')]
        
        if not column_map or len(parts) < 3:
            return None
        
        trans_data = {
            'date': '',
            'description': '',
            'debit': 0,
            'credit': 0,
            'balance': 0
        }
        
        # Extract data based on column mapping
        for field, idx in column_map.items():
            if idx < len(parts):
                value = parts[idx].strip()
                if field == 'date':
                    trans_data['date'] = value
                elif field == 'description':
                    trans_data['description'] = value
                elif field in ['debit', 'credit', 'balance']:
                    # Parse numeric value
                    num_str = re.sub(r'[^\d.,\-]', '', value)
                    if num_str and num_str != '-':
                        try:
                            trans_data[field] = abs(float(num_str.replace(',', '')))
                        except ValueError:
                            pass
        
        # Create transaction if we have minimal data
        if trans_data['date'] and trans_data['description']:
            # Special case for deposits that might be in withdrawals column
            desc_lower = trans_data['description'].lower()
            if 'deposit' in desc_lower or 'payroll' in desc_lower:
                if trans_data['debit'] > 0 and trans_data['credit'] == 0:
                    trans_data['credit'] = trans_data['debit']
                    trans_data['debit'] = 0
            
            return BankTransaction(**trans_data)
        
        return None
    
    def _parse_space_delimited_line(self, line: str) -> Optional[BankTransaction]:
        """Parse a space-delimited transaction line"""
        # Similar to v2 parser logic
        date_pattern = r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}'
        date_match = re.search(date_pattern, line)
        
        if not date_match:
            return None
        
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
        
        # Find all numeric values (with or without dollar signs)
        num_pattern = r'[-+]?\$?[\d,]+\.?\d*'
        num_matches = list(re.finditer(num_pattern, remaining))
        
        if num_matches:
            # Description is everything before the first number
            first_num_start = num_matches[0].start()
            trans_data['description'] = remaining[:first_num_start].strip()
            
            # Process numeric values
            amounts = []
            for match in num_matches:
                num_str = match.group().replace('$', '').replace(',', '')
                try:
                    amounts.append(float(num_str))
                except ValueError:
                    pass
            
            # Assign amounts based on context
            desc_lower = trans_data['description'].lower()
            
            if len(amounts) == 1:
                trans_data['balance'] = abs(amounts[0])
            elif len(amounts) == 2:
                if any(kw in desc_lower for kw in ['deposit', 'salary', 'income', 'payroll']):
                    trans_data['credit'] = abs(amounts[0])
                else:
                    trans_data['debit'] = abs(amounts[0])
                trans_data['balance'] = abs(amounts[1])
            elif len(amounts) >= 3:
                trans_data['debit'] = abs(amounts[0]) if amounts[0] else 0
                trans_data['credit'] = abs(amounts[1]) if amounts[1] else 0
                trans_data['balance'] = abs(amounts[-1]) if amounts[-1] else 0
        
        # Clean up description
        trans_data['description'] = trans_data['description'].strip('|').strip()
        
        if trans_data['description']:
            return BankTransaction(**trans_data)
        
        return None
    
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