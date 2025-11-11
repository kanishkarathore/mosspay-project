document.addEventListener('DOMContentLoaded', function() {
    
    // --- STATE ---
    // We change const to let so we can reset it, OR we can clear it property by property.
    // Let's clear it property by property, as that's safer.
    const cart = {};

    // --- DOM Elements ---
    const itemList = document.getElementById('item-list');
    const searchInput = document.getElementById('item-search-input');
    const billItemsList = document.getElementById('bill-items-list');
    const totalAmountEl = document.getElementById('total-amount');
    const totalCarbonEl = document.getElementById('total-carbon');
    const sendToPhoneBtn = document.getElementById('btn-send-to-phone');
    const generateQrBtn = document.getElementById('btn-generate-qr');
    const customerPhoneInput = document.getElementById('customer-phone');
    const qrCodeContainer = document.getElementById('qr-code-container');
    const messageDisplay = document.getElementById('bill-message-display');

    // --- FUNCTIONS ---

    // 1. Update Bill UI (The right panel)
    function updateBillUI() {
        billItemsList.innerHTML = '';
        let totalAmount = 0;
        let totalCarbon = 0;
        
        const itemsInCart = Object.keys(cart).length > 0;
        
        if (!itemsInCart) {
            billItemsList.innerHTML = '<p class="empty-bill">No items added yet.</p>';
        } else {
            for (const itemId in cart) {
                const item = cart[itemId];
                totalAmount += item.price * item.quantity;
                totalCarbon += item.carbon * item.quantity;
                
                const billEntry = document.createElement('div');
                billEntry.className = 'bill-item-entry';
                billEntry.innerHTML = `
                    <span class="item-name">${item.name} (x${item.quantity})</span>
                    <span class="item-price">₹${(item.price * item.quantity).toFixed(2)}</span>
                `;
                billItemsList.appendChild(billEntry);
            }
        }
        
        totalAmountEl.textContent = `₹${totalAmount.toFixed(2)}`;
        totalCarbonEl.textContent = `${totalCarbon.toFixed(1)} kg`;
    }

    // 2. Handle Clicks on + and -
    itemList.addEventListener('click', function(e) {
        const button = e.target.closest('.btn-quantity');
        if (!button) return;

        const action = button.dataset.action;
        const id = button.dataset.id;
        const stock = parseInt(button.dataset.stock, 10);
        const quantityEl = document.getElementById(`quantity-${id}`);
        let currentQuantity = cart[id] ? cart[id].quantity : 0;

        if (action === 'increase') {
            if (currentQuantity < stock) {
                currentQuantity++;
                if (!cart[id]) {
                    cart[id] = {
                        name: button.dataset.name,
                        price: parseFloat(button.dataset.price),
                        carbon: parseFloat(button.dataset.carbon),
                        stock: stock,
                        quantity: 0
                    };
                }
                cart[id].quantity = currentQuantity;
            } else {
                alert(`Cannot add more. Only ${stock} in stock.`);
            }
        } else if (action === 'decrease') {
            if (currentQuantity > 0) {
                currentQuantity--;
                cart[id].quantity = currentQuantity;
                if (currentQuantity === 0) {
                    delete cart[id];
                }
            }
        }
        
        quantityEl.textContent = currentQuantity;
        updateBillUI();
    });

    // 3. Handle Search Filter
    searchInput.addEventListener('keyup', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        const allItems = itemList.querySelectorAll('.item-list-entry');
        
        allItems.forEach(item => {
            const itemName = item.dataset.name;
            if (itemName.includes(searchTerm)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    });

    // 4. Handle "Send to Phone"
    sendToPhoneBtn.addEventListener('click', async function() {
        const phone = customerPhoneInput.value;
        const itemsInCart = Object.keys(cart).map(itemId => ({
            id: itemId, // Get the ID from the cart's key
            quantity: cart[itemId].quantity
        }));

        if (!phone || phone.length !== 10 || !/^\d+$/.test(phone)) {
            alert('Please enter a valid 10-digit phone number.');
            return;
        }
        if (itemsInCart.length === 0) {
            alert('Please add items to the bill.');
            return;
        }
        
        messageDisplay.textContent = 'Sending...';
        messageDisplay.className = 'message-sending';

        try {
            const response = await fetch('/api/vendor/send-bill-to-phone', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    phone: phone,
                    cart: itemsInCart
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                messageDisplay.textContent = `Success: ${result.message}`;
                messageDisplay.className = 'message-success';
                
                // --- THIS IS THE FIX ---
                // We must delete each key from the const, not reassign the const
                Object.keys(cart).forEach(id => {
                    document.getElementById(`quantity-${id}`).textContent = '0';
                    delete cart[id]; // Delete the property
                });
                // --- END OF FIX ---

                updateBillUI();
                customerPhoneInput.value = '';
                
                setTimeout(() => window.location.reload(), 2000);
            } else {
                messageDisplay.textContent = `Error: ${result.error}`;
                messageDisplay.className = 'message-error';
            }
        } catch (error) {
            messageDisplay.textContent = `Error: ${error.message}`;
            messageDisplay.className = 'message-error';
        }
    });
    
    // 5. Handle "Generate QR"
    generateQrBtn.addEventListener('click', function() {
        const totalAmount = totalAmountEl.textContent;
        const totalCarbon = totalCarbonEl.textContent;
        
        if (Object.keys(cart).length === 0) {
            alert('Please add items to the bill to generate a QR code.');
            return;
        }
        
        const qrText = `MossPay Bill\nTotal: ${totalAmount}\nCarbon Saved: ${totalCarbon}`;
        
        qrCodeContainer.innerHTML = '';
        new QRCode(qrCodeContainer, {
            text: qrText,
            width: 128,
            height: 128
        });
        messageDisplay.textContent = 'QR code generated for bill details.';
        messageDisplay.className = 'message-success';
    });

});