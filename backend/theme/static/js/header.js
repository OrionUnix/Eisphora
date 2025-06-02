
   
      // Animation pour simuler un scrolling de texte sur l'écran LED
        const screenContent = document.querySelector('.screen-content');
        let scrollPosition = 0;
        
        setInterval(() => {
            scrollPosition = (scrollPosition + 20) % 100;
            screenContent.style.transform = `translateY(-${scrollPosition}px)`;
        }, 2000);
   


        document.addEventListener('DOMContentLoaded', function() {
    const fillBtn = document.getElementById('fillBtn');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const successMessage = document.getElementById('successMessage');
    const restartCount = document.getElementById('restartCount');
    
    let restartCounter = 0;
    
    // Liste des champs avec des délais réduits
    const fields = [
        { id: 'fullName', value: 'Jean Dupont', delay: 500 },
        { id: 'taxId', value: 'FR-1234567890A', delay: 1000 },
        { id: 'annualIncome', value: '€ 45,200.00', delay: 1500 },
        { id: 'deductions', value: '€ 8,750.00', delay: 2000 },
        { id: 'taxableIncome', value: '€ 36,450.00', delay: 2500 },
        { id: 'taxDue', value: '€ 4,325.00', delay: 3000 }
    ];
    
    // Fonction pour réinitialiser le formulaire
    function resetForm() {
        document.querySelectorAll('.form-input').forEach(input => {
            input.value = '';
        });
        
        document.querySelectorAll('.auto-fill-indicator').forEach(indicator => {
            indicator.classList.remove('show');
        });
        
        progressBar.style.width = '0%';
        progressText.textContent = "'Preparing your form...'";
        fillBtn.innerHTML = '<i class="fas fa-magic mr-2"></i>  "Fill Automatically"';
        fillBtn.style.background = 'linear-gradient(to right, #0d3b66, #1d5c96)';
        successMessage.classList.remove('show');
    }
    
    // Fonction pour démarrer le remplissage (version accélérée et infinie)
    function startAutoFill() {
        // Démarrer l'animation de progression (plus rapide)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 2; // Augmentation plus rapide
            if (progress > 100) progress = 100;
            progressBar.style.width = `${progress}%`;
            
            if (progress <= 30) {
                progressText.textContent = "'Retrieving your information...'";
            } else if (progress <= 70) {
                progressText.textContent = " 'Calculating your income...'";
            } else {
                progressText.textContent = " 'Finalizing your declaration...'";
            }
            
            if (progress >= 100) {
                clearInterval(progressInterval);
            }
        }, 20); // Intervalle réduit
        
        // Remplir les champs avec délais réduits
        fields.forEach((field, index) => {
            setTimeout(() => {
                const inputField = document.getElementById(field.id);
                const indicator = document.getElementById(field.id + 'Indicator');
                
                // Effet d'écriture accéléré
                let i = 0;
                const typingInterval = setInterval(() => {
                    if (i < field.value.length) {
                        inputField.value = field.value.substring(0, i + 1);
                        i++;
                    } else {
                        clearInterval(typingInterval);
                        indicator.classList.add('show');
                        
                        // Dernier champ: préparer le redémarrage
                        if (index === fields.length - 1) {
                            // Afficher le message de succès
                            successMessage.classList.add('show');
                            progressText.textContent = " 'Form completed at 100%' ";
                            fillBtn.innerHTML = '<i class="fas fa-check mr-2"></i>  trans "Form Completed"';
                            
                            // Incrémenter le compteur et réinitialiser
                            setTimeout(() => {
                                restartCounter++;
                                restartCount.textContent = `Restarts: ${restartCounter}`;
                                resetForm();
                                
                                // Relancer l'animation après un court délai
                                setTimeout(startAutoFill, 500);
                            }, 1000);
                        }
                    }
                }, 20); // Vitesse d'écriture augmentée
            }, field.delay);
        });
    }

    // Démarrer la première itération
    startAutoFill();
});