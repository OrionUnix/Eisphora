def calculate_french_taxes(transactions):
    """
    Calcule les plus-values selon le régime fiscal français des actifs numériques (depuis 2019).
    Règle : Les échanges Crypto -> Crypto ne sont pas imposables.
    Les échanges Crypto -> Fiat (EUR/USD) ou les achats de biens sont des évènements imposables.
    
    Formule Plus-Value :
    PV = Prix de Cession - (Prix Total d'Acquisition * (Prix de Cession / Valeur Globale du Portefeuille))
    """
    
    portfolio = {} # { 'BTC': 1.5, 'ETH': 10 }
    total_acquisition_cost = 0.0 # Prix Total d'Acquisition (PTA)
    taxable_events = []
    global_plus_value = 0.0

    # Sort chronologically to simulate the portfolio state at each point in time
    transactions.sort(key=lambda t: t['date'])

    for tx in transactions:
        op = tx['operation_type']
        crypto = tx['crypto_token']
        quantity = tx['quantity']
        price = tx['price']
        fees = tx['fees']
        
        if op == 'achat':
            # Fiat -> Crypto
            # Increase portfolio quantity
            portfolio[crypto] = portfolio.get(crypto, 0) + quantity
            # Increase total acquisition cost (price per unit * quantity + fees)
            cost = (quantity * price) + fees
            total_acquisition_cost += cost
            
        elif op == 'vente':
            # Crypto -> Fiat (Taxable Event)
            if crypto in portfolio and portfolio[crypto] >= quantity:
                portfolio[crypto] -= quantity
                
                # Prix de Cession (net des frais)
                prix_cession = (quantity * price) - fees
                
                # Valeur Globale du Portefeuille (VGP) au moment de la vente
                # Problème: Dans un cas réel, il faut connaître le prix exact de CHAQUE crypto du portfolio.
                # Pour cette démo statique, on va estimer la VGP en utilisant le prix de cession 
                # pour la crypto vendue, et ignorer les autres (ou demander à l'utilisateur).
                # Ici nous utilisons une approximation: on suppose que la seule valeur qu'on a est celle qu'on vient de vendre
                # Si l'utilisateur saisit une VGP globale, on l'utiliserait.
                valeur_globale = prix_cession  # Simplified for MVP without historic price APIs
                
                # Si on a d'autres cryptos, on les ajoute à la valeur globale avec une estimation (dernier prix connu)
                # (Simulé ici par une fraction pure si la valeur_globale est juste le montant vendu)
                
                # Formule officielle
                if valeur_globale > 0:
                    fraction = prix_cession / valeur_globale
                    pv = prix_cession - (total_acquisition_cost * fraction)
                    
                    # Mise à jour du PTA après la vente
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
            # Crypto -> Crypto (Non imposable en France)
            # Les quantités changent, mais le PTA ne bouge pas.
            pass
            
    return {
        'total_plus_value': global_plus_value,
        'taxable_events': taxable_events,
        'final_acquisition_cost': total_acquisition_cost,
        'remaining_portfolio': portfolio
    }
