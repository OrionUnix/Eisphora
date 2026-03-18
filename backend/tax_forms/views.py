import os
from django.shortcuts import render
from django.contrib import messages
from .forms import Form2048
from django.utils.translation import gettext_lazy as _
from .services.extractor import parse_transaction_file, fetch_on_chain_transactions, parse_generic_row
from .services.calculator import calculate_french_taxes, calculate_bareme_progressif, get_pfu_rate


def form_2048_view(request):
    print("Vue form_2048_view appelée pour", request.path)

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
                    'fees': request.POST.get(f'fees_{i}'),
                    'currency': request.POST.get(f'currency_{i}', 'EUR'),
                    'tx_hash': request.POST.get(f'tx_hash_{i}')
                }
                tx = parse_generic_row(row)
                if tx:
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
                for uploaded_file in transaction_files:
                    print(f"Processing file: {uploaded_file.name} ({uploaded_file.size} bytes)")
                    messages.info(request, _(f"Analyse du fichier : {uploaded_file.name}"))
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
            taxable_profits = calc_results['total_plus_value']

            # PFU depuis tax_config.json
            pfu_rate = get_pfu_rate("2025")
            estimated_tax = max(0, taxable_profits * pfu_rate / 100)

            # Barème progressif — TMI 30% par défaut (le plus courant)
            bareme_result = calculate_bareme_progressif(taxable_profits, tmi_rate=30, year="2025")
            estimated_tax_bareme = bareme_result['total']

            # --- Mapper les résultats sur les transactions ---
            taxable_events_map = {event['id']: event for event in calc_results['taxable_events']}
            for tx in all_transactions:
                event = taxable_events_map.get(tx.get('index'))
                if event:
                    tx['plus_value'] = event['plus_value']
                    tx['prix_cession'] = event['prix_cession']
                    tx['prix_acquisition'] = event.get('prix_acquisition', 0)
                    tx['valeur_globale_estimee'] = event['valeur_globale_estimee']

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
                'bareme_ir': bareme_result['ir'],
                'bareme_ps': bareme_result['ps'],
                'cex_dex': cex_dex,
                'manual_transactions': all_transactions,
                'file_count': len(transaction_files),
                'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
            }
            print(f"Rendu de form_2048.html avec {len(all_transactions)} transactions ({len(transaction_files)} fichiers)")
            return render(request, 'tax_forms/form_2048.html', context)
        else:
            print("Form errors:", form.errors)
            messages.error(request, _("Veuillez corriger les erreurs dans le formulaire."))
    else:
        form = Form2048()

    print("Rendu de form_2048.html sans résultats")
    return render(request, 'tax_forms/form_2048.html', {'form': form})