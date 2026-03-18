import json
import os
from datetime import datetime
from typing import List, Dict, Any

# Assure-toi que cette fonction existe bien dans ton projet
from tax_forms.services.extractor import get_historical_price

_TAX_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'tax_config.json')


def load_tax_config(year: str = "2026") -> dict:
    """Charge la configuration des taux fiscaux."""
    try:
        with open(_TAX_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Impossible de charger tax_config.json : {e}")
        return {}


def get_pfu_rate(year: str = "2026") -> float:
    """Taux PFU par défaut (ex: 30% en 2025, potentiellement 31.4% en 2026)."""
    config = load_tax_config(year)
    return config.get('pfu', {}).get(year, {}).get('total_rate', 30.0)


def get_ps_rate(year: str = "2026") -> float:
    """Taux des prélèvements sociaux."""
    config = load_tax_config(year)
    return config.get('bareme_progressif', {}).get(year, {}).get('ps_rate', 17.2)


def calculate_french_taxes(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcule les plus-values imposables crypto selon l'art. 150 VH bis du CGI.
    
    - Seules les cessions contre monnaie d'État (fiat) sont taxables.
    - Échanges crypto ↔ crypto : sursis d'imposition (PTA conservé, pas de PV).
    - Moins-values : elles s'imputent sur les plus-values de la même année.
    - Méthode : Prix Moyen Pondéré Global (PMP global).
    """
    portfolio: Dict[str, float] = {}               # crypto -> quantité détenue
    total_acquisition_cost: float = 0.0            # Prix Total d'Acquisition (PTA)
    total_prix_cession_imposable: float = 0.0      # Somme des cessions taxables
    taxable_events: List[Dict] = []
    global_plus_value: float = 0.0                 # Bilan net (Plus-values - Moins-values)

    price_cache: Dict[str, float] = {}             # Cache pour éviter de spammer l'API

    # 1. Tri chronologique robuste
    def parse_date(tx) -> datetime:
        d = tx.get('date')
        if not d:
            return datetime.min
        try:
            return datetime.fromisoformat(str(d).replace('Z', '+00:00'))
        except ValueError:
            try:
                return datetime.strptime(str(d), '%Y-%m-%d')
            except ValueError:
                return datetime.min

    transactions = sorted(transactions, key=parse_date)

    # 2. Traitement des transactions
    for idx, tx in enumerate(transactions):
        op = str(tx.get('operation_type', '')).lower().strip()
        crypto = str(tx.get('crypto_token', '')).strip().upper()

        if not crypto:
            continue

        # Sécurisation des données entrantes (gestion des floats)
        try:
            qty = float(tx.get('quantity') or 0)
            unit_price = float(tx.get('price') or 0)
            fees = float(tx.get('fees') or 0)
            date = tx.get('date')
        except (TypeError, ValueError):
            tx['remaining_quantity'] = portfolio.get(crypto, 0.0)
            continue

        if qty <= 0:
            tx['remaining_quantity'] = portfolio.get(crypto, 0.0)
            continue

        # ==========================================
        # OPÉRATION : ACHAT (Fiat -> Crypto)
        # ==========================================
        if op in ('achat', 'buy', 'acquisition', 'deposit_fiat'):
            cost = (qty * unit_price) + fees
            total_acquisition_cost += cost
            portfolio[crypto] = portfolio.get(crypto, 0.0) + qty
            tx['remaining_quantity'] = portfolio[crypto]

        # ==========================================
        # OPÉRATION : VENTE (Crypto -> Fiat)
        # ==========================================
        elif op in ('vente', 'sell', 'cession', 'fiat_withdrawal'):
            available = portfolio.get(crypto, 0.0)
            if available < qty:
                print(f"[WARN] Vente ignorée pour {crypto} : stock {available:.8f} < vente {qty:.8f}")
                tx['remaining_quantity'] = available
                continue

            # A. Calcul du Prix de Cession Net
            prix_cession_net = (qty * unit_price) - fees
            total_prix_cession_imposable += prix_cession_net

            # B. Calcul de la Valeur Globale du Portefeuille (VGP)
            valeur_globale = 0.0
            for asset, asset_qty in list(portfolio.items()):
                if asset_qty <= 0:
                    continue
                if asset == crypto:
                    p = unit_price
                else:
                    # Utilisation du cache pour optimiser les performances
                    cache_key = f"{asset}_{date}"
                    if cache_key not in price_cache:
                        try:
                            # On récupère le prix historique (ou 0 si introuvable)
                            price_cache[cache_key] = get_historical_price(asset, date) or 0.0
                        except Exception as e:
                            print(f"[ERR] Prix historique {asset} le {date} : {e}")
                            price_cache[cache_key] = 0.0
                    p = price_cache[cache_key]
                    
                valeur_globale += (asset_qty * p)

            # Sécurité : la VGP ne peut pas être inférieure au prix de cession
            valeur_globale = max(valeur_globale, prix_cession_net, 1e-6)

            # C. Calcul du Prix d'Acquisition Fractionné
            manual_acq = float(tx.get('acq_price') or 0)
            if manual_acq > 0:
                prix_acq_fractionne = qty * manual_acq
            else:
                fraction = prix_cession_net / valeur_globale
                prix_acq_fractionne = total_acquisition_cost * fraction

            # D. Calcul de la Plus-Value (PV) ou Moins-Value
            pv = prix_cession_net - prix_acq_fractionne
            
            # CORRECTION FISCALE : On additionne la PV, qu'elle soit positive ou négative.
            # Les moins-values s'imputent sur les plus-values de l'année.
            global_plus_value += pv

            # E. Mise à jour du PTA (Prix Total d'Acquisition) pour les ventes futures
            total_acquisition_cost = max(0.0, total_acquisition_cost - prix_acq_fractionne)

            # F. Mise à jour du portefeuille
            portfolio[crypto] -= qty
            if portfolio[crypto] <= 0:
                del portfolio[crypto]

            tx['remaining_quantity'] = portfolio.get(crypto, 0.0)

            # Enregistrement de l'événement imposable
            taxable_events.append({
                'id': tx.get('index') or idx + 1,
                'date': date,
                'type': 'Cession imposable',
                'crypto': crypto,
                'quantity': qty,
                'prix_cession_net': round(prix_cession_net, 2),
                'prix_acq_fractionne': round(prix_acq_fractionne, 2),
                'valeur_globale': round(valeur_globale, 2),
                'plus_value': round(pv, 2)
            })

        # ==========================================
        # OPÉRATION : ÉCHANGE (Crypto -> Crypto)
        # ==========================================
        elif op in ('echange', 'swap', 'exchange', 'transfert crypto', 'crypto_to_crypto'):
            available = portfolio.get(crypto, 0.0)
            if available < qty:
                print(f"[WARN] Échange ignoré pour {crypto} : stock {available:.8f} < échange {qty:.8f}")
                tx['remaining_quantity'] = available
                continue

            # 1. On retire la crypto cédée
            portfolio[crypto] -= qty
            if portfolio[crypto] <= 0:
                del portfolio[crypto]

            # 2. On ajoute la crypto reçue
            received_token = str(tx.get('received_token', '')).strip().upper()
            received_qty = float(tx.get('received_quantity') or 0)

            if received_token and received_qty > 0:
                portfolio[received_token] = portfolio.get(received_token, 0.0) + received_qty

            # CORRECTION FISCALE : En France, l'échange crypto-crypto est en sursis d'imposition.
            # Le PTA global (total_acquisition_cost) ne doit absolument pas être modifié ici !
            
            tx['remaining_quantity'] = portfolio.get(crypto, 0.0)

        # ==========================================
        # AUTRES OPÉRATIONS (Transfert intra-wallet, etc.)
        # ==========================================
        else:
            tx['remaining_quantity'] = portfolio.get(crypto, 0.0)

    # 3. Nettoyage final du portfolio (on supprime les micro-poussières)
    portfolio = {k: v for k, v in portfolio.items() if v > 1e-8}

    return {
        'total_plus_value_imposable': round(global_plus_value, 2),
        'total_prix_cession_imposable': round(total_prix_cession_imposable, 2),
        'taxable_events': taxable_events,
        'remaining_acquisition_cost': round(total_acquisition_cost, 2),
        'remaining_portfolio': {k: round(v, 8) for k, v in portfolio.items()},
        'note_fiscale': (
            "Régime art. 150 VH bis – Échanges crypto↔crypto non imposables (sursis). "
            "Les moins-values de l'année compensent les plus-values de l'année."
        )
    }