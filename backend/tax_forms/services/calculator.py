def calculate_french_taxes(transactions):
    """
    Calcule les plus-values selon le régime fiscal français.
    """
    
    portfolio = {} # { 'BTC': 1.5, 'ETH': 10 }
    total_acquisition_cost = 0.0 # Prix Total d'Acquisition (PTA)
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
        
        if op == 'achat':
            portfolio[crypto] = portfolio.get(crypto, 0) + quantity
            cost = (quantity * price) + fees
            total_acquisition_cost += cost
            tx['remaining_quantity'] = portfolio[crypto]
            
        elif op == 'vente':
            if crypto in portfolio and portfolio[crypto] >= quantity:
                portfolio[crypto] -= quantity
                tx['remaining_quantity'] = portfolio[crypto]
                prix_cession = (quantity * price) - fees
                valeur_globale = prix_cession
                
                if valeur_globale > 0:
                    fraction = prix_cession / valeur_globale
                    prix_acq = total_acquisition_cost * fraction
                    pv = prix_cession - prix_acq
                    total_acquisition_cost = total_acquisition_cost - prix_acq
                else:
                    pv = 0
                    prix_acq = 0
                    
                global_plus_value += pv
                
                taxable_events.append({
                    'id': idx + 1,
                    'date': tx['date'],
                    'crypto': crypto,
                    'quantity': quantity,
                    'prix_cession': prix_cession,
                    'prix_acquisition': prix_acq,
                    'valeur_globale_estimee': valeur_globale,
                    'plus_value': pv
                })
            else:
                tx['remaining_quantity'] = portfolio.get(crypto, 0)
                
        elif op == 'echange':
            tx['remaining_quantity'] = portfolio.get(crypto, 0)
            pass
        else:
            tx['remaining_quantity'] = portfolio.get(crypto, 0)
            
    return {
        'total_plus_value': global_plus_value,
        'taxable_events': taxable_events,
        'final_acquisition_cost': total_acquisition_cost,
        'remaining_portfolio': portfolio
    }
