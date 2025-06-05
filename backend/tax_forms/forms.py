from django import forms
from django.utils.translation import gettext_lazy as _

class Form2048(forms.Form):
    # Identification du déclarant
    nom = forms.CharField(label=_("Nom"), max_length=100, required=True)
    prenoms = forms.CharField(label=_("Prénoms"), max_length=100, required=True)
    adresse = forms.CharField(label=_("Adresse"), widget=forms.Textarea, required=True)

    # Champs pour les sessions (jusqu’à 5 sessions)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for i in range(1, 6):  # Remplace 'dies' par 'i'
            self.fields[f'date_session_{i}'] = forms.DateField(
                label=_("Date de la session {}").format(i),
                required=False,
                widget=forms.DateInput(attrs={'type': 'date'})
            )
            self.fields[f'valeur_globale_{i}'] = forms.DecimalField(
                label=_("Valeur globale du portefeuille au moment de la session {} (€)").format(i),
                required=False,
                decimal_places=2,
                max_digits=12
            )
            self.fields[f'prix_session_{i}'] = forms.DecimalField(
                label=_("Prix de session {} (€)").format(i),
                required=False,
                decimal_places=2,
                max_digits=12
            )
            self.fields[f'frais_session_{i}'] = forms.DecimalField(
                label=_("Frais de session {} (€)").format(i),
                required=False,
                decimal_places=2,
                max_digits=12,
                initial=0
            )
            self.fields[f'transaction_details_{i}'] = forms.CharField(
                label=_("Détails de la transaction pour la session {}").format(i),
                required=False,
                widget=forms.Textarea,
                help_text=_("Exemple : Bob vend 1 BTC")
            )

    # Champs pour l’importation automatique
    transaction_file = forms.FileField(
        label=_("Uploader un fichier de transactions (CSV)"),
        required=False
    )
    crypto_address = forms.CharField(
        label=_("Adresse crypto (EVM-compatible)"),
        max_length=42,
        required=False,
        help_text=_("Exemple : 0x1234567890abcdef1234567890abcdef12345678")
    )