import os
from django.shortcuts import render
from django.contrib import messages
from django.views.decorators.debug import sensitive_post_parameters
from .forms import Form2048
from django.utils.translation import gettext_lazy as _
from .services.extractor import parse_transaction_file, fetch_on_chain_transactions, parse_generic_row, get_historical_price, parse_custom_csv
from .services.calculator import calculate_french_taxes, get_pfu_rate


@sensitive_post_parameters('transaction_files', 'crypto_address', 'custom_mapping_json')
def form_2048_view(request):

    if request.method == 'POST':
        form = Form2048(request.POST, request.FILES)
        if form.is_valid():
            cex_dex = form.cleaned_data.get('cex_dex')
            crypto_addresses_raw = form.cleaned_data.get('crypto_address', '')
            # Lire les fichiers directement depuis request.FILES (évite conflits validation Django)
            transaction_files = request.FILES.getlist('transaction_files')

            all_transactions = []

            # --- 1. Transactions saisies manuellement dans le tableau ---
            transaction_count = int(request.POST.get('transaction_count', 0))
            for i in range(1, transaction_count + 1):
                row = {
                    'date': request.POST.get(f'date_transaction_{i}'),
                    'type': request.POST.get(f'operation_type_{i}'),
                    'crypto': request.POST.get(f'crypto_token_{i}'),
                    'quantity': request.POST.get(f'quantity_{i}'),
                    'price': request.POST.get(f'price_{i}'),
                    'acq_price': request.POST.get(f'acq_price_{i}', 0),
                    'fees': request.POST.get(f'fees_{i}'),
                    'currency': request.POST.get(f'currency_{i}', 'EUR'),
                    'source': request.POST.get(f'source_{i}', 'Manuel'),
                    'source_type': request.POST.get(f'source_type_{i}', 'Manuel')
                }
                tx = parse_generic_row(row)
                if tx:
                    tx['source'] = row['source']
                    tx['source_type'] = row['source_type']
                    all_transactions.append(tx)

            # --- 2. Adresses crypto (BTC, Tron, EVM — auto-détectées) ---
            if crypto_addresses_raw:
                addresses = [a.strip() for a in crypto_addresses_raw.splitlines() if a.strip()]
                for addr in addresses:
                    messages.info(request, _(f"Récupération des transactions pour {addr[:12]}..."))
                    chain_txs = fetch_on_chain_transactions(addr)
                    all_transactions.extend(chain_txs)

            # --- 3. Fichiers importés (CSV, XLS, XLSX, PDF — multi-fichiers) ---
            if transaction_files:
                mapping_json = request.POST.get('custom_mapping_json')
                custom_delimiter = request.POST.get('custom_mapping_delimiter', ',')

                for uploaded_file in transaction_files:
                    messages.info(request, _(f"Analyse du fichier : {uploaded_file.name}"))
                    
                    if mapping_json and uploaded_file.name.endswith('.csv'):
                        cex_txs = parse_custom_csv(uploaded_file, mapping_json, custom_delimiter)
                    else:
                        cex_txs = parse_transaction_file(uploaded_file, cex_type=cex_dex or "generic")
                        
                    if not cex_txs:
                        messages.warning(request, _(f"Aucune transaction extraite de {uploaded_file.name}. Vérifiez le format."))
                    else:
                        messages.success(request, _(f"{len(cex_txs)} transactions extraites de {uploaded_file.name}."))
                    all_transactions.extend(cex_txs)

            # --- Indexer toutes les transactions ---
            for idx, tx in enumerate(all_transactions):
                tx['index'] = idx + 1

            # --- Calcul fiscal ---
            calc_results = calculate_french_taxes(all_transactions)
            taxable_profits = calc_results.get('total_plus_value_imposable', 0)

            # PFU depuis tax_config.json
            pfu_rate = get_pfu_rate("2025")
            estimated_tax = max(0, taxable_profits * pfu_rate / 100)

            # Le barème progressif a été retiré pour simplification
            estimated_tax_bareme = 0

            # --- Mapper les résultats sur les transactions ---
            taxable_events_map = {event.get('id'): event for event in calc_results['taxable_events']}
            
            FIAT_CURRENCIES = {
                'EUR', 'USD', 'GBP', 'CHF', 'JPY', 'CAD', 'AUD', 'NZD',
                'NOK', 'SEK', 'DKK', 'HKD', 'SGD', 'KRW', 'BRL', 'MXN',
                'PLN', 'CZK', 'HUF', 'RON', 'BGN', 'TRY', 'ZAR', 'INR'
            }
            
            for tx in all_transactions:
                # Ensure every transaction has basic keys for the template
                tx.setdefault('acq_price', 0)
                tx.setdefault('price', 0)
                tx.setdefault('plus_value', 0)
                
                event = taxable_events_map.get(tx.get('index'))
                if event:
                    # Map calculation results back to the transaction
                    tx['plus_value'] = event.get('plus_value', 0)
                    tx['valeur_cession'] = event.get('prix_cession_net', 0)
                    tx['prix_cession'] = event.get('prix_cession_net', 0)
                    tx['prix_acquisition'] = event.get('prix_acq_fractionne', 0)
                    tx['valeur_globale_estimee'] = event.get('valeur_globale', 0)
                    
                    # Update acq_price and price for display if they were missing or 0
                    if not tx.get('acq_price'):
                        tx['acq_price'] = tx['prix_acquisition']
                    if not tx.get('price'):
                        tx['price'] = tx['prix_cession']

                # Marquer si la transaction doit être affichée dans le tableau des cessions
                tx['is_taxable_sale'] = (str(tx.get('operation_type')).lower() == 'vente' and 
                                         str(tx.get('currency', '')).upper() in FIAT_CURRENCIES)

            # --- Portfolio Distribution ---
            remaining_portfolio = calc_results.get('remaining_portfolio', {})
            portfolio_distribution = []
            total_portfolio_value = 0
            from datetime import datetime
            today_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            for asset, qty in remaining_portfolio.items():
                # Get current price for valuation
                price = get_historical_price(asset, today_str)
                val = qty * price
                if val > 0.01:  # Ignore dust
                    portfolio_distribution.append({
                        'asset': asset,
                        'qty': qty,
                        'price': price,
                        'value': val
                    })
                    total_portfolio_value += val

            # Calculate percentages
            if total_portfolio_value > 0:
                for item in portfolio_distribution:
                    item['percentage'] = round((item['value'] / total_portfolio_value) * 100, 1)
            
            # Sort by value
            portfolio_distribution = sorted(portfolio_distribution, key=lambda x: x['value'], reverse=True)

            # JSON encoding for the template
            import json
            portfolio_distribution_json = json.dumps(portfolio_distribution)

            # --- Sources Actives (Filtré pour la vue) ---
            sources_map = {}
            for tx in all_transactions:
                s_name = str(tx.get('source', ''))
                s_type = tx.get('source_type', 'Manuel')
                if s_name and s_name != 'Manuel' and s_name not in sources_map:
                    sources_map[s_name] = s_type
            
            unique_sources = []
            for name, stype in sources_map.items():
                unique_sources.append({'name': name, 'type': stype})
            
            unique_sources = sorted(unique_sources, key=lambda x: x['name'])

            context = {
                'sessions': all_transactions,
                'taxable_events': calc_results['taxable_events'],
                'calc_results': calc_results,
                'form': form,
                'show_results': True,
                'taxable_profits': taxable_profits,
                'estimated_tax': estimated_tax,
                'estimated_tax_bareme': estimated_tax_bareme,
                'pfu_rate': pfu_rate,
                'bareme_ir': 0,
                'bareme_ps': 0,
                'cex_dex': cex_dex,
                'manual_transactions': all_transactions,
                'file_count': len(transaction_files),
                'unique_sources': unique_sources,
                'portfolio_distribution': portfolio_distribution_json,
                'total_portfolio_value': total_portfolio_value,
                'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
            }
            return render(request, 'tax_forms/form_2048.html', context)
        else:
            messages.error(request, _("Veuillez corriger les erreurs dans le formulaire."))
    else:
        form = Form2048()

    return render(request, 'tax_forms/form_2048.html', {'form': form})