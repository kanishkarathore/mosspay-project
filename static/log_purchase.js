document.addEventListener('DOMContentLoaded', function() {
    
    const logPurchaseList = document.querySelector('.log-purchase-list');

    logPurchaseList.addEventListener('click', async function(e) {
        
        // --- Logic for "Log Purchase" Button ---
        const logButton = e.target.closest('.btn-log-purchase');
        if (logButton) {
            const billId = logButton.dataset.billId;
            const cardFooter = logButton.parentElement;

            try {
                const response = await fetch('/api/consumer/log-purchase', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ bill_id: billId })
                });
                const result = await response.json();

                if (response.ok) {
                    cardFooter.innerHTML = `
                        <span class="badge-logged">
                            <i class="fas fa-check-circle"></i> Logged!
                        </span>
                    `;
                    // Update the header badge to show "Logged"
                    const header = cardFooter.closest('.bill-card').querySelector('.bill-card-header');
                    header.classList.remove('clickable'); // No need to expand
                } else {
                    alert(`Error: ${result.error}`);
                }
            } catch (error) {
                alert(`Error: ${error.message}`);
            }
        }
        
        // --- NEW: Logic for Expanding the Card ---
        const cardHeader = e.target.closest('.bill-card-header.clickable');
        if (cardHeader) {
            const billCard = cardHeader.closest('.bill-card');
            const details = billCard.querySelector('.bill-card-details');
            const icon = cardHeader.querySelector('.expand-icon');

            // Toggle visibility
            details.classList.toggle('visible');
            icon.classList.toggle('rotated');
        }
    });
});