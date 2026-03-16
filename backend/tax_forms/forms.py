from django import forms
from django.utils.translation import gettext_lazy as _

class Form2048(forms.Form):
    # Champs pour les transactions manuelles 
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
    cex_dex = forms.ChoiceField(
        label=_("CEX/DEX utilisé"),
        choices=[
            ("", "-------"), 
            ("binance", "Binance"), 
            ("kraken", "Kraken"), 
            ("coinbase", "Coinbase"),
            ("cryptocom", "Crypto.com"),
            ("kucoin", "KuCoin"),
            ("bybit", "Bybit"),
            ("uniswap", "Uniswap")
        ],
        required=False,
        help_text=_("Indiquez la plateforme utilisée pour cette transaction.")
    )
    blockchain = forms.MultipleChoiceField(
        label=_("Blockchains (EVM)"),
        choices=[
            ("ethereum", "Ethereum"),
            ("polygon", "Polygon"),
            ("bsc", "Binance Smart Chain"),
            ("avalanche", "Avalanche"),
            ("fantom", "Fantom"),
            ("arbitrum", "Arbitrum"),
            ("optimism", "Optimism")
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        initial=["ethereum"]
    )