import csv
import codecs
from django.core.files.uploadedfile import InMemoryUploadedFile

def parse_csv_file(file: InMemoryUploadedFile, cex_type: str = "generic"):
    file.seek(0)
    csv_reader = csv.DictReader(codecs.iterdecode(file, 'utf-8'))
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
            
    transactions.sort(key=lambda x: x['date'])
    return transactions

def parse_binance_row(row: dict):
    try:
        op_type_raw = row.get('Type', '').lower()
        if 'buy' in op_type_raw:
            op_type = 'achat'
        elif 'sell' in op_type_raw:
            op_type = 'vente'
        else:
            op_type = 'transfert'

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
    return []
