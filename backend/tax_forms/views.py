from django.shortcuts import render
from django.contrib import messages
from .forms import Form2048
from django.utils.translation import gettext_lazy as _
from .services.extractor import parse_csv_file, fetch_on_chain_transactions, parse_generic_row
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
            
            # 1. Gestion des transactions manuelles
            transaction_count = int(request.POST.get('transaction_count', 0))
            for i in range(1, transaction_count + 1):
                row = {
                    'date': request.POST.get(f'date_transaction_{i}'),
                    'type': request.POST.get(f'operation_type_{i}'),
                    'crypto': request.POST.get(f'crypto_token_{i}'),
                    'quantity': request.POST.get(f'quantity_{i}'),
                    'price': request.POST.get(f'price_{i}'),
                    'fees': request.POST.get(f'fees_{i}'),
                    'currency': request.POST.get(f'currency_{i}', 'EUR')
                }
                tx = parse_generic_row(row)
                if tx:
                    all_transactions.append(tx)

            # 2. Gestion API Blockchain
            if crypto_address:
                messages.info(request, _("Adresse crypto fournie. Récupération des transactions en cours..."))
                chain_txs = fetch_on_chain_transactions(crypto_address)
                all_transactions.extend(chain_txs)
                
            # 3. Gestion Fichier CEX (en mémoire uniquement)
            if transaction_file:
                messages.info(request, _("Fichier de transactions reçu. Analyse sans sauvegarde disque..."))
                cex_txs = parse_csv_file(transaction_file, cex_type=cex_dex or "generic")
                all_transactions.extend(cex_txs)
                
            # 4. Calcul de l'imposition française
            calc_results = calculate_french_taxes(all_transactions)
            taxable_profits = calc_results['total_plus_value']
            
            # Pour l'affichage, on combine:
            sessions = all_transactions # On garde l'historique de toutes les opérations pour le tableau
            taxable_events = calc_results['taxable_events']



            context = {
                'sessions': sessions,
                'taxable_events': taxable_events,
                'calc_results': calc_results,
                'form': form,
                'show_results': True,
                'taxable_profits': taxable_profits,
                'cex_dex': cex_dex,
            }
            print("Rendu de form_2048.html avec résultats")
            return render(request, 'tax_forms/form_2048.html', context)
        else:
            messages.error(request, _("Veuillez corriger les erreurs dans le formulaire."))
    else:
        form = Form2048(initial=initial_data)

    print("Rendu de form_2048.html sans résultats")
    return render(request, 'tax_forms/form_2048.html', {'form': form})