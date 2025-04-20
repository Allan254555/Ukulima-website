// Initialize payment
async function initializePayment() {
  const cartItems = getCartItems(); // Your function to get cart items
  
  const response = await fetch('/payments/initialize', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': getCSRFToken() // Add CSRF protection
    },
    body: JSON.stringify({
      items: cartItems
    })
  });

  const data = await response.json();
  
  if (data.authorization_url) {
    // Redirect to Paystack
    window.location.href = data.authorization_url;
    
    // Or for popup flow:
    // const popup = window.open(data.authorization_url, 'paystackPayment', 'width=500,height=600');
    // checkPaymentStatus(data.reference, popup);
  } else {
    showError(data.error || 'Payment initialization failed');
  }
}

// For popup flow - check payment status
async function checkPaymentStatus(reference, popup) {
  const interval = setInterval(async () => {
    if (popup.closed) {
      clearInterval(interval);
      const result = await verifyPayment(reference);
      if (result.status === 'completed') {
        window.location.href = `/order/${result.order_id}`;
      }
    }
  }, 2000);
}

async function verifyPayment(reference) {
  const response = await fetch(`/payments/verify/${reference}`);
  return await response.json();
}on>
