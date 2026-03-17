from django.test import TestCase
from unittest.mock import patch
from tax_forms.services.calculator import calculate_french_taxes
from datetime import datetime

class CalculatorTestCase(TestCase):
    def test_single_purchase_and_sale(self):
        """Test a simple purchase and subsequent sale of the same asset."""
        transactions = [
            {
                'date': '2023-01-01 10:00:00',
                'operation_type': 'achat',
                'crypto_token': 'BTC',
                'quantity': 1.0,
                'price': 20000.0,
                'fees': 100.0,
                'currency': 'EUR'
            },
            {
                'date': '2023-06-01 10:00:00',
                'operation_type': 'vente',
                'crypto_token': 'BTC',
                'quantity': 0.5,
                'price': 30000.0,
                'fees': 150.0,
                'currency': 'EUR'
            }
        ]
        
        results = calculate_french_taxes(transactions)
        
        # PTA = (1 * 20000) + 100 = 20100
        # Prix Cession Net = (0.5 * 30000) - 150 = 14850
        # Valeur Globale at sale time (only 1 BTC owned): 1 * 30000 = 30000
        # Fraction = 14850 / 30000 = 0.495
        # Prix Acq Fractionne = 20100 * 0.495 = 9949.5
        # PV = 14850 - 9949.5 = 4900.5
        
        self.assertEqual(len(results['taxable_events']), 1)
        event = results['taxable_events'][0]
        self.assertEqual(event['prix_cession'], 14850.0)
        self.assertEqual(event['valeur_globale_estimee'], 30000.0)
        self.assertEqual(event['prix_acquisition'], 9949.5)
        self.assertEqual(event['plus_value'], 4900.5)
        self.assertEqual(results['total_plus_value'], 4900.5)
        self.assertEqual(results['final_acquisition_cost'], 20100 - 9949.5)

    @patch('tax_forms.services.calculator.get_historical_price')
    def test_multi_asset_portfolio(self, mock_get_price):
        """Test sale when holding multiple types of assets."""
        # Mocking values for the sale date '2023-06-01'
        # BTC price is taken from the 'vente' transaction (40000)
        # ETH price needs to be fetched
        mock_get_price.return_value = 2000.0
        
        transactions = [
            {
                'date': '2023-01-01 10:00:00',
                'operation_type': 'achat',
                'crypto_token': 'BTC',
                'quantity': 1.0,
                'price': 20000.0,
                'fees': 0.0,
                'currency': 'EUR'
            },
            {
                'date': '2023-02-01 10:00:00',
                'operation_type': 'achat',
                'crypto_token': 'ETH',
                'quantity': 10.0,
                'price': 1000.0,
                'fees': 0.0,
                'currency': 'EUR'
            },
            {
                'date': '2023-06-01 10:00:00',
                'operation_type': 'vente',
                'crypto_token': 'BTC',
                'quantity': 1.0,
                'price': 40000.0,
                'fees': 0.0,
                'currency': 'EUR'
            }
        ]
        
        results = calculate_french_taxes(transactions)
        
        # PTA = 20000 + 10000 = 30000
        # Prix Cession Net = 40000
        # Valeur Globale at sale time: 
        #   (1 BTC * 40000) + (10 ETH * 2000) = 40000 + 20000 = 60000
        # Fraction = 40000 / 60000 = 2/3
        # Prix Acq Fractionne = 30000 * (2/3) = 20000
        # PV = 40000 - 20000 = 20000
        
        self.assertEqual(len(results['taxable_events']), 1)
        event = results['taxable_events'][0]
        self.assertEqual(event['valeur_globale_estimee'], 60000.0)
        self.assertEqual(event['prix_acquisition'], 20000.0)
        self.assertEqual(event['plus_value'], 20000.0)
        
        # Verify that get_historical_price was called for ETH but not for BTC (since BTC was the sold asset)
        mock_get_price.assert_called_with('ETH', '2023-06-01 10:00:00')
