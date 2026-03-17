from tax_forms.services.extractor import get_historical_price

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
