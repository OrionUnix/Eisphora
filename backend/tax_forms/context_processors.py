from tax_forms.services.calculator import get_exoneration_threshold, load_tax_config

def fiscal_config(request):
    config = load_tax_config()
    pfu_config = config.get('pfu', {})
    bareme_config = config.get('bareme_progressif', {})
    
    return {
        'exoneration_seuil': get_exoneration_threshold(),
        'pfu_total_rate': pfu_config.get('total_rate', 31.4),
        'pfu_ir_rate': pfu_config.get('ir_rate', 12.8),
        'pfu_ps_rate': pfu_config.get('ps_rate', 18.6),
        'ps_rate_bareme': bareme_config.get('ps_rate', 18.6),
    }
