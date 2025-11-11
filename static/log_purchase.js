document.addEventListener('DOMContentLoaded', function() {
    
    const allLogButtons = document.querySelectorAll('.btn-log-purchase');

    allLogButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const billId = this.dataset.billId;
            const cardFooter = this.parentElement;

            try {
                // 1. Send the bill ID to the backend API
                const response = await fetch('/api/consumer/log-purchase', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ bill_id: billId })
                });

                const result = await response.json();

                if (response.ok) {
                    // 2. Success! Change the button to a "Logged" badge
                    cardFooter.innerHTML = `
                        <span class="badge-logged">
                            <i class="fas fa-check-circle"></i> Logged!
                        </span>
                    `;
                    // You could also update the main MossCoin balance on the page here
                } else {
                    // 3. Show an error
                    alert(`Error: ${result.error}`);
                }
            } catch (error) {
                alert(`Error: ${error.message}`);
            }
        });
    });

});