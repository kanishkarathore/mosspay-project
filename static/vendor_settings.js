document.addEventListener('DOMContentLoaded', function() {
    
    const passwordForm = document.getElementById('change-password-form');
    const messageDisplay = document.getElementById('password-message-display');

    passwordForm.addEventListener('submit', async function(e) {
        e.preventDefault(); // Stop the form from submitting normally
        
        const old_password = document.getElementById('old_password').value;
        const new_password = document.getElementById('new_password').value;

        // Clear any old messages
        messageDisplay.textContent = '';
        messageDisplay.className = '';

        try {
            const response = await fetch('/api/vendor/change-password', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    old_password: old_password,
                    new_password: new_password
                })
            });

            const result = await response.json();

            if (response.ok) {
                // Success
                messageDisplay.textContent = result.message;
                messageDisplay.className = 'message-success';
                passwordForm.reset();
            } else {
                // Error (e.g., "Old password is not correct")
                messageDisplay.textContent = `Error: ${result.error}`;
                messageDisplay.className = 'message-error';
            }
        } catch (error) {
            messageDisplay.textContent = `Error: ${error.message}`;
            messageDisplay.className = 'message-error';
        }
    });
});