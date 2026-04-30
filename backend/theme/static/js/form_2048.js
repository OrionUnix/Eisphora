// --- FOCUS LIGNE (Stylo) ---
window.focusRow = function (btn) {
    const row = btn.closest('tr');
    const firstInput = row.querySelector('input[type="text"]');
    if (firstInput) firstInput.focus();

    row.classList.add('bg-indigo-100');
    setTimeout(() => {
        row.classList.remove('bg-indigo-100');
    }, 400);
};

// --- VALIDATION DATE ---
window.validateDate = function(input) {
    const val = input.value.trim();
    const statusDiv = input.nextElementSibling;
    if (!statusDiv || !statusDiv.classList.contains('date-status')) return;

    if (!val) {
        statusDiv.innerHTML = '';
        return;
    }

    const dateReg = /^(\d{4})-(\d{2})-(\d{2})/;
    const match = val.match(dateReg);

    if (match) {
        const year = parseInt(match[1]);
        const month = parseInt(match[2]);
        const day = parseInt(match[3]);

        if (month < 1 || month > 12 || day < 1 || day > 31) {
            statusDiv.innerHTML = '<span class="text-[9px] font-bold text-red-500 bg-red-50 px-1.5 py-0.5 rounded-md border border-red-100 flex items-center gap-1 w-max"><i class="fas fa-times-circle"></i> Date invalide</span>';
            return;
        }

        if (year === 2025) {
            statusDiv.innerHTML = '<span class="text-[9px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-md border border-emerald-100 flex items-center gap-1 w-max"><i class="fas fa-check-circle"></i> Fiscal 2025</span>';
        } else if (year < 2025) {
            statusDiv.innerHTML = '<span class="text-[9px] font-bold text-slate-400 bg-slate-50 px-1.5 py-0.5 rounded-md border border-slate-200 flex items-center gap-1 w-max"><i class="fas fa-history"></i> Antérieur</span>';
        } else {
            statusDiv.innerHTML = '<span class="text-[9px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded-md border border-amber-100 flex items-center gap-1 w-max">Futur</span>';
        }
    } else {
        statusDiv.innerHTML = '<span class="text-[9px] font-bold text-red-500 bg-red-50 px-1.5 py-0.5 rounded-md border border-red-100 flex items-center gap-1 w-max"><i class="fas fa-times-circle"></i> Format: YYYY-MM-DD</span>';
    }
};

// --- CONFIGURATION FISCALE DYNAMIQUE ---
window.TAX_CONFIG = null;
window.PS_RATE = 18.6;
window.PFU_TOTAL_RATE = 31.4;
window.EXONERATION_THRESHOLD = 305;
window.TRANCHES = [];
window.DECOTE_CONFIG = null;

window.loadTaxConfig = function() {
    try {
        const scriptEl = document.getElementById('tax-config-data');
        if (scriptEl && scriptEl.textContent.trim()) {
            window.TAX_CONFIG = JSON.parse(scriptEl.textContent);
            
            if (window.TAX_CONFIG.bareme_progressif) {
                const bConfig = window.TAX_CONFIG.bareme_progressif;
                window.PS_RATE = bConfig.ps_rate || 18.6;
                window.TRANCHES = bConfig.tranches || [];
                window.DECOTE_CONFIG = bConfig.decote || null;
            }
            if (window.TAX_CONFIG.pfu) {
                window.PFU_TOTAL_RATE = window.TAX_CONFIG.pfu.total_rate || 31.4;
            }
            if (window.TAX_CONFIG.exoneration_seuil) {
                window.EXONERATION_THRESHOLD = parseFloat(window.TAX_CONFIG.exoneration_seuil) || 305;
            }

            // Update UI elements if present
            const pfuInput = document.getElementById('pfu-rate');
            if (pfuInput) pfuInput.value = window.PFU_TOTAL_RATE;

            const psRateEl = document.getElementById('card-ps-rate');
            if (psRateEl) psRateEl.textContent = window.PS_RATE;

        }
    } catch (e) {
        console.error("Erreur chargement tax_config:", e);
    }
};

function calculIR(revenuNet, parts = 1.0) {
    if (!window.TRANCHES || window.TRANCHES.length === 0) return { impot: 0, tmi: 0 };

    const quotient = revenuNet / parts;
    let irPart = 0.0;
    let tmi = 0;
    
    for (const tranche of window.TRANCHES) {
        if (quotient <= tranche.min) break;
        const max = tranche.max !== null ? tranche.max : Infinity;
        const base = Math.min(quotient, max) - tranche.min;
        irPart += base * (tranche.rate / 100);
        if (base > 0) tmi = tranche.rate;
    }
    
    let impotBrut = irPart * parts;
    
    // Décote
    let decote = 0;
    if (window.DECOTE_CONFIG) {
        if (parts < 2) { // Célibataire
            if (impotBrut < window.DECOTE_CONFIG.seuil_celibataire) {
                decote = Math.max(0, 873 - (impotBrut * window.DECOTE_CONFIG.taux)); // On garde le 873 statique ou on peut l'améliorer
            }
        } else { // Couple
            if (impotBrut < window.DECOTE_CONFIG.seuil_couple) {
                decote = Math.max(0, 1444 - (impotBrut * window.DECOTE_CONFIG.taux));
            }
        }
    }
    
    return { 
        impot: Math.max(0, impotBrut - decote),
        tmi: tmi
    };
}

window.updateTaxes = function() {
    const taxDataEl = document.getElementById('tax-data');
    if (!taxDataEl) return;
    
    var taxableAmount = parseFloat(taxDataEl.dataset.gains) || 0;
    var totalCessions = parseFloat(taxDataEl.dataset.totalCessions) || 0;
    
    // Update Total Cessions Card
    var elTotalCessions = document.getElementById('val-total-cessions');
    var elExemptionMsg = document.getElementById('exemption-msg');
    
    if (elTotalCessions) {
        elTotalCessions.textContent = Math.round(totalCessions).toLocaleString('fr-FR') + ' €';
    }
    
    var isExempt = (totalCessions > 0 && totalCessions <= window.EXONERATION_THRESHOLD);
    
    if (elExemptionMsg) {
        if (isExempt) {
            elExemptionMsg.classList.remove('hidden');
            taxableAmount = 0; // Exonéré
        } else {
            elExemptionMsg.classList.add('hidden');
        }
    }

    var elPlus = document.getElementById('val-plus');
    var elMoins = document.getElementById('val-minus');

    if (taxableAmount >= 0) {
        if (elPlus) elPlus.textContent = "+ " + taxableAmount.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €";
        if (elMoins) elMoins.textContent = "- 0 €";
    } else {
        if (elPlus) elPlus.textContent = "+ 0 €";
        if (elMoins) elMoins.textContent = "- " + Math.abs(taxableAmount).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €";
    }

    if (taxableAmount <= 0) {
        var elPfuR = document.getElementById('val-pfu');
        var elBarR = document.getElementById('val-bareme');
        if (elPfuR) elPfuR.textContent = "0 €";
        if (elBarR) elBarR.textContent = "0 €";
        return;
    }

    var pfuTotal = taxableAmount * (window.PFU_TOTAL_RATE / 100);
    var elPfuResult = document.getElementById('val-pfu');
    if (elPfuResult) elPfuResult.textContent = Math.round(pfuTotal).toLocaleString('fr-FR') + ' €';

    // --- Calcul Barème Progressif Exact ---
    var revenuNet = parseFloat(document.getElementById('revenu-net')?.value) || 0;
    var nbParts = parseFloat(document.getElementById('nb-parts')?.value) || 1;

    var irSans = calculIR(revenuNet, nbParts);
    var irAvec = calculIR(revenuNet + taxableAmount, nbParts);

    // Delta IR + Prélèvements Sociaux
    var baremeTotal = (irAvec.impot - irSans.impot) + (taxableAmount * (window.PS_RATE / 100));
    
    var elBaremeResult = document.getElementById('val-bareme');
    if (elBaremeResult) elBaremeResult.textContent = Math.round(baremeTotal).toLocaleString('fr-FR') + ' €';

    // Mise à jour de la TMI affichée (visuel uniquement)
    var elTmiSelect = document.getElementById('bareme-rate');
    if (elTmiSelect) elTmiSelect.value = irAvec.tmi;

    // Badge styling
    updateTaxBadges(pfuTotal, baremeTotal);
};

function updateTaxBadges(pfuTotal, baremeTotal) {
    var badgePfu = document.getElementById('badge-pfu');
    var badgeBareme = document.getElementById('badge-bareme');
    var cardPfu = document.getElementById('card-pfu');
    var cardBareme = document.getElementById('card-bareme');
    var msgPfu = document.getElementById('pfu-msg');
    var msgBareme = document.getElementById('bareme-msg');

    // Reset all
    badgePfu?.classList.add('hidden');
    badgeBareme?.classList.add('hidden');
    msgPfu?.classList.add('hidden');
    msgBareme?.classList.add('hidden');
    cardPfu?.classList.remove('ring-4', 'ring-purple-400');
    cardBareme?.classList.remove('ring-4', 'ring-emerald-400');

    // If no tax, don't show "advantageous" message
    if (pfuTotal <= 0 && baremeTotal <= 0) return;

    if (pfuTotal <= baremeTotal) {
        badgePfu?.classList.remove('hidden');
        msgPfu?.classList.remove('hidden');
        cardPfu?.classList.add('ring-4', 'ring-purple-400');
    } else {
        badgeBareme?.classList.remove('hidden');
        msgBareme?.classList.remove('hidden');
        cardBareme?.classList.add('ring-4', 'ring-emerald-400');
    }
}

// --- GESTION DES FICHIERS (Drag & Drop) ---
let selectedFiles = new DataTransfer();

window.initFileUpload = function() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    if (!dropZone || !fileInput) return;

    dropZone.onclick = () => fileInput.click();

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('border-[#7c5cbf]', 'bg-purple-50/50');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('border-[#7c5cbf]', 'bg-purple-50/50');
        });
    });

    dropZone.addEventListener('drop', (e) => { handleFiles(e.dataTransfer.files, fileInput); });
    fileInput.addEventListener('change', (e) => { handleFiles(e.target.files, fileInput); });
};

function handleFiles(files, input) {
    for (let f of files) { selectedFiles.items.add(f); }
    input.files = selectedFiles.files;
    renderFileChips();
}

window.removeFile = function(fileName) {
    const fileInput = document.getElementById('file-input');
    let dt = new DataTransfer();
    for (let f of selectedFiles.files) { if (f.name !== fileName) dt.items.add(f); }
    selectedFiles = dt;
    fileInput.files = selectedFiles.files;
    renderFileChips();
};

function renderFileChips() {
    const container = document.getElementById('file-chips');
    if (!container) return;
    container.innerHTML = '';
    for (let f of selectedFiles.files) {
        const chip = document.createElement('div');
        chip.className = 'flex items-center gap-1.5 md:gap-2 px-2 py-1 md:px-3 md:py-1.5 rounded-lg text-[10px] md:text-xs font-bold bg-[#7c5cbf]/10 border border-[#7c5cbf]/20 text-[#7c5cbf] shadow-sm max-w-full';
        const shortName = f.name.length > 15 ? f.name.substring(0, 15) + '...' : f.name;
        chip.innerHTML = `<i class="fas fa-file-alt shrink-0"></i><span class="truncate">${shortName}</span><button type="button" onclick="removeFile('${f.name}')" class="ml-1 hover:text-red-500 transition-colors shrink-0 p-1"><i class="fas fa-times"></i></button>`;
        container.appendChild(chip);
    }
}

// --- DÉTECTION DES WALLETS ---
window.initWalletDetection = function() {
    const walletInput = document.getElementById('id_crypto_address');
    const networkBadge = document.getElementById('network-badge');
    const networkText = document.getElementById('network-text');
    if (!walletInput || !networkBadge) return;

    walletInput.addEventListener('input', function () {
        const addresses = this.value.split('\n').map(a => a.trim()).filter(Boolean);
        if (addresses.length === 0) { networkBadge.classList.add('hidden'); return; }

        const addr = addresses[0];
        let type = '';
        if (/^0x[0-9a-fA-F]{40}$/.test(addr)) type = 'EVM (ETH/BSC)';
        else if (/^(1|3)[a-km-zA-HJ-NP-Z1-9]{25,34}$/.test(addr) || /^bc1[a-z0-9]{25,90}$/.test(addr)) type = 'Bitcoin';
        else if (/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(addr)) type = 'Solana';
        else if (/^T[A-Za-z1-9]{33}$/.test(addr)) type = 'Tron';
        else type = 'Inconnu';

        networkText.innerText = type;
        networkBadge.classList.remove('hidden');
        if (type === 'Inconnu') {
            networkBadge.classList.replace('text-[#7c5cbf]', 'text-slate-500');
            networkBadge.classList.replace('bg-[#7c5cbf]/10', 'bg-slate-100');
        } else {
            networkBadge.classList.replace('text-slate-500', 'text-[#7c5cbf]');
            networkBadge.classList.replace('bg-slate-100', 'bg-[#7c5cbf]/10');
        }
    });
};

// --- LOGIQUE TABLEAU MANUEL & PAGINATION ---
let currentPage = 1;
let rowsPerPage = 50;

window.updateRowStyle = function(select) {
    const type = select.value;
    select.classList.remove('bg-blue-50', 'text-blue-700', 'bg-orange-50', 'text-orange-700', 'bg-slate-100', 'text-slate-600');
    if (type === 'achat') select.classList.add('bg-blue-50', 'text-blue-700');
    else if (type === 'vente') select.classList.add('bg-orange-50', 'text-orange-700');
    else select.classList.add('bg-slate-100', 'text-slate-600');
    
    // Update the indicator count
    if (typeof updateTaxableCount === 'function') updateTaxableCount();
};

window.recalculateGlobalGains = function() {
    let totalGain = 0;
    let totalSalePrice = 0;
    const rows = document.querySelectorAll('.transaction-row');
    
    rows.forEach(row => {
        const typeElement = row.querySelector('[name^="operation_type_"]');
        const type = typeElement ? typeElement.value : 'transfert';
        
        if (type === 'vente') {
            const qty = parseFloat(row.querySelector('input[name^="quantity_"]').value) || 0;
            const price = parseFloat(row.querySelector('input[name^="price_"]').value) || 0;
            const acqPrice = parseFloat(row.querySelector('input[name^="acq_price_"]').value) || 0;
            
            const salePrice = qty * price;
            const gain = salePrice - (qty * acqPrice);
            
            totalGain += gain;
            totalSalePrice += salePrice;
        }
    });

    const taxDataEl = document.getElementById('tax-data');
    if (taxDataEl) {
        taxDataEl.dataset.gains = totalGain;
        taxDataEl.dataset.totalCessions = totalSalePrice;
    }
    updateTaxes();
};

window.updateRowTotal = function(input) {
    const row = input.closest('tr');
    if (!row) return;
    const qty = parseFloat(row.querySelector('input[name^="quantity_"]').value) || 0;
    const price = parseFloat(row.querySelector('input[name^="price_"]').value) || 0;
    const acqPrice = parseFloat(row.querySelector('input[name^="acq_price_"]').value) || 0;
    const typeElement = row.querySelector('[name^="operation_type_"]');
    const type = typeElement ? typeElement.value : 'transfert';

    const total = qty * price;
    row.querySelector('.row-total').textContent = total.toLocaleString('fr-FR', { minimumFractionDigits: 2 }) + ' €';

    const gainEl = row.querySelector('.row-gain');
    if (!gainEl) return;

    if (type === 'vente') {
        const cost = qty * acqPrice;
        const gain = total - cost;
        gainEl.textContent = (gain > 0 ? '+ ' : '') + gain.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';
        gainEl.classList.toggle('text-emerald-600', gain > 0);
        gainEl.classList.toggle('text-red-500', gain < 0);
        gainEl.classList.toggle('text-slate-400', gain === 0);
    } else {
        gainEl.textContent = '-- €';
        gainEl.classList.remove('text-emerald-600', 'text-red-500');
        gainEl.classList.add('text-slate-400');
    }

    recalculateGlobalGains();
};

window.updatePagination = function() {
    const allRows = document.querySelectorAll('.transaction-row');
    const visibleRows = Array.from(allRows).filter(row => !row.classList.contains('hidden-tx-row'));
    const total = visibleRows.length;
    
    const emptyState = document.getElementById('tx-empty-state');
    const tableContainer = document.getElementById('tx-table-container');
    const paginationContainer = document.getElementById('pagination-container');

    if (total === 0) {
        emptyState?.classList.remove('hidden');
        tableContainer?.classList.add('hidden');
        paginationContainer?.classList.add('hidden');
        return;
    }

    emptyState?.classList.add('hidden');
    tableContainer?.classList.remove('hidden');
    paginationContainer?.classList.remove('hidden');

    const totalPages = Math.max(1, Math.ceil(total / rowsPerPage));
    if (currentPage > totalPages) currentPage = totalPages;

    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;

    visibleRows.forEach((row, index) => {
        row.classList.toggle('hidden', index < start || index >= end);
    });

    const info = document.getElementById('pagination-info');
    if (info) {
        info.textContent = `Affichage de ${total === 0 ? 0 : start + 1} à ${Math.min(end, total)} sur ${total} cessions`;
    }

    const prevBtn = document.getElementById('prev-btn');
    if (prevBtn) prevBtn.disabled = currentPage === 1;
    const nextBtn = document.getElementById('next-btn');
    if (nextBtn) nextBtn.disabled = currentPage === totalPages;
};

window.addTransactionRow = function() {
    const container = document.getElementById('transactions-container');
    const countInput = document.getElementById('transaction_count');
    let counter = parseInt(countInput.value) + 1;
    countInput.value = counter;

    const tr = document.createElement('tr');
    tr.className = "hover:bg-indigo-50/30 transition-colors group transaction-row animate-fade-in";
    tr.id = `tr-row-${counter}`;

    tr.innerHTML = `
        <td class="px-5 py-3">
            <input type="text" name="date_transaction_${counter}" placeholder="YYYY-MM-DD" oninput="validateDate(this)" class="w-32 dynamic-table-input text-xs md:text-sm font-mono px-2 py-1.5" />
            <div class="date-status mt-1"></div>
        </td>
        <td class="px-5 py-3">
            <div class="relative">
                <select name="operation_type_${counter}" onchange="updateRowStyle(this); updateRowTotal(this)" class="w-full px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wide border border-slate-200 hover:border-indigo-300 focus:ring-2 focus:ring-indigo-500 outline-none cursor-pointer appearance-none transition-all bg-slate-100 text-slate-600">
                    <option value="achat">Achat</option>
                    <option value="vente">Vente</option>
                    <option value="transfert" selected>Transfert</option>
                </select>
                <div class="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none opacity-50"><i class="fas fa-chevron-down text-[8px]"></i></div>
            </div>
        </td>
        <td class="px-5 py-3">
            <input type="text" name="crypto_token_${counter}" placeholder="BTC" class="w-16 dynamic-table-input text-xs md:text-sm font-bold uppercase px-2 py-1.5" />
        </td>
        <td class="px-5 py-3 text-right">
            <input type="number" step="any" name="quantity_${counter}" value="0.000000" oninput="updateRowTotal(this)" class="w-28 text-right dynamic-table-input text-xs md:text-sm font-mono px-2 py-1.5" />
        </td>
        <td class="px-5 py-3 text-right">
            <input type="number" step="any" name="acq_price_${counter}" value="0.00" oninput="updateRowTotal(this)" class="w-24 text-right dynamic-table-input text-xs md:text-sm font-mono px-2 py-1.5" />
            <span class="text-[10px] text-slate-400">€</span>
        </td>
        <td class="px-5 py-3 text-right">
            <input type="number" step="any" name="price_${counter}" value="0.00" oninput="updateRowTotal(this)" class="w-24 text-right dynamic-table-input text-xs md:text-sm font-mono px-2 py-1.5" />
            <span class="text-[10px] text-slate-400">€</span>
        </td>
        <td class="px-5 py-3 text-xs md:text-sm font-mono font-bold text-right row-total">0,00 €</td>
        <td class="px-5 py-3 text-xs md:text-sm font-mono font-bold text-right row-gain">0,00 €</td>
        <td class="px-5 py-3">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-50 text-slate-500 border border-slate-100 italic">Manuel</span>
        </td>
        <td class="px-5 py-3 text-center">
            <div class="flex items-center justify-center gap-2">
                <button type="button" class="remove-transaction w-9 h-9 rounded-xl text-slate-400 hover:text-red-600 hover:bg-red-50 border border-transparent transition-all flex items-center justify-center shadow-sm"><i class="fas fa-trash-alt text-sm"></i></button>
            </div>
            <input type="hidden" name="source_${counter}" value="Manuel" class="tx-source">
            <input type="hidden" name="source_type_${counter}" value="Manuel" class="tx-source-type">
        </td>
    `;

    container.appendChild(tr);
    currentPage = Math.ceil(document.querySelectorAll('.transaction-row').length / rowsPerPage);
    updatePagination();
    if (typeof updateTaxableCount === 'function') updateTaxableCount();
    tr.querySelector('input').focus();
};

// --- FILTRAGE SESSIONS IMPOSABLES ---
window.initFilters = function() {
    // Les filtres ne sont plus nécessaires car on n'affiche que les cessions imposables
};

window.prevPage = function() { if (currentPage > 1) { currentPage--; updatePagination(); } };
window.nextPage = function() { if (currentPage < Math.ceil(document.querySelectorAll('.transaction-row').length / rowsPerPage)) { currentPage++; updatePagination(); } };
window.updatePageSize = function() { rowsPerPage = parseInt(document.getElementById('rows-per-page').value); currentPage = 1; updatePagination(); };

window.clearAllTransactions = function() {
    if (confirm("Voulez-vous vraiment effacer toutes les transactions ?")) {
        document.getElementById('transactions-container').innerHTML = '';
        document.getElementById('transaction_count').value = '0';
        updatePagination();
        if (typeof updateTaxableCount === 'function') updateTaxableCount();
    }
};

window.removeSource = function(sourceName, tagId) {
    if (confirm(`Voulez-vous supprimer toutes les transactions importées depuis : ${sourceName} ?`)) {
        const rows = document.querySelectorAll('.transaction-row');
        rows.forEach(row => {
            const sourceInput = row.querySelector('.tx-source');
            if (sourceInput && sourceInput.value === sourceName) {
                row.remove();
            }
        });
        
        const tag = document.getElementById(tagId);
        if (tag) tag.remove();
        
        const container = document.getElementById('active-sources-container');
        if (container && container.querySelectorAll('.source-tag').length === 0) {
            container.remove();
        }
        
        updatePagination();
        recalculateGlobalGains();
        updateTaxableCount();
    }
};

window.updateTaxableCount = function() {
    const rows = document.querySelectorAll('.transaction-row');
    let taxableCount = 0;
    rows.forEach(row => {
        const select = row.querySelector('select[name^="operation_type_"]');
        if (select && select.value === 'vente') {
            taxableCount++;
        }
    });
    const valTx = document.getElementById('val-tx');
    if (valTx) {
        valTx.textContent = taxableCount;
    }
};

// --- CUSTOM CSV MAPPER ---
let customFileToParse = null;

window.extractHeadersFromCSV = function(csvText, separator) {
    const lines = csvText.split('\n');
    for (let i = 0; i < Math.min(20, lines.length); i++) {
        const line = lines[i].trim();
        if (!line) continue;
        const columns = line.split(separator).map(h => h.trim().replace(/"/g, ''));
        if (columns.length > 3) {
            console.log("Vraie ligne d'en-tête trouvée à la ligne", i + 1);
            return columns;
        }
    }
    return [];
};

window.readCustomCSVHeaders = function() {
    const fileInput = document.getElementById('custom-csv-input');
    const delimiter = document.getElementById('custom-delimiter').value;
    
    if (!fileInput.files.length) return alert("Veuillez sélectionner un fichier CSV.");
    
    customFileToParse = fileInput.files[0];
    const reader = new FileReader();
    
    reader.onload = function(e) {
        const text = e.target.result;
        const headers = extractHeadersFromCSV(text, delimiter);
        
        if (headers.length < 3) {
            alert("Impossible de lire suffisamment de colonnes. Le séparateur est-il correct ?");
            return;
        }
        
        // Remplir les menus déroulants de mappage avec les colonnes trouvées
        populateMappingSelects(headers);
        document.getElementById('mapping-step-2').classList.remove('hidden');
    };
    
    reader.readAsText(customFileToParse);
};

window.populateMappingSelects = function(headers) {
    const selects = document.querySelectorAll('.custom-map-select');
    
    selects.forEach(select => {
        select.innerHTML = '<option value="">-- Ignorer / Non présent --</option>';
        headers.forEach(header => {
            if (header) {
                const option = document.createElement('option');
                option.value = header;
                option.textContent = header;
                select.appendChild(option);
            }
        });
    });
};

window.applyCustomMapping = function() {
    const mapping = {
        date: document.getElementById('map-date').value,
        operation_type: document.getElementById('map-type').value,
        crypto_token: document.getElementById('map-asset').value,
        quantity: document.getElementById('map-qty').value,
        price: document.getElementById('map-price').value,
        fees: document.getElementById('map-fees').value,
        currency: document.getElementById('map-currency').value
    };
    
    if (!mapping.date || !mapping.operation_type || !mapping.crypto_token || !mapping.quantity) {
        return alert("Veuillez au moins mapper la Date, le Type, l'Actif et la Quantité.");
    }
    
    // Injecter le JSON dans le champ caché
    document.getElementById('custom_mapping_json').value = JSON.stringify(mapping);
    document.getElementById('custom_mapping_delimiter').value = document.getElementById('custom-delimiter').value;
    
    // Assigner le fichier au vrai file input pour qu'il soit envoyé au bouton Simuler
    const mainFileInput = document.getElementById('file-input');
    const dt = new DataTransfer();
    
    // Keep existing files if any
    if (mainFileInput.files) {
        for (let f of mainFileInput.files) {
            dt.items.add(f);
        }
    }
    dt.items.add(customFileToParse);
    mainFileInput.files = dt.files;
    
    selectedFiles = dt;
    if(typeof renderFileChips === "function") renderFileChips();
    
    document.getElementById('customMapperModal').classList.add('hidden');
    alert("Mappage enregistré avec succès ! Veuillez cliquer sur 'Simuler mes impôts' pour lancer l'analyse.");
};

// --- DOM READY ---
document.addEventListener('DOMContentLoaded', function () {
    window.loadTaxConfig();
    updateTaxes();
    initFileUpload();
    initWalletDetection();
    initFilters();
    updatePagination();

    // Event delegation for remove buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.remove-transaction')) {
            const row = e.target.closest('.transaction-row');
            row.remove();
            updatePagination();
            updateTaxableCount();
            recalculateGlobalGains();
        }
    });

    // Initial styles and totals for rows
    document.querySelectorAll('.transaction-row').forEach(row => {
        const select = row.querySelector('select');
        if (select) updateRowStyle(select);
        const inputs = row.querySelectorAll('input');
        if (inputs.length > 0) updateRowTotal(inputs[0]);
    });
    
    updateTaxableCount();
});
