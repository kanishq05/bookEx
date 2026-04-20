// Cart Logic
let cart = JSON.parse(sessionStorage.getItem('shopping_cart')) || [];

function saveCart() {
    sessionStorage.setItem('shopping_cart', JSON.stringify(cart));
    updateCartUI();
}

function addToCart(id, name, price) {
    price = parseFloat(price);
    let existingItem = cart.find(item => item.id === id);
    if (existingItem) {
        existingItem.quantity += 1;
        if (window.showToast) showToast(`Updated: ${name} (×${existingItem.quantity})`, 'info');
    } else {
        cart.push({ id, name, price, quantity: 1 });
        if (window.showToast) showToast(`Added "${name}" to cart`, 'success');
    }
    saveCart();
}

function removeFromCart(id) {
    cart = cart.filter(item => item.id !== id);
    saveCart();
}

function changeQuantity(id, delta) {
    let item = cart.find(item => item.id === id);
    if (item) {
        item.quantity += delta;
        if (item.quantity <= 0) {
            removeFromCart(id);
        } else {
            saveCart();
        }
    }
}

function updateCartUI() {
    let cartContainer = document.getElementById('cart-items');
    let totalContainer = document.getElementById('cart-total');

    if (!cartContainer || !totalContainer) return;

    cartContainer.innerHTML = '';
    let total = 0;

    if (cart.length === 0) {
        cartContainer.innerHTML = '<p style="color: #888; font-size: 0.9em; font-style: italic;">Your cart is empty.</p>';
    }

    cart.forEach(item => {
        let itemTotal = item.price * item.quantity;
        total += itemTotal;

        // Create item UI
        let itemDiv = document.createElement('div');
        itemDiv.style.marginBottom = '10px';
        itemDiv.style.paddingBottom = '10px';
        itemDiv.style.borderBottom = '1px dashed #eee';

        itemDiv.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 5px;">
                <span style="font-weight: bold; font-size: 0.9em;">${item.name}</span>
                <span style="font-size: 0.9em; color: #555;">$${itemTotal.toFixed(2)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <button onclick="changeQuantity('${item.id}', -1)" style="cursor:pointer; padding: 2px 6px; border: 1px solid #ccc; background: white; border-radius: 3px;">-</button>
                    <span style="margin: 0 5px; font-size: 0.9em;">${item.quantity}</span>
                    <button onclick="changeQuantity('${item.id}', 1)" style="cursor:pointer; padding: 2px 6px; border: 1px solid #ccc; background: white; border-radius: 3px;">+</button>
                </div>
                <button onclick="removeFromCart('${item.id}')" style="cursor:pointer; padding: 2px 6px; border: none; background: #e74c3c; color: white; border-radius: 3px; font-size: 0.8em;">Remove</button>
            </div>
        `;
        cartContainer.appendChild(itemDiv);
    });

    totalContainer.innerText = total.toFixed(2);

    // Add Checkout Button if cart is not empty
    if (cart.length > 0) {
        let checkoutBtn = document.createElement('button');
        checkoutBtn.innerText = 'Checkout';
        checkoutBtn.style.marginTop = '15px';
        checkoutBtn.style.width = '100%';
        checkoutBtn.style.padding = '10px';
        checkoutBtn.style.background = '#007BFF';
        checkoutBtn.style.color = 'white';
        checkoutBtn.style.border = 'none';
        checkoutBtn.style.cursor = 'pointer';
        checkoutBtn.style.borderRadius = '5px';
        checkoutBtn.style.fontWeight = 'bold';
        checkoutBtn.onclick = function () { checkout(); };
        cartContainer.appendChild(checkoutBtn);
    }
}

function checkout() {
    cart = [];
    sessionStorage.removeItem('shopping_cart');
    updateCartUI();
    window.location.href = '/checkout_success/';
}

// Initial render
document.addEventListener('DOMContentLoaded', () => {
    updateCartUI();
});
