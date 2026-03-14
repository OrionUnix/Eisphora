def calculate_french_taxes(transactions):
    """
    Calcule les plus-values selon le régime fiscal français.
    """
    
    portfolio = {} # { 'BTC': 1.5, 'ETH': 10 }
    total_acquisition_cost = 0.0 # Prix Total d'Acquisition (PTA)
    taxable_events = []
    global_plus_value = 0.0

    transactions.sort(key=lambda t: t['date'])

    for tx in transactions:
        op = tx['operation_type']
        crypto = tx['crypto_token']
        quantity = tx['quantity']
        price = tx['price']
        fees = tx['fees']
        
        if op == 'achat':
            portfolio[crypto] = portfolio.get(crypto, 0) + quantity
            cost = (quantity * price) + fees
            total_acquisition_cost += cost
            
        elif op == 'vente':
            if crypto in portfolio and portfolio[crypto] >= quantity:
                portfolio[crypto] -= quantity
                prix_cession = (quantity * price) - fees
                valeur_globale = prix_cession
                
                if valeur_globale > 0:
                    fraction = prix_cession / valeur_globale
                    pv = prix_cession - (total_acquisition_cost * fraction)
                    total_acquisition_cost = total_acquisition_cost - (total_acquisition_cost * fraction)
                else:
                    pv = 0
                    
                global_plus_value += pv
                
                taxable_events.append({
                    'date': tx['date'],
                    'crypto': crypto,
                    'quantity': quantity,
                    'prix_cession': prix_cession,
                    'valeur_globale_estimee': valeur_globale,
                    'plus_value': pv
                })
                
        elif op == 'echange':
            pass
            
    return {
        'total_plus_value': global_plus_value,
        'taxable_events': taxable_events,
        'final_acquisition_cost': total_acquisition_cost,
        'remaining_portfolio': portfolio
    }
