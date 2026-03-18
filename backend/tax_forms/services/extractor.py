import pandas as pd
import io
import re
import os
import time
import requests
import pdfplumber
from django.core.files.uploadedfile import InMemoryUploadedFile

# ---------------------------------------------------------------------------
# Address Auto-Detection
# ---------------------------------------------------------------------------

EVM_CHAINS = ['ethereum', 'polygon', 'bsc', 'avalanche', 'fantom', 'arbitrum', 'optimism']

def detect_address_type(address: str) -> dict:
    """
    Détecte automatiquement le type d'une adresse blockchain.
    Retourne un dict: {'type': 'evm'|'btc'|'tron'|'unknown', 'chains': [...]}
    """
    address = address.strip()
    # EVM (Ethereum et compatibles) : commence par 0x, 42 chars hex
    if re.match(r'^0x[0-9a-fA-F]{40}$', address):
        return {'type': 'evm', 'chains': EVM_CHAINS}
    # Bitcoin (Legacy P2PKH, P2SH, Bech32)
    if re.match(r'^(1|3)[1-9A-HJ-NP-Za-km-z]{25,34}$', address) or re.match(r'^bc1[a-z0-9]{25,90}$', address):
        return {'type': 'btc', 'chains': ['bitcoin']}
    # Tron : T + 33 chars base58
    if re.match(r'^T[1-9A-HJ-NP-Za-km-z]{33}$', address):
        return {'type': 'tron', 'chains': ['tron']}
    
    return {'type': 'unknown', 'chains': []}

# ---------------------------------------------------------------------------
# Fetchers API Historique de Prix
# ---------------------------------------------------------------------------

PRICE_CACHE = {}

def get_historical_price(symbol: str, timestamp_str: str, currency: str = 'EUR') -> float:
    """
    Récupère le prix historique d'un token via l'API CryptoCompare.
    Utilise un cache local pour éviter les appels redondants.
    """
    if not timestamp_str or not symbol:
        return 0.0

    try:
        # CORRECTION : Forcer l'UTC pour éviter les décalages horaires
        date_obj = pd.to_datetime(timestamp_str)
        if date_obj.tzinfo is None:
            date_obj = date_obj.tz_localize('UTC')
            
        ts = int(date_obj.timestamp())
        
        # Arrondir à l'heure pour augmenter le taux de hit du cache
        ts_key = (symbol, ts // 3600 * 3600, currency)
        
        if ts_key in PRICE_CACHE:
            return PRICE_CACHE[ts_key]
            
        print(f"Fetching historical price for {symbol} at {date_obj}...")
        url = "https://min-api.cryptocompare.com/data/v2/histohour"
        params = {
            'fsym': symbol,
            'tsym': currency,
            'limit': 1,
            'toTs': ts
        }
        
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if data.get('Response') == 'Success' and data.get('Data', {}).get('Data'):
            # Prendre le dernier point de données avant ou à l'instant T
            price = data['Data']['Data'][-1].get('close', 0)
            PRICE_CACHE[ts_key] = price
            return price
            
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        
    return 0.0

# ---------------------------------------------------------------------------
# Blockchains Fetchers
# ---------------------------------------------------------------------------

SCAN_APIS = {
    "ethereum": "https://api.etherscan.io/v2/api",
    "polygon": "https://api.etherscan.io/v2/api",
    "bsc": "https://api.etherscan.io/v2/api",
    "avalanche": "https://api.snowtrace.io/api",
    "fantom": "https://api.etherscan.io/v2/api",
    "arbitrum": "https://api.etherscan.io/v2/api",
    "optimism": "https://api.etherscan.io/v2/api"
}

CHAIN_METADATA = {
    "ethereum": {"chainid": 1, "symbol": "ETH", "version": "v2"},
    "polygon": {"chainid": 137, "symbol": "MATIC", "version": "v2"},
    "bsc": {"chainid": 56, "symbol": "BNB", "version": "v2"},
    "avalanche": {"chainid": 43114, "symbol": "AVAX", "version": "v1"},
    "fantom": {"chainid": 146, "symbol": "FTM", "version": "v2"},
    "arbitrum": {"chainid": 42161, "symbol": "ETH", "version": "v2"},
    "optimism": {"chainid": 10, "symbol": "ETH", "version": "v2"}
}

def fetch_on_chain_transactions(address: str, blockchains: list = None) -> list:
    address = address.strip()
    detected = detect_address_type(address)
    addr_type = detected['type']
    print(f"Address {address[:12]}... detected as type: {addr_type}")

    if addr_type == 'btc':
        return fetch_btc_transactions(address)
    elif addr_type == 'tron':
        return fetch_tron_transactions(address)
    elif addr_type == 'evm':
        chains_to_scan = blockchains if blockchains else detected['chains']
        return _fetch_evm_transactions(address, chains_to_scan)
    else:
        print(f"Unknown address type for: {address}")
        return []

def _fetch_evm_transactions(address: str, blockchains: list) -> list:
    transactions = []
    
    for chain in blockchains:
        api_url = SCAN_APIS.get(chain)
        metadata = CHAIN_METADATA.get(chain)
        if not api_url or not metadata:
            continue

        api_key = os.getenv("ETHERSCAN_API_KEY")
        if not api_key:
            api_key = os.getenv(f"{chain.upper()}_SCAN_API_KEY")

        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'sort': 'asc',
            'apikey': api_key or 'FREE_KEY'
        }
        if metadata.get('version') == 'v2':
            params['chainid'] = metadata['chainid']

        try:
            print(f"Fetching transactions for {address} on {chain} (ID: {metadata['chainid']})...")
            response = requests.get(api_url, params=params, timeout=10)
            data = response.json()

            if data.get('status') == '1' and 'result' in data:
                raw_txs = data['result']
                for tx in raw_txs:
                    value_native = float(tx.get('value', 0)) / 10**18
                    if value_native > 0:
                        is_outbound = tx.get('from', '').lower() == address.lower()
                        date_str = pd.to_datetime(int(tx['timeStamp']), unit='s', utc=True).strftime('%Y-%m-%d %H:%M:%S')
                        price_unit = get_historical_price(metadata['symbol'], date_str)
                        
                        # CORRECTION : On ne paie le gas que si on est l'expéditeur (outbound)
                        gas_fee = (float(tx.get('gasUsed', 0)) * float(tx.get('gasPrice', 0))) / 10**18
                        
                        transactions.append({
                            'date': date_str,
                            'operation_type': 'vente' if is_outbound else 'achat',
                            'crypto_token': metadata['symbol'],
                            'tx_hash': tx.get('hash'),
                            'quantity': value_native,
                            'price': price_unit,
                            'fees': gas_fee if is_outbound else 0.0,
                            'currency': 'EUR'
                        })
            else:
                print(f"No transactions found on {chain}.")
                
        except Exception as e:
            print(f"Error fetching from {chain}: {e}")
            
        # CORRECTION : Éviter le Rate Limit d'Etherscan (max 5 req/sec sur le plan gratuit)
        time.sleep(0.25)

    return transactions

def fetch_btc_transactions(address: str) -> list:
    transactions = []
    try:
        url = f"https://blockstream.info/api/address/{address}/txs"
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return []
            
        txs = response.json()
        for tx in txs:
            status = tx.get('status', {})
            if not status.get('confirmed'):
                continue
                
            block_time = status.get('block_time', 0)
            date_str = pd.to_datetime(block_time, unit='s', utc=True).strftime('%Y-%m-%d %H:%M:%S') if block_time else None
            if not date_str:
                continue

            received = sum(vout.get('value', 0) / 1e8 for vout in tx.get('vout', []) if address in [vout.get('scriptpubkey_address', '')])
            sent = sum(vin.get('prevout', {}).get('value', 0) / 1e8 for vin in tx.get('vin', []) if address in [vin.get('prevout', {}).get('scriptpubkey_address', '')])
            
            fees_btc = tx.get('fee', 0) / 1e8
            net = received - sent
            op_type = 'achat' if net > 0 else 'vente'
            quantity = abs(net)

            if quantity < 1e-9:
                continue

            price_unit = get_historical_price('BTC', date_str)
            transactions.append({
                'date': date_str,
                'operation_type': op_type,
                'crypto_token': 'BTC',
                'tx_hash': tx.get('txid'),
                'quantity': quantity,
                'price': price_unit,
                'fees': fees_btc if op_type == 'vente' else 0.0,
                'currency': 'EUR'
            })
    except Exception as e:
        print(f"Error fetching BTC transactions: {e}")
    return transactions

def fetch_tron_transactions(address: str) -> list:
    transactions = []
    try:
        url = f"https://api.trongrid.io/v1/accounts/{address}/transactions"
        params = {'limit': 200, 'only_confirmed': True}
        tron_api_key = os.getenv('TRON_API_KEY', '')
        headers = {'TRON-PRO-API-KEY': tron_api_key} if tron_api_key else {}
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
            
        txs = response.json().get('data', [])
        for tx in txs:
            raw_data = tx.get('raw_data', {}).get('contract', [{}])[0]
            if raw_data.get('type', '') != 'TransferContract':
                continue
                
            value_data = raw_data.get('parameter', {}).get('value', {})
            amount_trx = value_data.get('amount', 0) / 1e6
            if amount_trx < 0.001:
                continue
                
            timestamp_ms = tx.get('block_timestamp', 0)
            date_str = pd.to_datetime(timestamp_ms, unit='ms', utc=True).strftime('%Y-%m-%d %H:%M:%S') if timestamp_ms else None
            if not date_str:
                continue
                
            from_addr = value_data.get('owner_address', '')
            op_type = 'vente' if from_addr == address else 'achat'
            price_unit = get_historical_price('TRX', date_str)
            
            transactions.append({
                'date': date_str,
                'operation_type': op_type,
                'crypto_token': 'TRX',
                'tx_hash': tx.get('txID'),
                'quantity': amount_trx,
                'price': price_unit,
                'fees': 0.0,
                'currency': 'EUR'
            })
    except Exception as e:
        print(f"Error fetching Tron transactions: {e}")
    return transactions

# ---------------------------------------------------------------------------
# File Parsers (CEX & Generics)
# ---------------------------------------------------------------------------

def clean_numeric(value):
    if value is None or value == '' or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    
    s = str(value).strip()
    cleaned = re.sub(r'[^0-9.,-]', '', s)
    if not cleaned:
        return 0.0
        
    if ',' in cleaned and '.' not in cleaned:
        cleaned = cleaned.replace(',', '.')
    elif ',' in cleaned and '.' in cleaned:
        cleaned = cleaned.replace(',', '')
        
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def parse_transaction_file(file: InMemoryUploadedFile, cex_type: str = "generic"):
    file.seek(0)
    filename = file.name.lower()
    
    try:
        if filename.endswith('.pdf'):
            df = parse_pdf_file(file)
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(file)
        else:
            df = attempt_csv_parse(file, filename)
            if df is None and (filename.endswith('.txt') or filename.endswith('.csv')):
                df = parse_unstructured_text(file)
        
        if df is None or df.empty:
            raise ValueError(f"Format de fichier non supporté ou données vides : {filename}")
        
        transactions = []
        df.columns = [str(c).lower().strip() for c in df.columns]
        df = df.fillna({
            'quantity': 0, 'price': 0, 'fees': 0, 'amount': 0, 'fee': 0, 'type': '', 'operation': ''
        })

        for _, row_ser in df.iterrows():
            row = row_ser.to_dict()
            if cex_type == "binance":
                tx = parse_binance_row(row)
            elif cex_type == "coinbase":
                tx = parse_coinbase_row(row)
            elif cex_type == "kraken":
                tx = parse_kraken_row(row)
            else:
                tx = parse_generic_row(row)
                
            if tx and tx.get('date'):
                transactions.append(tx)
                
        try:
            transactions.sort(key=lambda x: pd.to_datetime(x['date'], utc=True) if x['date'] else pd.Timestamp.min.tz_localize('UTC'))
        except:
            transactions.sort(key=lambda x: str(x['date']))
            
        return transactions
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        return []

def attempt_csv_parse(file, filename):
    file.seek(0)
    content = file.read()
    
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    delimiters = [None, ',', ';', '\t']
    header_keywords = {'timestamp', 'date', 'type', 'asset', 'symbol', 'quantity', 'amount', 'operation', 'transaction type', 'actif', 'quantité'}
    
    for encoding in encodings:
        try:
            decoded_content = content.decode(encoding)
            lines = decoded_content.splitlines()
            
            for sep in delimiters:
                try:
                    skiprows = 0
                    found_header = False
                    for i, line in enumerate(lines[:20]):
                        cells = [c.strip().lower() for c in (line.split(sep) if sep else line.split())]
                        if any(kw in cells for kw in header_keywords):
                            skiprows = i
                            found_header = True
                            break
                    
                    df = pd.read_csv(io.StringIO(decoded_content), sep=sep, skiprows=skiprows if found_header else 0, engine='python')
                    if len(df.columns) > 1:
                        cols_lower = [str(c).lower() for c in df.columns]
                        if any(kw in "".join(cols_lower) for kw in header_keywords):
                            return df
                except Exception: continue
        except UnicodeDecodeError: continue
    return None

def parse_pdf_file(file):
    all_data = []
    headers = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table:
                    row = [str(c).replace('\n', ' ').strip() if c else '' for c in row]
                    if not any(row): continue
                    if not headers:
                        if any(kw in [c.lower() for c in row] for kw in ['date', 'type', 'asset', 'actif']):
                            headers = row
                        continue
                    if len(row) == len(headers): all_data.append(row)
    return pd.DataFrame(all_data, columns=headers) if all_data and headers else None

def parse_unstructured_text(file):
    file.seek(0)
    lines = file.read().decode('utf-8', errors='ignore').splitlines()
    found_txs = []
    tx_pattern = re.compile(r'(\d{4}[-/]\d{2}[-/]\d{2})(?:\s+[\d:]{5,8})?\s+(Buy|Sell|Achat|Vente|Trade|Deposit|Withdrawal)\s+([\d.,]+)\s+([A-Z0-9]{2,10})', re.IGNORECASE)
    for line in lines:
        match = tx_pattern.search(line)
        if match:
            found_txs.append({
                'date': match.group(1),
                'type': match.group(2).lower(),
                'quantity': match.group(3).replace(',', '.'),
                'asset': match.group(4).upper()
            })
    return pd.DataFrame(found_txs) if found_txs else None

def parse_coinbase_row(row: dict):
    try:
        date = row.get('timestamp') or row.get('date') or row.get('created at')
        op_type_raw = str(row.get('transaction type') or row.get('type') or row.get('operation') or '').lower()
        asset = row.get('asset') or row.get('symbol') or row.get('base asset')
        quantity = row.get('quantity transacted') or row.get('amount') or row.get('size') or row.get('quantity')
        price = row.get('spot price at transaction') or row.get('price at transaction') or row.get('price') or row.get('unit price') or row.get('subtotal')
        fees = row.get('fees') or row.get('fee') or 0
        currency = row.get('spot price currency') or row.get('currency') or row.get('quote asset') or 'EUR'

        if any(word in op_type_raw for word in ['buy', 'achat', 'match']):
            op_type = 'achat'
        elif any(word in op_type_raw for word in ['sell', 'vente']):
            op_type = 'vente'
        elif any(word in op_type_raw for word in ['receive', 'reçu', 'deposit', 'dépôt', 'withdrawal', 'retrait', 'send', 'envoi']):
            op_type = 'transfert'
        else:
            op_type = 'transfert'

        return {
            'date': date,
            'operation_type': op_type,
            'crypto_token': asset,
            'quantity': abs(clean_numeric(quantity)),
            'price': clean_numeric(price),
            'fees': clean_numeric(fees),
            'currency': currency
        }
    except Exception: return None

def parse_binance_row(row: dict):
    try:
        op_type_raw = str(row.get('type') or row.get('operation') or '').lower()
        op_type = 'achat' if 'buy' in op_type_raw else 'vente' if 'sell' in op_type_raw else 'transfert'

        market = row.get('market') or ''
        crypto = market.replace('EUR', '').replace('USD', '') or row.get('asset') or row.get('crypto')
        currency = 'EUR' if 'EUR' in market else 'USD' if 'USD' in market else row.get('currency') or 'UNKNOWN'

        return {
            'date': row.get('date(utc)') or row.get('date') or row.get('time'),
            'operation_type': op_type,
            'crypto_token': crypto,
            'quantity': clean_numeric(row.get('amount') or row.get('quantity')),
            'price': clean_numeric(row.get('price')),
            'fees': clean_numeric(row.get('fee') or row.get('fees')),
            'currency': currency
        }
    except Exception: return None

def parse_kraken_row(row: dict):
    try:
        date = row.get('time') or row.get('date')
        op_type_raw = str(row.get('type') or row.get('tx_type') or '').lower()
        asset = row.get('asset') or row.get('pair')
        
        if asset and len(asset) > 3 and (asset.startswith('X') or asset.startswith('Z')):
            asset = asset[1:]

        quantity = row.get('amount') or row.get('vol') or row.get('quantity')
        price = row.get('price') or row.get('cost')
        fees = row.get('fee') or 0
        currency = row.get('currency') or 'EUR'

        op_type = 'achat' if any(w in op_type_raw for w in ['buy', 'trade']) else 'vente' if 'sell' in op_type_raw else 'transfert'

        return {
            'date': date,
            'operation_type': op_type,
            'crypto_token': asset,
            'quantity': abs(clean_numeric(quantity)),
            'price': clean_numeric(price),
            'fees': clean_numeric(fees),
            'currency': currency
        }
    except Exception: return None

def parse_generic_row(row: dict):
    try:
        date = row.get('date') or row.get('timestamp') or row.get('time') or row.get('created_at') or row.get('date(utc)') or row.get('transact_time') or row.get('heure')
        op_type_raw = str(row.get('type') or row.get('operation_type') or row.get('operation') or row.get('side') or row.get('type d\'opération') or '').lower()
        asset = row.get('crypto') or row.get('asset') or row.get('token') or row.get('symbol') or row.get('crypto_token') or row.get('base_asset') or row.get('actif') or row.get('devise') or row.get('market', '').replace('EUR', '').replace('USD', '')
        quantity = row.get('quantity') or row.get('amount') or row.get('amount_crypto') or row.get('executed') or row.get('filled') or row.get('quantité') or row.get('montant')
        price = row.get('price') or row.get('value') or row.get('unit_price') or row.get('spot_price') or row.get('price at transaction') or row.get('subtotal') or row.get('prix') or row.get('valeur')
        fees = row.get('fees') or row.get('fee') or row.get('transaction_fee') or row.get('frais') or row.get('commission') or 0
        currency = row.get('currency') or row.get('fiat') or row.get('quote_asset') or row.get('unité') or 'EUR'
        acq_price = row.get('acq_price') or row.get('acquisition_price') or row.get('prix_acquisition') or row.get('prix d\'acquisition') or 0

        if any(word in op_type_raw for word in ['buy', 'achat']):
            op_type = 'achat'
        elif any(word in op_type_raw for word in ['sell', 'vente']):
            op_type = 'vente'
        elif any(word in op_type_raw for word in ['deposit', 'dépôt', 'reçu', 'receive', 'withdrawal', 'retrait', 'envoi', 'send']):
            op_type = 'transfert'
        else:
            op_type = 'transfert'

        return {
            'date': date,
            'operation_type': op_type,
            'crypto_token': asset,
            'quantity': clean_numeric(quantity),
            'price': clean_numeric(price),
            'acq_price': clean_numeric(acq_price),
            'fees': clean_numeric(fees),
            'currency': currency
        }
    except Exception: return None