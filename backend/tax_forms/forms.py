from django import forms
from django.utils.translation import gettext_lazy as _


class Form2048(forms.Form):
    """
    Formulaire principal — les fichiers sont lus directement depuis request.FILES
    côté vue (request.FILES.getlist('transaction_files')), sans passer par la
    validation Django pour éviter les conflits avec l'upload multiple.
    """
    crypto_address = forms.CharField(
        label=_("Adresse(s) crypto (BTC, Tron, EVM…)"),
        max_length=2000,
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': '0x... (EVM)\nbc1... (Bitcoin)\nT... (Tron)\n(une adresse par ligne)'
        }),
        help_text=_("La blockchain est détectée automatiquement. Entrez une adresse par ligne.")
    )
    cex_dex = forms.ChoiceField(
        label=_("CEX/DEX / Format du fichier"),
        choices=[
            ("", "--- Auto-détection ---"),
            ("binance", "Binance"),
            ("kraken", "Kraken"),
            ("coinbase", "Coinbase"),
            ("cryptocom", "Crypto.com"),
            ("kucoin", "KuCoin"),
            ("bybit", "Bybit"),
            ("uniswap", "Uniswap"),
        ],
        required=False,
        help_text=_("Optionnel : précisez le format pour améliorer le parsing.")
    )