from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import Form2048
from django.utils.translation import gettext_lazy as _

def form_2048_view(request):
    print("Vue form_2048_view appelée pour", request.path)  # Débogage
    initial_data = {}

    if request.method == 'POST':
        form = Form2048(request.POST, request.FILES)
        if form.is_valid():
            nom = form.cleaned_data['nom']
            prenoms = form.cleaned_data['prenoms']
            adresse = form.cleaned_data['adresse']

            sessions = []
            for i in range(1, 6):
                session_data = {
                    'date': form.cleaned_data.get(f'date_session_{i}'),
                    'valeur_globale': form.cleaned_data.get(f'valeur_globale_{i}'),
                    'prix_session': form.cleaned_data.get(f'prix_session_{i}'),
                    'frais_session': form.cleaned_data.get(f'frais_session_{i}'),
                    'transaction_details': form.cleaned_data.get(f'transaction_details_{i}'),
                }
                if any(session_data.values()):
                    prix_session = session_data['prix_session'] or 0
                    frais_session = session_data['frais_session'] or 0
                    session_data['prix_session_net'] = prix_session - frais_session
                    sessions.append(session_data)

            transaction_file = form.cleaned_data.get('transaction_file')
            crypto_address = form.cleaned_data.get('crypto_address')

            if transaction_file:
                messages.info(request, _("Fichier de transactions reçu. Traitement en cours..."))
            elif crypto_address:
                messages.info(request, _("Adresse crypto fournie. Récupération des transactions en cours..."))

            context = {
                'nom': nom,
                'prenoms': prenoms,
                'adresse': adresse,
                'sessions': sessions,
            }
            print("Rendu de form_2048_result.html")  # Débogage
            return render(request, 'tax_forms/form_2048_result.html', context)
        else:
            messages.error(request, _("Veuillez corriger les erreurs dans le formulaire."))
    else:
        form = Form2048(initial=initial_data)

    print("Rendu de form_2048.html")  # Débogage
    return render(request, 'tax_forms/form_2048.html', {'form': form})