document.addEventListener('DOMContentLoaded', function() {
    
    const allRedeemButtons = document.querySelectorAll('.btn-redeem');
    const balanceDisplay = document.getElementById('user-balance');

    allRedeemButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const rewardId = this.dataset.rewardId;
            const cost = parseInt(this.dataset.cost, 10);
            
            // 1. Confirm with the user
            if (!confirm(`Are you sure you want to spend ${cost} MossCoins for this reward?`)) {
                return; // Stop if they click "Cancel"
            }
            
            // 2. Disable button to prevent double-click
            this.disabled = true;
            this.textContent = 'Redeeming...';

            try {
                // 3. Send the reward ID to the backend API
                const response = await fetch('/api/consumer/redeem-reward', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ reward_id: rewardId })
                });

                const result = await response.json();

                if (response.ok) {
                    // 4. Success!
                    alert(result.message);
                    // Update the balance on the page
                    balanceDisplay.textContent = result.new_balance;
                    // Change button to "Redeemed"
                    this.textContent = 'Redeemed!';
                    this.classList.add('redeemed');
                } else {
                    // 5. Show an error
                    alert(`Error: ${result.error}`);
                    this.disabled = false; // Re-enable button
                    this.innerHTML = `<i class="fas fa-coins"></i> ${cost}`;
                }
            } catch (error) {
                alert(`Error: ${error.message}`);
                this.disabled = false;
                this.innerHTML = `<i class="fas fa-coins"></i> ${cost}`;
            }
        });
    });
});