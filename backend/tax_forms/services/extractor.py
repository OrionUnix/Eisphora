import csv
import io
import json
import logging
import os
import re
import time
from typing import Dict, List, Optional
import pandas as pd
import requests
from django.core.cache import cache
from django.core.files.uploadedfile import InMemoryUploadedFile
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Session HTTP avec retry automatique
# ---------------------------------------------------------------------------

def _build_session(retries: int = 3, backoff: float = 0.5) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

_SESSION = _build_session()


# ---------------------------------------------------------------------------
# Détection automatique du type d'adresse blockchain
# ---------------------------------------------------------------------------

EVM_CHAINS = [
    'ethereum', 'polygon', 'bsc', 'avalanche',
    'fantom', 'arbitrum', 'optimism',
]

def detect_address_type(address: str) -> dict:
    """
    Détecte automatiquement le type d'une adresse blockchain.

    Retourne
    --------
    dict : {'type': 'evm'|'btc'|'tron'|'unknown', 'chains': [...]}
    """
    address = address.strip()

    # EVM (Ethereum et compatibles) : 0x + 40 caractères hexadécimaux
    if re.match(r'^0x[0-9a-fA-F]{40}$', address):
        return {'type': 'evm', 'chains': EVM_CHAINS}

    # Bitcoin Legacy (P2PKH / P2SH) et SegWit (Bech32)
    if (
        re.match(r'^(1|3)[1-9A-HJ-NP-Za-km-z]{25,34}$', address)
        or re.match(r'^bc1[a-z0-9]{25,90}$', address)
    ):
        return {'type': 'btc', 'chains': ['bitcoin']}

    # Tron : T + 33 caractères base58
    if re.match(r'^T[1-9A-HJ-NP-Za-km-z]{33}$', address):
        return {'type': 'tron', 'chains': ['tron']}

    return {'type': 'unknown', 'chains': []}


# ---------------------------------------------------------------------------
# Récupération des prix historiques (CryptoCompare + fallback CoinGecko)
# ---------------------------------------------------------------------------

# Mapping symbole → id CoinGecko (complété par rapport à la version originale)
_COINGECKO_IDS: Dict[str, str] = {
    'BTC':   'bitcoin',
    'ETH':   'ethereum',
    'BNB':   'binancecoin',
    'AVAX':  'avalanche-2',
    'FTM':   'fantom',
    'MATIC': 'polygon',
    'POL':   'polygon-ecosystem-token',
    'SOL':   'solana',
    'ADA':   'cardano',
    'DOT':   'polkadot',
    'LINK':  'chainlink',
    'UNI':   'uniswap',
    'XRP':   'ripple',
    'LTC':   'litecoin',
    'TRX':   'tron',
    'ATOM':  'cosmos',
    'NEAR':  'near',
    'OP':    'optimism',
    'ARB':   'arbitrum',
}

_CACHE_TTL = 86_400  # 24 heures (en secondes)


def get_historical_price(
    symbol: str,
    timestamp_str: str,
    currency: str = 'EUR',
) -> float:
    """
    Récupère le prix historique d'un token pour une date donnée.

    Stratégie
    ---------
    1. Cache Django (évite les appels réseau redondants).
    2. API CryptoCompare /histohour.
    3. Fallback API CoinGecko /history.

    Paramètres
    ----------
    symbol        : Symbole du token (ex: 'BTC', 'ETH').
    timestamp_str : Date/heure ISO 8601 ou 'YYYY-MM-DD'.
    currency      : Devise de référence (défaut 'EUR').

    Retourne
    --------
    float : Prix en `currency`, ou 0.0 si introuvable.
    """
    if not symbol or not timestamp_str:
        return 0.0

    symbol = symbol.upper().strip()
    currency = currency.upper().strip()

    try:
        date_obj = pd.to_datetime(timestamp_str)
        if date_obj.tzinfo is None:
            date_obj = date_obj.tz_localize('UTC')
        ts = int(date_obj.timestamp())
    except Exception:
        logger.warning("get_historical_price : date invalide '%s'", timestamp_str)
        return 0.0

    # Arrondi à l'heure pour maximiser les hits cache
    ts_rounded = ts // 3600 * 3600
    cache_key = f"hprice_{symbol}_{ts_rounded}_{currency}"

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    price = _fetch_cryptocompare(symbol, ts_rounded, currency)

    if price <= 0:
        price = _fetch_coingecko(symbol, date_obj, currency)

    if price > 0:
        cache.set(cache_key, price, timeout=_CACHE_TTL)
    else:
        # Cache aggressively even if price is 0.0 to prevent spamming the APIs for unknown shitcoins
        cache.set(cache_key, 0.0, timeout=_CACHE_TTL)
        logger.debug(
            "Prix introuvable pour %s au %s (%s). Mis en cache à 0.0.",
            symbol, timestamp_str, currency,
        )

    return price


def _fetch_cryptocompare(symbol: str, ts: int, currency: str) -> float:
    """Appel à l'API CryptoCompare histohour."""
    try:
        url = "https://min-api.cryptocompare.com/data/v2/histohour"
        params = {
            'fsym': symbol,
            'tsym': currency,
            'limit': 1,
            'toTs': ts,
        }
        resp = _SESSION.get(url, params=params, timeout=6)
        resp.raise_for_status()
        data = resp.json()

        if data.get('Response') == 'Success':
            candles = data.get('Data', {}).get('Data', [])
            if candles:
                return float(candles[-1].get('close', 0.0))
    except Exception as exc:
        logger.debug("CryptoCompare error [%s] : %s", symbol, exc)
    return 0.0


def _fetch_coingecko(symbol: str, date_obj, currency: str) -> float:
    """Appel à l'API CoinGecko /history (fallback)."""
    try:
        cg_id = _COINGECKO_IDS.get(symbol, symbol.lower())
        url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/history"
        params = {'date': date_obj.strftime('%d-%m-%Y')}

        time.sleep(0.5)  # Respect du rate-limit CoinGecko (plan gratuit)
        resp = _SESSION.get(url, params=params, timeout=8)
        resp.raise_for_status()
        price = (
            resp.json()
            .get('market_data', {})
            .get('current_price', {})
            .get(currency.lower(), 0.0)
        )
        return float(price) if price else 0.0
    except Exception as exc:
        logger.debug("CoinGecko error [%s] : %s", symbol, exc)
    return 0.0


# ---------------------------------------------------------------------------
# Configuration des blockchains EVM
# ---------------------------------------------------------------------------

SCAN_APIS: Dict[str, str] = {
    "ethereum":  "https://api.etherscan.io/v2/api",
    "polygon":   "https://api.etherscan.io/v2/api",
    "bsc":       "https://api.etherscan.io/v2/api",
    "avalanche": "https://api.snowtrace.io/api",
    "fantom":    "https://api.etherscan.io/v2/api",
    "arbitrum":  "https://api.etherscan.io/v2/api",
    "optimism":  "https://api.etherscan.io/v2/api",
}

CHAIN_METADATA: Dict[str, dict] = {
    "ethereum":  {"chainid": 1,      "symbol": "ETH",  "version": "v2"},
    "polygon":   {"chainid": 137,    "symbol": "MATIC", "version": "v2"},
    "bsc":       {"chainid": 56,     "symbol": "BNB",  "version": "v2"},
    "avalanche": {"chainid": 43114,  "symbol": "AVAX", "version": "v1"},
    "fantom":    {"chainid": 146,    "symbol": "FTM",  "version": "v2"},
    "arbitrum":  {"chainid": 42161,  "symbol": "ETH",  "version": "v2"},
    "optimism":  {"chainid": 10,     "symbol": "ETH",  "version": "v2"},
}


# ---------------------------------------------------------------------------
# Fetchers on-chain
# ---------------------------------------------------------------------------

def fetch_on_chain_transactions(
    address: str,
    blockchains: Optional[List[str]] = None,
) -> List[dict]:
    """
    Point d'entrée unique pour récupérer les transactions on-chain.
    Détecte automatiquement le type d'adresse et dispatch vers le bon fetcher.
    """
    address = address.strip()
    detected = detect_address_type(address)
    addr_type = detected['type']

    if addr_type == 'btc':
        return fetch_btc_transactions(address)
    elif addr_type == 'tron':
        return fetch_tron_transactions(address)
    elif addr_type == 'evm':
        chains = blockchains if blockchains else detected['chains']
        return _fetch_evm_transactions(address, chains)
    else:
        logger.warning("Adresse non reconnue : '%s'", address)
        return []


def _fetch_evm_transactions(address: str, blockchains: List[str]) -> List[dict]:
    """
    Récupère les transactions EVM (natif + ERC-20) pour chaque chain demandée.
    Utilise l'API Etherscan v2 (ou Snowtrace pour Avalanche).
    """
    transactions: List[dict] = []

    api_key = (
        os.getenv("ETHERSCAN_API_KEY")
        or os.getenv("SCAN_API_KEY")
        or "FREE_KEY"
    )

    for chain in blockchains:
        api_url = SCAN_APIS.get(chain)
        metadata = CHAIN_METADATA.get(chain)
        if not api_url or not metadata:
            logger.warning("Chain non configurée : '%s'", chain)
            continue

        chain_api_key = os.getenv(f"{chain.upper()}_SCAN_API_KEY", api_key)

        base_params = {
            'module': 'account',
            'address': address,
            'startblock': 0,
            'endblock': 99_999_999,
            'sort': 'asc',
            'apikey': chain_api_key,
        }
        if metadata.get('version') == 'v2':
            base_params['chainid'] = metadata['chainid']

        # --- Transactions natives (ETH, BNB, MATIC, AVAX…) ---
        native_txs = _call_scan_api(
            api_url, {**base_params, 'action': 'txlist'}
        )
        for tx in native_txs:
            parsed = _parse_evm_native_tx(tx, address, metadata)
            if parsed:
                transactions.append(parsed)

        # --- Transactions ERC-20 (USDC, LINK, UNI, PEPE…) ---
        erc20_txs = _call_scan_api(
            api_url, {**base_params, 'action': 'tokentx'}
        )
        for tx in erc20_txs:
            parsed = _parse_evm_erc20_tx(tx, address)
            if parsed:
                transactions.append(parsed)

        # Respect du rate-limit Etherscan (5 req/s sur plan gratuit)
        time.sleep(0.25)

    # Tri chronologique final
    transactions.sort(key=lambda x: x.get('date', ''))
    return transactions


def _call_scan_api(url: str, params: dict) -> List[dict]:
    """Appel générique à une API compatible Etherscan. Retourne la liste brute."""
    try:
        resp = _SESSION.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') == '1' and isinstance(data.get('result'), list):
            return data['result']
        logger.debug("Scan API – réponse vide ou erreur : %s", data.get('message'))
    except Exception as exc:
        logger.error("Scan API error (%s) : %s", url, exc)
    return []


def _parse_evm_native_tx(tx: dict, address: str, metadata: dict) -> Optional[dict]:
    """Parse une transaction native EVM (ETH, BNB, MATIC…)."""
    try:
        value_native = float(tx.get('value', 0)) / 10**18
        if value_native <= 0:
            return None

        is_outbound = tx.get('from', '').lower() == address.lower()
        ts = int(tx['timeStamp'])
        date_str = pd.to_datetime(ts, unit='s', utc=True).strftime('%Y-%m-%dT%H:%M:%SZ')
        symbol = metadata['symbol']
        price_unit = get_historical_price(symbol, date_str)
        gas_fee = (
            float(tx.get('gasUsed', 0)) * float(tx.get('gasPrice', 0))
        ) / 10**18

        return {
            'date': date_str,
            'operation_type': 'vente' if is_outbound else 'achat',
            'crypto_token': symbol,
            'tx_hash': tx.get('hash'),
            'quantity': value_native,
            'price': price_unit,
            'fees': gas_fee if is_outbound else 0.0,
            'currency': 'EUR',
            'source': address,
        }
    except Exception as exc:
        logger.debug("Parse EVM native tx error : %s", exc)
        return None


def _parse_evm_erc20_tx(tx: dict, address: str) -> Optional[dict]:
    """Parse une transaction ERC-20 (token transfer)."""
    try:
        decimals = int(tx.get('tokenDecimal', 18) or 18)
        raw_value = float(tx.get('value', 0) or 0)
        quantity = raw_value / (10 ** decimals)
        if quantity <= 0:
            return None

        symbol = str(tx.get('tokenSymbol', 'UNKNOWN')).upper()
        is_outbound = tx.get('from', '').lower() == address.lower()
        ts = int(tx['timeStamp'])
        date_str = pd.to_datetime(ts, unit='s', utc=True).strftime('%Y-%m-%dT%H:%M:%SZ')
        price_unit = get_historical_price(symbol, date_str)

        return {
            'date': date_str,
            'operation_type': 'vente' if is_outbound else 'achat',
            'crypto_token': symbol,
            'tx_hash': tx.get('hash'),
            'quantity': quantity,
            'price': price_unit,
            'fees': 0.0,  # Les frais de gas sont comptés dans la tx native
            'currency': 'EUR',
            'source': address,
        }
    except Exception as exc:
        logger.debug("Parse ERC-20 tx error : %s", exc)
        return None


def fetch_btc_transactions(address: str) -> List[dict]:
    """
    Récupère les transactions Bitcoin via l'API Blockstream.
    Gère la pagination (max 25 tx par appel).
    """
    transactions: List[dict] = []
    last_seen_txid: Optional[str] = None

    while True:
        url = f"https://blockstream.info/api/address/{address}/txs"
        if last_seen_txid:
            url += f"/chain/{last_seen_txid}"

        try:
            resp = _SESSION.get(url, timeout=15)
            resp.raise_for_status()
            txs = resp.json()
        except Exception as exc:
            logger.error("Blockstream API error [%s] : %s", address, exc)
            break

        if not txs:
            break

        for tx in txs:
            parsed = _parse_btc_tx(tx, address)
            if parsed:
                transactions.append(parsed)

        if len(txs) < 25:
            break  # Dernière page
        last_seen_txid = txs[-1].get('txid')

    return transactions


def _parse_btc_tx(tx: dict, address: str) -> Optional[dict]:
    """Parse une transaction Bitcoin brute."""
    try:
        status = tx.get('status', {})
        if not status.get('confirmed'):
            return None

        block_time = status.get('block_time', 0)
        if not block_time:
            return None

        date_str = pd.to_datetime(block_time, unit='s', utc=True).strftime('%Y-%m-%dT%H:%M:%SZ')

        received = sum(
            vout.get('value', 0) / 1e8
            for vout in tx.get('vout', [])
            if vout.get('scriptpubkey_address') == address
        )
        sent = sum(
            vin.get('prevout', {}).get('value', 0) / 1e8
            for vin in tx.get('vin', [])
            if vin.get('prevout', {}).get('scriptpubkey_address') == address
        )

        net = received - sent
        quantity = abs(net)
        if quantity < 1e-9:
            return None

        op_type = 'achat' if net > 0 else 'vente'
        fees_btc = tx.get('fee', 0) / 1e8
        price_unit = get_historical_price('BTC', date_str)

        return {
            'date': date_str,
            'operation_type': op_type,
            'crypto_token': 'BTC',
            'tx_hash': tx.get('txid'),
            'quantity': quantity,
            'price': price_unit,
            'fees': fees_btc if op_type == 'vente' else 0.0,
            'currency': 'EUR',
            'source': address,
        }
    except Exception as exc:
        logger.debug("Parse BTC tx error : %s", exc)
        return None


def fetch_tron_transactions(address: str) -> List[dict]:
    """
    Récupère les transactions Tron TRX via TronGrid.
    Gère la pagination complète via le curseur 'fingerprint'.
    """
    transactions: List[dict] = []
    tron_api_key = os.getenv('TRON_API_KEY', '')
    headers = {'TRON-PRO-API-KEY': tron_api_key} if tron_api_key else {}
    url = f"https://api.trongrid.io/v1/accounts/{address}/transactions"
    fingerprint: Optional[str] = None

    while True:
        params: dict = {'limit': 200, 'only_confirmed': True}
        if fingerprint:
            params['fingerprint'] = fingerprint

        try:
            resp = _SESSION.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            logger.error("TronGrid API error [%s] : %s", address, exc)
            break

        txs = payload.get('data', [])
        for tx in txs:
            parsed = _parse_tron_tx(tx, address)
            if parsed:
                transactions.append(parsed)

        # Curseur de pagination TronGrid
        meta = payload.get('meta', {})
        fingerprint = meta.get('fingerprint')
        if not fingerprint or not txs:
            break

    return transactions


def _parse_tron_tx(tx: dict, address: str) -> Optional[dict]:
    """Parse une transaction Tron TRX brute."""
    try:
        raw_data = tx.get('raw_data', {}).get('contract', [{}])[0]
        if raw_data.get('type') != 'TransferContract':
            return None

        value_data = raw_data.get('parameter', {}).get('value', {})
        amount_trx = value_data.get('amount', 0) / 1e6
        if amount_trx < 0.001:
            return None

        timestamp_ms = tx.get('block_timestamp', 0)
        if not timestamp_ms:
            return None

        date_str = pd.to_datetime(timestamp_ms, unit='ms', utc=True).strftime('%Y-%m-%dT%H:%M:%SZ')
        from_addr = value_data.get('owner_address', '')
        op_type = 'vente' if from_addr == address else 'achat'
        price_unit = get_historical_price('TRX', date_str)

        return {
            'date': date_str,
            'operation_type': op_type,
            'crypto_token': 'TRX',
            'tx_hash': tx.get('txID'),
            'quantity': amount_trx,
            'price': price_unit,
            'fees': 0.0,
            'currency': 'EUR',
            'source': address,
        }
    except Exception as exc:
        logger.debug("Parse Tron tx error : %s", exc)
        return None


# ---------------------------------------------------------------------------
# Utilitaires de nettoyage numérique
# ---------------------------------------------------------------------------

def clean_numeric(value) -> float:
    """
    Convertit une valeur en float positif.
    Gère les virgules européennes, les symboles corrompus et les espaces.
    """
    if value is None or value == '':
        return 0.0
    if isinstance(value, (int, float)):
        return float(value) if not pd.isna(value) else 0.0

    s = str(value).strip()
    cleaned = re.sub(r'[^0-9.,-]', '', s)
    if not cleaned:
        return 0.0

    # Notation européenne : "1.234,56" → "1234.56"
    if ',' in cleaned and '.' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')
    # Notation simple : "1234,56" → "1234.56"
    elif ',' in cleaned:
        cleaned = cleaned.replace(',', '.')

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


# ---------------------------------------------------------------------------
# Normalisation du type d'opération
# ---------------------------------------------------------------------------

def _normalize_op_type(raw: str) -> str:

    raw = raw.lower().strip()

    # -----------------------------------------------------------------------
    # Transferts internes Coinbase (Retail Staking/Unstaking Transfer)
    # Ces opérations sont des mouvements comptables internes entre le wallet
    # principal et le sous-compte de staking. Elles se présentent toujours
    # par paires (+qty / -qty) qui se neutralisent et n'ont AUCUNE réalité
    # fiscale : ni cession, ni acquisition, ni modification du PTA.
    # -----------------------------------------------------------------------
    if any(w in raw for w in [
        'retail staking transfer',
        'retail unstaking transfer',
    ]):
        return 'transfert_interne'  # Ignoré dans calculate_french_taxes()

    if any(w in raw for w in ['buy', 'achat', 'match', 'advanced trade buy']):
        return 'achat'
    if any(w in raw for w in ['sell', 'vente', 'advanced trade sell']):
        return 'vente'
    if any(w in raw for w in ['receive', 'reçu']):
        return 'achat'   # Réception externe = nouvelle acquisition → augmente le PTA
    if any(w in raw for w in ['staking income', 'staking', 'earn', 'reward',
                               'income', 'interest', 'cashback', 'referral',
                               'distribution', 'airdrop']):
        return 'staking'  # Gains passifs → augmente le PTA au prix marché
    if any(w in raw for w in ['deposit', 'dépôt']):
        return 'depot'    # Auto-transfert entrant : PTA inchangé
    if any(w in raw for w in ['withdrawal', 'retrait', 'send', 'envoi']):
        return 'retrait'  # Envoi externe : PTA inchangé
    if any(w in raw for w in ['convert', 'swap', 'exchange']):
        return 'echange'  # Échange crypto↔crypto : sursis d'imposition

    return 'transfert'    # Neutre / inconnu


# ---------------------------------------------------------------------------
# Parser CSV personnalisé (mappage utilisateur)
# ---------------------------------------------------------------------------

def parse_custom_csv(
    file: InMemoryUploadedFile,
    mapping_json: str,
    delimiter: str = ',',
) -> List[dict]:
    file.seek(0)

    try:
        mapping = json.loads(mapping_json)
    except json.JSONDecodeError as exc:
        logger.error("parse_custom_csv : mapping JSON invalide : %s", exc)
        return []

    delimiter = delimiter or ','

    try:
        content = file.read()
        try:
            decoded = content.decode('utf-8')
        except UnicodeDecodeError:
            decoded = content.decode('latin-1')

        cleaned_lines = [line.rstrip(delimiter + '\r\n ') for line in decoded.splitlines()]
        cleaned_content = '\n'.join(cleaned_lines)

        # Détection intelligente de la ligne d'en-tête
        skiprows = 0
        for i, line in enumerate(cleaned_lines[:20]):
            line = line.strip()
            if not line:
                continue
            row_cells = next(csv.reader(io.StringIO(line), delimiter=delimiter), [])
            if len(row_cells) > 3:
                skiprows = i
                break

        df = pd.read_csv(
            io.StringIO(cleaned_content),
            sep=delimiter,
            skiprows=skiprows,
            engine='python',
        )
        df.columns = [str(c).strip() for c in df.columns]

    except Exception as exc:
        logger.error("parse_custom_csv : erreur lecture CSV : %s", exc)
        return []

    transactions: List[dict] = []

    for idx, row_ser in df.iterrows():
        row = row_ser.to_dict()

        raw_date = row.get(mapping.get('date', ''))
        raw_type = str(row.get(mapping.get('operation_type', ''), '') or '')
        raw_asset = row.get(mapping.get('crypto_token', ''))
        raw_qty = row.get(mapping.get('quantity', ''))
        raw_price = row.get(mapping.get('price', ''))
        raw_fees = row.get(mapping.get('fees', ''))
        raw_currency = row.get(mapping.get('currency', ''))

        # Ignorer les lignes sans date ou actif
        if pd.isna(raw_date) or pd.isna(raw_asset) or str(raw_date) == '' or str(raw_asset) == '':
            continue

        tx = {
            'index': idx + 1,
            'date': str(raw_date),
            'operation_type': _normalize_op_type(raw_type),
            # 🔴 CORRECTION : clé 'crypto_token' (pas 'crypto')
            'crypto_token': str(raw_asset).strip().upper(),
            'quantity': abs(clean_numeric(raw_qty)),
            'price': clean_numeric(raw_price),
            'fees': clean_numeric(raw_fees),
            'currency': (
                str(raw_currency).strip().upper()
                if not pd.isna(raw_currency) and raw_currency
                else 'EUR'
            ),
            'source': 'Import personnalisé',
        }
        transactions.append(tx)

    try:
        transactions.sort(
            key=lambda x: pd.to_datetime(x['date'], utc=True)
            if x['date']
            else pd.Timestamp.min.tz_localize('UTC')
        )
    except Exception:
        transactions.sort(key=lambda x: str(x['date']))

    logger.info("parse_custom_csv : %d transactions parsées.", len(transactions))
    return transactions


# ---------------------------------------------------------------------------
# Parser générique de fichiers (CSV / Excel / PDF / TXT)
# ---------------------------------------------------------------------------

_HEADER_KEYWORDS = {
    'timestamp', 'date', 'type', 'asset', 'symbol', 'quantity',
    'amount', 'operation', 'transaction type', 'actif', 'quantité',
}

def parse_transaction_file(
    file: InMemoryUploadedFile,
    cex_type: str = "generic",
) -> List[dict]:
    file.seek(0)
    filename = file.name.lower()

    try:
        if filename.endswith(('.pdf', '.xlsx', '.xls')):
            logger.warning("Format PDF/XLSX non supporté : %s", filename)
            return []

        df = _attempt_csv_parse(file)
        if df is None:
            df = _parse_unstructured_text(file)

        if df is None or df.empty:
            logger.warning("Fichier vide ou format non supporté : %s", filename)
            return []

        df.columns = [str(c).lower().strip() for c in df.columns]
        df = df.fillna({
            'quantity': 0, 'price': 0, 'fees': 0,
            'amount': 0, 'fee': 0, 'type': '', 'operation': '',
        })

        # Auto-détection du CEX depuis le nom de fichier
        effective_cex = cex_type
        if effective_cex == "generic":
            if "coinbase" in filename:
                effective_cex = "coinbase"
            elif "binance" in filename:
                effective_cex = "binance"
            elif "kraken" in filename:
                effective_cex = "kraken"

        _parsers = {
            "binance":  _parse_binance_row,
            "coinbase": _parse_coinbase_row,
            "kraken":   _parse_kraken_row,
        }
        row_parser = _parsers.get(effective_cex, _parse_generic_row)

        transactions: List[dict] = []
        for _, row_ser in df.iterrows():
            tx = row_parser(row_ser.to_dict())
            if tx and tx.get('date'):
                tx['source'] = filename
                transactions.append(tx)

        try:
            transactions.sort(
                key=lambda x: pd.to_datetime(x['date'], utc=True)
                if x['date']
                else pd.Timestamp.min.tz_localize('UTC')
            )
        except Exception:
            transactions.sort(key=lambda x: str(x['date']))

        logger.info(
            "parse_transaction_file [%s / %s] : %d transactions parsées.",
            filename, effective_cex, len(transactions),
        )
        return transactions

    except Exception as exc:
        logger.error("parse_transaction_file [%s] : %s", filename, exc, exc_info=True)
        return []


def _attempt_csv_parse(file: InMemoryUploadedFile) -> Optional[pd.DataFrame]:
    """
    Tente de parser un fichier CSV en essayant plusieurs encodages et délimiteurs.
    """
    file.seek(0)
    content = file.read()

    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    delimiters = [',', ';', '\t', None]

    for encoding in encodings:
        try:
            decoded = content.decode(encoding)
            decoded = decoded.replace('â‚¬', '').replace('Â', '')
        except UnicodeDecodeError:
            continue

        lines = decoded.splitlines()

        for sep in delimiters:
            try:
                cleaned_lines = [line.rstrip((sep or '') + '\r\n ') for line in lines]
                cleaned_content = '\n'.join(cleaned_lines)

                skiprows = 0
                found_header = False
                for i, line in enumerate(cleaned_lines[:20]):
                    cells = [
                        c.strip().lower()
                        for c in (line.split(sep) if sep else line.split())
                    ]
                    if any(kw in cells for kw in _HEADER_KEYWORDS):
                        skiprows = i
                        found_header = True
                        break

                df = pd.read_csv(
                    io.StringIO(cleaned_content),
                    sep=sep,
                    skiprows=skiprows if found_header else 0,
                    engine='python',
                )
                if len(df.columns) > 1:
                    cols_joined = " ".join(str(c).lower() for c in df.columns)
                    if any(kw in cols_joined for kw in _HEADER_KEYWORDS):
                        return df
            except Exception:
                continue

    return None





def _parse_unstructured_text(file) -> Optional[pd.DataFrame]:
    """
    Tente d'extraire des transactions depuis du texte brut non structuré.
    """
    try:
        file.seek(0)
        lines = file.read().decode('utf-8', errors='ignore').splitlines()
        pattern = re.compile(
            r'(\d{4}[-/]\d{2}[-/]\d{2})(?:\s+[\d:]{5,8})?\s+'
            r'(Buy|Sell|Achat|Vente|Trade|Deposit|Withdrawal)\s+'
            r'([\d.,]+)\s+([A-Z0-9]{2,10})',
            re.IGNORECASE,
        )
        rows = []
        for line in lines:
            m = pattern.search(line)
            if m:
                rows.append({
                    'date': m.group(1),
                    'type': m.group(2).lower(),
                    'quantity': m.group(3).replace(',', '.'),
                    'asset': m.group(4).upper(),
                })
        return pd.DataFrame(rows) if rows else None
    except Exception as exc:
        logger.error("_parse_unstructured_text : %s", exc)
        return None


# ---------------------------------------------------------------------------
# Parsers spécifiques par CEX
# ---------------------------------------------------------------------------

def _parse_coinbase_row(row: dict) -> Optional[dict]:
    """Parse une ligne du CSV Coinbase."""
    try:
        date = row.get('timestamp') or row.get('date')
        op_raw = str(row.get('transaction type') or row.get('type') or '')
        asset = row.get('asset')
        quantity = row.get('quantity transacted') or row.get('amount')
        
        # Prix unitaire — nom exact Coinbase
        price_raw = (
            row.get('price at transaction')      # ← nom réel
            or row.get('spot price at transaction')
            or row.get('price')
        )
        price = clean_numeric(price_raw)
        
        # Fallback robuste depuis Notes
        # "Sold 2.741 AVAX for 71.21984156 EUR on AVAX-EUR at 26.14 EUR/AVAX"
        notes = str(row.get('notes') or '')
        if price == 0 and notes:
            m = re.search(r'at\s+([\d.]+)\s+\w+/\w+', notes)
            if m:
                price = float(m.group(1))
        
        # Frais — nom exact Coinbase récent
        fees = (
            row.get('fees and/or spread')
            or row.get('fees') or row.get('fee') or 0
        )
        
        # Subtotal = montant sans frais (utile pour FIFO)
        subtotal = clean_numeric(row.get('subtotal') or 0)
        total = clean_numeric(row.get('total') or 0)
        
        currency = (
            row.get('price currency')
            or row.get('currency') or 'EUR'
        )

        op_type = _normalize_op_type(op_raw)
        
        # Staking Income — quantité peut être très petite (0.0003489...)
        # → ne pas filtrer les très petites valeurs pour le staking
        qty = abs(clean_numeric(quantity))
        if qty == 0 and op_type != 'staking':
            return None

        return {
            'date': date,
            'operation_type': op_type,
            'crypto_token': str(asset).strip().upper() if asset else None,
            'quantity': qty,
            'price': price,
            'subtotal': subtotal,  # utile pour recalcul FIFO si prix = 0
            'total': total,
            'fees': clean_numeric(fees),
            'currency': str(currency).upper().strip(),
        }
    except Exception as exc:
        logger.debug("_parse_coinbase_row : %s", exc)
        return None


def _parse_binance_row(row: dict) -> Optional[dict]:
    """Parse une ligne du CSV Binance."""
    try:
        op_raw = str(row.get('type') or row.get('operation') or '')

        market = str(row.get('market') or '')

        # 🟡 CORRECTION : extraction du symbole robustifiée avec regex
        # "BTCEUR" → "BTC", "ETHUSDT" → "ETH", "ETHBTC" → "ETH"
        crypto = None
        if market:
            # On tente de retirer le suffixe de la paire (devise ou crypto de cotation)
            suffixes = r'(EUR|USD|USDT|USDC|BUSD|BTC|ETH|BNB)$'
            stripped = re.sub(suffixes, '', market).strip()
            if stripped:
                crypto = stripped
        if not crypto:
            crypto = str(row.get('asset') or row.get('crypto') or '').strip().upper() or None

        # Devise de cotation : EUR si la paire se termine par EUR, sinon USD, etc.
        if 'EUR' in market:
            currency = 'EUR'
        elif 'USD' in market:
            currency = 'USD'
        else:
            currency = str(row.get('currency') or 'UNKNOWN').upper()

        return {
            'date': (
                row.get('date(utc)') or row.get('date') or row.get('time')
            ),
            'operation_type': _normalize_op_type(op_raw),
            'crypto_token': crypto,
            'quantity': abs(clean_numeric(row.get('amount') or row.get('quantity'))),
            'price': clean_numeric(row.get('price')),
            'fees': clean_numeric(row.get('fee') or row.get('fees')),
            'currency': currency,
        }
    except Exception as exc:
        logger.debug("_parse_binance_row : %s", exc)
        return None


def _parse_kraken_row(row: dict) -> Optional[dict]:
    """Parse une ligne du CSV Kraken."""
    try:
        asset = str(row.get('asset') or row.get('pair') or '')

        # Kraken préfixe certains symboles avec X (crypto) ou Z (fiat)
        asset = re.sub(r'^X{1,2}|^Z', '', asset)

        op_raw = str(row.get('type') or row.get('tx_type') or '')

        return {
            'date': row.get('time') or row.get('date'),
            'operation_type': _normalize_op_type(op_raw),
            'crypto_token': asset.upper(),
            'quantity': abs(clean_numeric(
                row.get('amount') or row.get('vol') or row.get('quantity')
            )),
            'price': clean_numeric(row.get('price') or row.get('cost')),
            'fees': clean_numeric(row.get('fee') or 0),
            'currency': str(row.get('currency') or 'EUR').upper(),
        }
    except Exception as exc:
        logger.debug("_parse_kraken_row : %s", exc)
        return None


def _parse_generic_row(row: dict) -> Optional[dict]:
    """
    Parser générique : tente de mapper les colonnes les plus communes
    de n'importe quel export CSV crypto.
    """
    try:
        date = (
            row.get('date') or row.get('timestamp') or row.get('time')
            or row.get('created_at') or row.get('date(utc)')
            or row.get('transact_time') or row.get('heure')
        )
        op_raw = str(
            row.get('type') or row.get('operation_type')
            or row.get('operation') or row.get('side')
            or row.get("type d'opération") or row.get('transaction type')
            or ''
        )
        asset = (
            row.get('crypto_token') or row.get('crypto') or row.get('asset')
            or row.get('token') or row.get('symbol') or row.get('base_asset')
            or row.get('actif') or row.get('devise')
            # Binance-style : retirer la devise de cotation de la paire
            or re.sub(r'(EUR|USD|USDT|USDC|BUSD)$', '', str(row.get('market', ''))).strip()
            or None
        )
        quantity = (
            row.get('quantity') or row.get('amount') or row.get('amount_crypto')
            or row.get('executed') or row.get('filled') or row.get('quantité')
            or row.get('montant') or row.get('quantity transacted') or row.get('size')
        )
        price_candidates = [
            row.get('price'), row.get('value'), row.get('unit_price'),
            row.get('spot_price'), row.get('price at transaction'),
            row.get('prix'), row.get('valeur'),
        ]
        price_raw = next((v for v in price_candidates if v and clean_numeric(v) > 0), None)
        if price_raw is None:
            # Dernier recours : subtotal reconstitué
            subtotal_val = clean_numeric(row.get('subtotal') or 0)
            qty_check = abs(clean_numeric(quantity))
            if subtotal_val > 0 and qty_check > 0:
                price_raw = subtotal_val / qty_check
        fees = (
            row.get('fees') or row.get('fee') or row.get('transaction_fee')
            or row.get('fees and/or spread') or row.get('frais')
            or row.get('commission') or 0
        )
        currency = (
            row.get('currency') or row.get('price currency')
            or row.get('fiat') or row.get('quote_asset')
            or row.get('unité') or 'EUR'
        )
        acq_price = (
            row.get('acq_price') or row.get('acquisition_price')
            or row.get('prix_acquisition') or row.get("prix d'acquisition") or 0
        )

        return {
            'date': date,
            'operation_type': _normalize_op_type(op_raw),
            'crypto_token': str(asset).strip().upper() if asset else None,
            'quantity': abs(clean_numeric(quantity)),
            'price': clean_numeric(price_raw) if price_raw else 0.0,
            'acq_price': clean_numeric(acq_price),
            'fees': clean_numeric(fees),
            'currency': str(currency).upper().strip(),
        }
    except Exception as exc:
        logger.debug("_parse_generic_row : %s", exc)
        return None