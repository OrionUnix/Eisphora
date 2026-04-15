import pandas as pd
import io
import re
import os
import time
import requests
import pdfplumber
from django.core.files.uploadedfile import InMemoryUploadedFile
from typing import Dict

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
# Fetchers API Historique de Prix (Avec Fallback CoinGecko)
# ---------------------------------------------------------------------------

PRICE_CACHE = {}

def get_historical_price(symbol: str, timestamp_str: str, currency: str = 'EUR') -> float:
    """
    Récupère le prix historique d'un token via l'API CryptoCompare, avec fallback sur CoinGecko.
    Utilise un cache local pour éviter les appels redondants.
    """
    if not timestamp_str or not symbol:
        return 0.0

    try:
        # Forcer l'UTC pour éviter les décalages horaires
        date_obj = pd.to_datetime(timestamp_str)
        if date_obj.tzinfo is None:
            date_obj = date_obj.tz_localize('UTC')
            
        ts = int(date_obj.timestamp())
        
        # Arrondir à l'heure pour augmenter le taux de hit du cache
        ts_key = (symbol.upper(), ts // 3600 * 3600, currency.upper())
        
        if ts_key in PRICE_CACHE:
            return PRICE_CACHE[ts_key]
            
        # 1. Tentative CryptoCompare
        url = "https://min-api.cryptocompare.com/data/v2/histohour"
        params = {'fsym': symbol.upper(), 'tsym': currency.upper(), 'limit': 1, 'toTs': ts}
        
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if data.get('Response') == 'Success' and data.get('Data', {}).get('Data'):
            price = data['Data']['Data'][-1].get('close', 0.0)
            if price > 0:
                PRICE_CACHE[ts_key] = price
                return price

        # 2. Fallback CoinGecko (si CryptoCompare échoue)
        cg_id = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin', 'AVAX': 'avalanche-2',
            'FTM': 'fantom', 'MATIC': 'polygon', 'POL': 'polygon-ecosystem-token'
        }.get(symbol.upper(), symbol.lower())
        
        url_cg = f"https://api.coingecko.com/api/v3/coins/{cg_id}/history"
        params_cg = {'date': date_obj.strftime('%d-%m-%Y')}
        
        time.sleep(0.5) # Pause de sécurité CoinGecko (Rate limit strict)
        
        resp_cg = requests.get(url_cg, params=params_cg, timeout=6)
        if resp_cg.status_code == 200:
            price = resp_cg.json().get('market_data', {}).get('current_price', {}).get(currency.lower(), 0.0)
            if price > 0:
                PRICE_CACHE[ts_key] = price
                return price
                
    except Exception as e:
        pass
        
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

    if addr_type == 'btc':
        return fetch_btc_transactions(address)
    elif addr_type == 'tron':
        return fetch_tron_transactions(address)
    elif addr_type == 'evm':
        chains_to_scan = blockchains if blockchains else detected['chains']
        return _fetch_evm_transactions(address, chains_to_scan)
    else:
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
                        
                        # On ne paie le gas que si on est l'expéditeur (outbound)
                        gas_fee = (float(tx.get('gasUsed', 0)) * float(tx.get('gasPrice', 0))) / 10**18
                        
                        transactions.append({
                            'date': date_str,
                            'operation_type': 'vente' if is_outbound else 'achat',
                            'crypto_token': metadata['symbol'],
                            'tx_hash': tx.get('hash'),
                            'quantity': value_native,
                            'price': price_unit,
                            'fees': gas_fee if is_outbound else 0.0,
                            'currency': 'EUR',
                            'source': address
                        })
                
        except Exception as e:
            pass
            
        # Éviter le Rate Limit d'Etherscan (max 5 req/sec sur le plan gratuit)
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
                'currency': 'EUR',
                'source': address
            })
    except Exception as e:
        pass
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
                'currency': 'EUR',
                'source': address
            })
    except Exception as e:
        pass
    return transactions

# ---------------------------------------------------------------------------
# File Parsers (CEX & Generics)
# ---------------------------------------------------------------------------

def clean_numeric(value):
    """
    Nettoie une valeur pour la convertir en float, 
    gère les virgules, les symboles corrompus (ex: â‚¬) et les espaces.
    """
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

import json

def parse_custom_csv(file: InMemoryUploadedFile, mapping_json: str, delimiter: str = ',') -> list:
    """
    Parse un CSV en utilisant un mappage de colonnes défini par l'utilisateur.
    mapping_json est une string JSON: {"date": "Timestamp", "operation_type": "Transaction Type", ...}
    """
    file.seek(0)
    try:
        # 1. Décoder le mappage de l'utilisateur
        mapping = json.loads(mapping_json)
        
        # 2. Sécuriser le délimiteur s'il n'est pas fourni correctement
        if not delimiter:
            delimiter = ','
            
        # 3. Lire le CSV avec le bon délimiteur (on gère les virgules de fin comme vu précédemment)
        content = file.read()
        try:
            decoded = content.decode('utf-8')
        except UnicodeDecodeError:
            decoded = content.decode('latin-1')
            
        cleaned_lines = [line.rstrip(delimiter + '\r\n ') for line in decoded.splitlines()]
        cleaned_content = '\n'.join(cleaned_lines)
            
        import io
        import csv
        
        # 3.5 Détecter intelligemment la ligne d'en-tête (sauter les lignes parasites)
        skiprows = 0
        for i, line in enumerate(cleaned_lines[:20]):
            line = line.strip()
            if not line:
                continue
            row_cells = next(csv.reader(io.StringIO(line), delimiter=delimiter), [])
            if len(row_cells) > 3:
                skiprows = i
                break

        df = pd.read_csv(io.StringIO(cleaned_content), sep=delimiter, skiprows=skiprows, engine='python')
        
        # 4. Nettoyer les noms de colonnes du dataframe (enlever les espaces inutiles)
        df.columns = [str(c).strip() for c in df.columns]
        
        transactions = []
        
        for idx, row_ser in df.iterrows():
            row = row_ser.to_dict()
            # Extraire les données en utilisant le nom exact de la colonne choisie par l'utilisateur
            raw_date = row.get(mapping.get('date', ''))
            raw_type = str(row.get(mapping.get('operation_type', ''))).lower()
            raw_asset = row.get(mapping.get('crypto_token', ''))
            raw_qty = row.get(mapping.get('quantity', ''))
            raw_price = row.get(mapping.get('price', ''))
            raw_fees = row.get(mapping.get('fees', ''))
            raw_currency = row.get(mapping.get('currency', ''))
            
            # Si on n'a pas de date ou d'actif, on ignore la ligne
            if pd.isna(raw_date) or pd.isna(raw_asset) or raw_date == '' or raw_asset == '':
                continue
                
            # Normalisation du type (Achat, Vente, Transfert)
            # Normalisation du type (Achat, Vente, Transfert)
            if any(w in raw_type for w in ['buy', 'achat']):
                op_type = 'achat'
            elif any(w in raw_type for w in ['sell', 'vente']):
                op_type = 'vente'
            elif any(w in raw_type for w in ['receive', 'reçu']):
                op_type = 'achat'      # Réception externe = nouvelle acquisition → augmente le PTA
            elif any(w in raw_type for w in ['staking', 'earn', 'reward', 'income']):
                op_type = 'staking'    # Gains passifs → augmente le PTA au prix marché
            elif any(w in raw_type for w in ['deposit', 'dépôt']):
                op_type = 'depot'      # Auto-transfert entrant
            elif any(w in raw_type for w in ['withdrawal', 'retrait', 'send', 'envoi']):
                op_type = 'retrait'    # Envoi externe
            else:
                op_type = 'transfert'

            # Construction de l'objet Transaction propre
            tx = {
                'index': idx + 1,
                'date': str(raw_date),
                'operation_type': op_type,
                'crypto': str(raw_asset).upper(),
                'quantity': abs(clean_numeric(raw_qty)),
                'price': clean_numeric(raw_price),
                'fees': clean_numeric(raw_fees),
                'currency': str(raw_currency).upper() if not pd.isna(raw_currency) and raw_currency else 'EUR',
                'source': 'Import personnalisé'
            }
            transactions.append(tx)
            
        # Tri des transactions
        try:
            transactions.sort(key=lambda x: pd.to_datetime(x['date'], utc=True) if x['date'] else pd.Timestamp.min.tz_localize('UTC'))
        except:
            transactions.sort(key=lambda x: str(x['date']))
            
        return transactions

    except Exception as e:
        return []

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
            
            # Auto-detect CEX from filename if generic
            effective_cex = cex_type
            if effective_cex == "generic":
                if "coinbase" in filename:
                    effective_cex = "coinbase"
                elif "binance" in filename:
                    effective_cex = "binance"
                elif "kraken" in filename:
                    effective_cex = "kraken"

            if effective_cex == "binance":
                tx = parse_binance_row(row)
            elif effective_cex == "coinbase":
                tx = parse_coinbase_row(row)
            elif effective_cex == "kraken":
                tx = parse_kraken_row(row)
            else:
                tx = parse_generic_row(row)
                
            if tx and tx.get('date'):
                tx['source'] = filename
                transactions.append(tx)
                
        try:
            transactions.sort(key=lambda x: pd.to_datetime(x['date'], utc=True) if x['date'] else pd.Timestamp.min.tz_localize('UTC'))
        except:
            transactions.sort(key=lambda x: str(x['date']))
            
        return transactions
    except Exception as e:
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
                    # Clean trailing delimiters to prevent pandas ParserError (e.g. Coinbase extra commas)
                    if sep:
                        cleaned_lines = [line.rstrip(sep + '\r\n ') for line in lines]
                    else:
                        cleaned_lines = lines
                        
                    cleaned_content = '\n'.join(cleaned_lines)
                    
                    skiprows = 0
                    found_header = False
                    for i, line in enumerate(cleaned_lines[:20]):
                        cells = [c.strip().lower() for c in (line.split(sep) if sep else line.split())]
                        if any(kw in cells for kw in header_keywords):
                            skiprows = i
                            found_header = True
                            break
                    
                    df = pd.read_csv(io.StringIO(cleaned_content), sep=sep, skiprows=skiprows if found_header else 0, engine='python')
                    if len(df.columns) > 1:
                        cols_lower = [str(c).lower() for c in df.columns]
                        if any(kw in "".join(cols_lower) for kw in header_keywords):
                            return df
                except Exception: continue
        except UnicodeDecodeError: continue
    return None

def parse_pdf_file(file):
    """
    Extrait des transactions depuis un PDF.
    Stratégie 1 : tableaux structurés via pdfplumber.extract_table().
    Stratégie 2 : texte brut via extract_text() passé à parse_unstructured_text().
    """
    HEADER_KEYWORDS = {'date', 'type', 'asset', 'actif', 'amount', 'quantity',
                       'montant', 'quantité', 'transaction', 'time', 'timestamp', 'opération'}
    all_data = []
    headers = []
    full_text_lines = []

    try:
        file.seek(0)
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                # --- Stratégie 1 : Tableaux ---
                tables = page.extract_tables() or []
                for table in tables:
                    local_headers = []
                    for row in table:
                        row = [str(c).replace('\n', ' ').strip() if c else '' for c in row]
                        if not any(row):
                            continue
                        row_lower = [c.lower() for c in row]
                        # Détection souple de l'en-tête
                        if not local_headers and any(kw in cell for cell in row_lower for kw in HEADER_KEYWORDS):
                            local_headers = row
                            if not headers:
                                headers = local_headers
                            continue
                        # Si on a déjà des headers globaux, on essaie de mapper
                        if not local_headers and headers:
                            local_headers = headers
                        if local_headers and len(row) == len(local_headers):
                            all_data.append(row)
                        elif local_headers and len(row) > 0:
                            # Compléter ou tronquer pour éviter les erreurs de DataFrame
                            padded = (row + [''] * len(local_headers))[:len(local_headers)]
                            all_data.append(padded)

                # --- Stratégie 2 : Texte brut (fallback) ---
                text = page.extract_text() or ''
                full_text_lines.extend(text.splitlines())

    except Exception:
        pass

    # Si tableaux extraits avec succès → retourner le DataFrame
    if all_data and headers:
        try:
            df = pd.DataFrame(all_data, columns=headers)
            df.columns = [str(c).lower().strip() for c in df.columns]
            return df
        except Exception:
            pass

    # Sinon → fallback texte brut
    if full_text_lines:
        import io as _io
        text_bytes = '\n'.join(full_text_lines).encode('utf-8')
        fake_file = _io.BytesIO(text_bytes)
        fake_file.name = 'extracted.txt'
        return parse_unstructured_text(fake_file)

    return None

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
        price = row.get('price at transaction') or row.get('spot price at transaction') or row.get('price') or row.get('unit price') or row.get('subtotal')
        
        # 🚨 CORRECTION : Ajout de 'fees and/or spread' pour le format Coinbase
        fees = row.get('fees and/or spread') or row.get('fees') or row.get('fee') or 0
        currency = row.get('price currency') or row.get('spot price currency') or row.get('currency') or row.get('quote asset') or 'EUR'

        # Classification granulaire pour le calcul fiscal PMP (art. 150 VH bis)
        if any(word in op_type_raw for word in ['buy', 'achat', 'match', 'advanced trade buy']):
            op_type = 'achat'          # Achat fiat→crypto : augmente le PTA
        elif any(word in op_type_raw for word in ['sell', 'vente', 'advanced trade sell']):
            op_type = 'vente'          # Vente crypto→fiat : événement imposable
        elif any(word in op_type_raw for word in ['receive', 'reçu']):
            op_type = 'achat'          # Réception externe = nouvelle acquisition : augmente le PTA
        elif any(word in op_type_raw for word in ['staking', 'income', 'reward', 'earn', 'interest', 'cashback', 'referral']):
            op_type = 'staking'        # Gains passifs : nouvelles unités au prix marché → augmente le PTA
        elif any(word in op_type_raw for word in ['withdrawal', 'retrait', 'send', 'envoi']):
            op_type = 'retrait'        # Envoi vers wallet externe : PTA inchangé
        else:
            op_type = 'depot'          # Dépôt fiat / auto-transfert entrant : PTA inchangé

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
        
        if any(word in op_type_raw for word in ['buy', 'achat']):
            op_type = 'achat'
        elif any(word in op_type_raw for word in ['sell', 'vente']):
            op_type = 'vente'
        elif any(word in op_type_raw for word in ['staking', 'earn', 'interest', 'reward', 'cashback', 'referral', 'distribution', 'airdrop']):
            op_type = 'staking'    # Gains passifs Binance → augmente le PTA
        elif any(word in op_type_raw for word in ['deposit', 'receive', 'in']):
            op_type = 'depot'      # Dépôt / auto-transfert entrant
        elif any(word in op_type_raw for word in ['withdraw', 'send', 'out']):
            op_type = 'retrait'    # Retrait vers wallet externe
        elif any(word in op_type_raw for word in ['convert', 'swap', 'exchange', 'transfer']):
            op_type = 'echange'    # Swap crypto↔crypto : sursis d'imposition
        else:
            op_type = 'transfert'

        market = row.get('market') or ''
        crypto = market.replace('EUR', '').replace('USD', '') or row.get('asset') or row.get('crypto')
        currency = 'EUR' if 'EUR' in market else 'USD' if 'USD' in market else row.get('currency') or 'UNKNOWN'

        return {
            'date': row.get('date(utc)') or row.get('date') or row.get('time'),
            'operation_type': op_type,
            'crypto_token': crypto,
            'quantity': abs(clean_numeric(row.get('amount') or row.get('quantity'))),
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

        if any(w in op_type_raw for w in ['buy', 'trade']):
            op_type = 'achat'
        elif 'sell' in op_type_raw:
            op_type = 'vente'
        elif any(w in op_type_raw for w in ['staking', 'reward', 'earn', 'interest']):
            op_type = 'staking'    # Gains passifs Kraken → augmente le PTA
        elif any(w in op_type_raw for w in ['deposit', 'receive']):
            op_type = 'depot'
        elif any(w in op_type_raw for w in ['withdrawal', 'send']):
            op_type = 'retrait'
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

def parse_generic_row(row: dict):
    try:
        date = row.get('date') or row.get('timestamp') or row.get('time') or row.get('created_at') or row.get('date(utc)') or row.get('transact_time') or row.get('heure')
        op_type_raw = str(row.get('type') or row.get('operation_type') or row.get('operation') or row.get('side') or row.get('type d\'opération') or row.get('transaction type') or '').lower()
        asset = row.get('crypto') or row.get('asset') or row.get('token') or row.get('symbol') or row.get('crypto_token') or row.get('base_asset') or row.get('actif') or row.get('devise') or row.get('market', '').replace('EUR', '').replace('USD', '')
        quantity = row.get('quantity') or row.get('amount') or row.get('amount_crypto') or row.get('executed') or row.get('filled') or row.get('quantité') or row.get('montant') or row.get('quantity transacted') or row.get('size')
        price = row.get('price') or row.get('value') or row.get('unit_price') or row.get('spot_price') or row.get('price at transaction') or row.get('subtotal') or row.get('prix') or row.get('valeur')
        fees = row.get('fees') or row.get('fee') or row.get('transaction_fee') or row.get('fees and/or spread') or row.get('frais') or row.get('commission') or 0
        currency = row.get('currency') or row.get('price currency') or row.get('fiat') or row.get('quote_asset') or row.get('unité') or 'EUR'
        acq_price = row.get('acq_price') or row.get('acquisition_price') or row.get('prix_acquisition') or row.get('prix d\'acquisition') or 0

        if any(word in op_type_raw for word in ['buy', 'achat']):
            op_type = 'achat'
        elif any(word in op_type_raw for word in ['sell', 'vente']):
            op_type = 'vente'
        elif any(word in op_type_raw for word in ['receive', 'reçu']):
            op_type = 'achat'      # Réception externe = acquisition → augmente le PTA
        elif any(word in op_type_raw for word in ['staking', 'reward', 'earn', 'income', 'interest', 'airdrop']):
            op_type = 'staking'    # Gains passifs → augmente le PTA au prix marché
        elif any(word in op_type_raw for word in ['deposit', 'dépôt']):
            op_type = 'depot'      # Auto-transfert entrant : PTA inchangé
        elif any(word in op_type_raw for word in ['withdrawal', 'retrait', 'send', 'envoi']):
            op_type = 'retrait'    # Envoi externe : PTA inchangé
        else:
            op_type = 'transfert'  # Neutre : auto-transfert inconnu

        return {
            'date': date,
            'operation_type': op_type,
            'crypto_token': asset,
            'quantity': abs(clean_numeric(quantity)),
            'price': clean_numeric(price),
            'acq_price': clean_numeric(acq_price),
            'fees': clean_numeric(fees),
            'currency': currency
        }
    except Exception: return None