import json
import os
from tax_forms.services.extractor import get_historical_price

# Charger la configuration fiscale
_TAX_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'tax_config.json')

def load_tax_config(year: str = "2025") -> dict:
    """Charge les taux fiscaux depuis tax_config.json."""
    try:
        with open(_TAX_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Warning: could not load tax_config.json: {e}")
        return {}

def get_pfu_rate(year: str = "2025") -> float:
    """Retourne le taux total PFU pour l'année donnée (défaut 30%)."""
    config = load_tax_config(year)
    return config.get('pfu', {}).get(year, {}).get('total_rate', 30.0)

def get_ps_rate(year: str = "2025") -> float:
    """Retourne le taux de prélèvements sociaux (défaut 17.2%)."""
    config = load_tax_config(year)
    return config.get('bareme_progressif', {}).get(year, {}).get('ps_rate', 17.2)

def calculate_bareme_progressif(gains: float, tmi_rate: float, year: str = "2025") -> dict:
    """
    Calcule l'impôt selon le barème progressif français.
    
    Le barème progressif s'applique à la totalité du revenu fiscal de référence du
    foyer, pas seulement aux gains crypto. Ce calcul est une ESTIMATION pour les
    gains crypto seuls (calcul simplifié).
    
    Returns:
        dict avec 'ir' (IR sur gains), 'ps' (prélèvements sociaux), 'total'
    """
    if gains <= 0:
        return {'ir': 0.0, 'ps': 0.0, 'total': 0.0, 'tmi': tmi_rate}
    
    config = load_tax_config(year)
    tranches = config.get('bareme_progressif', {}).get(year, {}).get('tranches', [])
    ps_rate = config.get('bareme_progressif', {}).get(year, {}).get('ps_rate', 17.2)
    
    if not tranches:
        # Fallback si config absente
        ir = gains * tmi_rate / 100
        ps = gains * ps_rate / 100
        return {'ir': ir, 'ps': ps, 'total': ir + ps, 'tmi': tmi_rate}
    
    # Calcul progressif réel sur les gains (estimation crypto seule)
    ir = 0.0
    remaining = gains
    for tranche in sorted(tranches, key=lambda t: t['min']):
        t_min = tranche['min']
        t_max = tranche['max']  # None = pas de plafond
        rate = tranche['rate'] / 100
        
        if t_max is None:
            # Dernière tranche : sans plafond
            if remaining > 0 and gains > t_min:
                amount_in_tranche = max(0, gains - t_min) if t_min == 0 else gains - t_min
                ir += max(0, min(remaining, amount_in_tranche)) * rate
                remaining = 0
        else:
            tranche_width = t_max - t_min + 1
            amount_in_tranche = min(remaining, tranche_width)
            if amount_in_tranche > 0:
                ir += amount_in_tranche * rate
                remaining -= amount_in_tranche
        
        if remaining <= 0:
            break
    
    ps = gains * ps_rate / 100
    return {
        'ir': round(ir, 2),
        'ps': round(ps, 2),
        'total': round(ir + ps, 2),
        'tmi': tmi_rate,
        'ps_rate': ps_rate
    }


def calculate_french_taxes(transactions):
    """
    Calcule les plus-values selon le régime fiscal français (Article 150 VH bis).
    """
    
    portfolio = {} # { 'BTC': 1.5, 'ETH': 10 }
    total_acquisition_cost = 0.0 # Prix Total d'Acquisition (PTA)
    total_prix_cession = 0.0
    taxable_events = []
    global_plus_value = 0.0

    # Tri robuste : gère les dates None ou invalides
    transactions.sort(key=lambda t: str(t.get('date') or ''))

    for idx, tx in enumerate(transactions):
        op = tx['operation_type']
        crypto = tx['crypto_token']
        quantity = tx['quantity']
        price = tx['price']
        fees = tx['fees']
        date = tx.get('date')
        
        if op == 'achat':
            portfolio[crypto] = portfolio.get(crypto, 0) + quantity
            cost = (quantity * price) + fees
            total_acquisition_cost += cost
            tx['remaining_quantity'] = portfolio[crypto]
            
        elif op == 'vente':
            if crypto in portfolio and portfolio[crypto] >= quantity:
                # 1. Calcul du Prix de Cession Net
                prix_cession_net = (quantity * price) - fees
                total_prix_cession += prix_cession_net
                
                # 2. Calcul de la Valeur Globale du Portefeuille à l'instant T
                # On doit valoriser chaque actif détenu au prix du marché au moment de la vente
                valeur_globale = 0.0
                for p_crypto, p_quantity in portfolio.items():
                    if p_quantity > 0:
                        # Si c'est l'actif vendu, on connaît déjà son prix (le prix de la transaction)
                        if p_crypto == crypto:
                            p_price = price
                        else:
                            # Sinon, on récupère le prix historique
                            p_price = get_historical_price(p_crypto, date)
                        
                        valeur_globale += (p_quantity * p_price)
                
                # S'assurer que la valeur globale n'est pas inférieure au prix de cession
                valeur_globale = max(valeur_globale, prix_cession_net)
                
                # 3. Calcul de l'Abattement (Prix d'Acquisition Fractionné)
                if valeur_globale > 0:
                    fraction = prix_cession_net / valeur_globale
                    prix_acq_fractionne = total_acquisition_cost * fraction
                    pv = prix_cession_net - prix_acq_fractionne
                    
                    # Mise à jour du PTA pour la suite
                    total_acquisition_cost -= prix_acq_fractionne
                else:
                    pv = 0
                    prix_acq_fractionne = 0
                
                # Mise à jour du portfolio APRES le calcul de la valeur globale
                portfolio[crypto] -= quantity
                tx['remaining_quantity'] = portfolio[crypto]
                    
                global_plus_value += pv
                
                taxable_events.append({
                    'id': tx.get('index') or idx + 1,
                    'date': date,
                    'crypto': crypto,
                    'quantity': quantity,
                    'prix_cession': prix_cession_net,
                    'prix_acquisition': prix_acq_fractionne,
                    'valeur_globale_estimee': valeur_globale,
                    'plus_value': pv
                })
            else:
                tx['remaining_quantity'] = portfolio.get(crypto, 0)
                
        elif op == 'echange':
            # Note: En France, un échange crypto-crypto n'est pas imposable.
            # Cependant, il change la composition du portefeuille mais pas le PTA global.
            tx['remaining_quantity'] = portfolio.get(crypto, 0)
            pass
        else:
            tx['remaining_quantity'] = portfolio.get(crypto, 0)
            
    return {
        'total_plus_value': global_plus_value,
        'total_prix_cession': total_prix_cession,
        'taxable_events': taxable_events,
        'final_acquisition_cost': total_acquisition_cost,
        'remaining_portfolio': portfolio
    }
