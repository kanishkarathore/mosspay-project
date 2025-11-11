document.addEventListener('DOMContentLoaded', function() {
    
    // Form fields
    const addItemForm = document.getElementById('add-item-form');
    
    // Handle submitting the final "Add Item" form
    addItemForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 1. Get data from all 4 fields
        const itemData = {
            name: document.getElementById('item-name').value,
            price: document.getElementById('item-price').value,
            unit: document.getElementById('item-unit').value,
            stock: document.getElementById('item-stock').value
        };

        if (!itemData.name || !itemData.price || !itemData.unit || !itemData.stock) {
            alert('Please fill out all fields.');
            return;
        }
        
        try {
            // 2. Send the data to our Flask server
            const response = await fetch('/api/vendor/add-item', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(itemData),
            });
            
            const newItem = await response.json();
            
            if (response.ok) {
                // 3. Add the new item to the table instantly
                const newRow = document.createElement('tr');
                newRow.innerHTML = `
                    <td>${newItem.name}</td>
                    <td>${newItem.price.toFixed(2)}</td>
                    <td>${newItem.unit}</td>
                    <td>${newItem.stock}</td>
                    <td>${newItem.carbon_saved_kg}</td>
                    <td><a href="#" class="btn-delete">Delete</a></td>
                `;
                document.querySelector('#items-table tbody').appendChild(newRow);
                
                // 4. Clear the form
                addItemForm.reset();
            } else {
                alert(`Error: ${newItem.error}`);
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    });
});