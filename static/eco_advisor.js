document.addEventListener('DOMContentLoaded', function() {
    
    // This is our database of pre-written answers
    const cannedResponses = {
        "How do I log a purchase?": "To log a purchase, get a bill from a vendor. Then, go to the 'Log Purchase' page in your app. You'll see all your pending bills. Just click the 'Log' button to claim your MossCoins!",
        "How do I redeem my MossCoins?": "Go to the 'Redeem' page from the main menu. You can browse all available rewards from our partners and government schemes. If you have enough coins, just click the 'Redeem' button!",
        "How can I reduce my water usage?": "A great way is to take shorter showers! Also, fix any leaky faucets. A single drip can waste hundreds of gallons of water per month.",
        "What's the most impactful way to recycle?": "Focus on the 'Big 4': 1. Paper & Cardboard, 2. Glass bottles & jars, 3. Metal cans (like soda cans), and 4. Plastic bottles & jugs. Make sure they are clean and dry!"
    };

    const chatWindow = document.getElementById('chat-window');
    const suggestionButtons = document.querySelectorAll('.chat-suggestion-btn');

    // Add a click listener to every button
    suggestionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const question = this.dataset.question;
            const answer = cannedResponses[question];
            
            // 1. Display the user's question
            addMessage(question, 'user-message');
            
            // 2. Show a "typing" indicator
            const typingIndicator = addMessage("MossPay is typing...", 'ai-message', true);
            
            // 3. Wait 1 second, then show the real answer
            setTimeout(() => {
                // Remove the typing indicator
                chatWindow.removeChild(typingIndicator);
                // Add the real answer
                addMessage(answer, 'ai-message');
            }, 1000); // 1-second delay
        });
    });

    // Helper function to add a message to the chat window
    function addMessage(text, type, isTyping = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;
        
        let icon = type === 'ai-message' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
        let textContent = `<p>${text}</p>`;
        
        if (isTyping) {
            textContent = '<p class="typing-dots"><span></span><span></span><span></span></p>';
        }

        messageDiv.innerHTML = icon + textContent;
        chatWindow.appendChild(messageDiv);
        
        // Scroll to the bottom
        chatWindow.scrollTop = chatWindow.scrollHeight;
        
        return messageDiv; // Return the element so we can remove it
    }
});