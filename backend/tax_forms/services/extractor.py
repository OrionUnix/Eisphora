import csv
import io
import datetime
from django.core.files.uploadedfile import InMemoryUploadedFile

def parse_csv_file(file: InMemoryUploadedFile, cex_type: str = "generic"):
    """
    Parses a CSV file directly from memory without saving to disk.
    Standardizes the output to a common format.
    """
    # Read the file from memory
    file_content = file.read().decode('utf-8')
    # Reset file pointer if needed elsewhere
    file.seek(0)
    
    csv_reader = csv.DictReader(io.StringIO(file_content))
    transactions = []
    
    for row in csv_reader:
        if cex_type == "binance":
            tx = parse_binance_row(row)
        elif cex_type == "kraken":
            tx = parse_kraken_row(row)
        else:
            tx = parse_generic_row(row)
            
        if tx:
            transactions.append(tx)
            
    # Sort by date ascending (FIFO requirement)
    transactions.sort(key=lambda x: x['date'])
    return transactions

def parse_binance_row(row: dict):
    # Binance format example: Date(UTC),Market,Type,Price,Amount,Total,Fee,Fee Coin
    # This is a simplified parser. Real world has many variations.
    try:
        op_type_raw = row.get('Type', '').lower()
        if 'buy' in op_type_raw:
            op_type = 'achat'
        elif 'sell' in op_type_raw:
            op_type = 'vente'
        else:
            # We skip transfers for now or label them non-taxable
            op_type = 'transfert'

        # Usually Market is like BTCEUR
        market = row.get('Market', '')
        crypto = market.replace('EUR', '').replace('USD', '')
        currency = 'EUR' if 'EUR' in market else 'USD' if 'USD' in market else 'UNKNOWN'

        return {
            'date': row.get('Date(UTC)', ''),
            'operation_type': op_type,
            'crypto_token': crypto,
            'quantity': float(row.get('Amount', 0)),
            'price': float(row.get('Price', 0)),
            'fees': float(row.get('Fee', 0)),
            'currency': currency
        }
    except Exception as e:
        print(f"Error parsing Binance row: {e}")
        return None

def parse_generic_row(row: dict):
    # Expected columns: date, type, crypto, quantity, price, fees, currency
    try:
        return {
            'date': row.get('date', ''),
            'operation_type': row.get('type', 'transfert').lower(),
            'crypto_token': row.get('crypto', ''),
            'quantity': float(row.get('quantity', 0)),
            'price': float(row.get('price', 0)),
            'fees': float(row.get('fees', 0)),
            'currency': row.get('currency', 'EUR')
        }
    except Exception as e:
        print(f"Error parsing generic row: {e}")
        return None

def fetch_on_chain_transactions(address: str):
    """
    Fetches transactions securely from an EVM explorer.
    Server acts as a proxy so the user's IP is not leaked.
    No data is cached on disk.
    """
    # TODO: Implement with requests to Etherscan/Polygonscan API
    # Returning empty list for simulation
    return []
