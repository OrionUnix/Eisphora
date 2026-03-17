from django.shortcuts import render
from django.contrib import messages
from .forms import Form2048
from django.utils.translation import gettext_lazy as _
from .services.extractor import parse_transaction_file, fetch_on_chain_transactions, parse_generic_row
from .services.calculator import calculate_french_taxes

def form_2048_view(request):
    print("Vue form_2048_view appelée pour", request.path)
    initial_data = {}

    if request.method == 'POST':
        form = Form2048(request.POST, request.FILES)
        if form.is_valid():
            sessions = []
            transaction_file = form.cleaned_data.get('transaction_file')
            crypto_address = form.cleaned_data.get('crypto_address')
            cex_dex = form.cleaned_data.get('cex_dex')

            all_transactions = []
            
            transaction_count = int(request.POST.get('transaction_count', 0))
            for i in range(1, transaction_count + 1):
                row = {
                    'date': request.POST.get(f'date_transaction_{i}'),
                    'type': request.POST.get(f'operation_type_{i}'),
                    'crypto': request.POST.get(f'crypto_token_{i}'),
                    'quantity': request.POST.get(f'quantity_{i}'),
                    'price': request.POST.get(f'price_{i}'),
                    'fees': request.POST.get(f'fees_{i}'),
                    'currency': request.POST.get(f'currency_{i}', 'EUR'),
                    'tx_hash': request.POST.get(f'tx_hash_{i}')
                }
                tx = parse_generic_row(row)
                if tx:
                    all_transactions.append(tx)

            if crypto_address:
                messages.info(request, _("Adresse crypto fournie. Récupération des transactions en cours..."))
                selected_blockchains = form.cleaned_data.get('blockchain', ['ethereum'])
                chain_txs = fetch_on_chain_transactions(crypto_address, blockchains=selected_blockchains)
                all_transactions.extend(chain_txs)
                
            if transaction_file:
                messages.info(request, _("Fichier de transactions reçu. Analyse sans sauvegarde disque..."))
                cex_txs = parse_transaction_file(transaction_file, cex_type=cex_dex or "generic")
                if not cex_txs:
                    messages.warning(request, _("Aucune transaction n'a pu être extraite du fichier. Vérifiez le format (CSV ou Excel)."))
                all_transactions.extend(cex_txs)

            # S'assurer que chaque transaction a un index pour le formulaire
            for idx, tx in enumerate(all_transactions):
                tx['index'] = idx + 1
                
            calc_results = calculate_french_taxes(all_transactions)
            taxable_profits = calc_results['total_plus_value']
            estimated_tax = max(0, taxable_profits * 0.30)  # PFU 12.8% IR + 17.2% PS
            estimated_tax_bareme = max(0, taxable_profits * (0.30 + 0.172))  # TMI 30% + 17.2% PS
            
            # Mapper les résultats de plus-value sur les transactions d'origine
            taxable_events_map = {event['id']: event for event in calc_results['taxable_events']}
            for tx in all_transactions:
                event = taxable_events_map.get(tx.get('index'))
                if event:
                    tx['plus_value'] = event['plus_value']
                    tx['prix_cession'] = event['prix_cession']
                    tx['prix_acquisition'] = event.get('prix_acquisition', 0)
                    tx['valeur_globale_estimee'] = event['valeur_globale_estimee']

            sessions = all_transactions
            taxable_events = calc_results['taxable_events']

            context = {
                'sessions': sessions,
                'taxable_events': taxable_events,
                'calc_results': calc_results,
                'form': form,
                'show_results': True,
                'taxable_profits': taxable_profits,
                'estimated_tax': estimated_tax,
                'estimated_tax_bareme': estimated_tax_bareme,
                'cex_dex': cex_dex,
                'manual_transactions': all_transactions,
            }
            print("Rendu de form_2048.html avec résultats")
            return render(request, 'tax_forms/form_2048.html', context)
        else:
            messages.error(request, _("Veuillez corriger les erreurs dans le formulaire."))
    else:
        form = Form2048(initial=initial_data)

    print("Rendu de form_2048.html sans résultats")
    return render(request, 'tax_forms/form_2048.html', {'form': form})