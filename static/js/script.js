// Common JavaScript functions for the application

// Automatically close alert messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    // Get all alert messages
    const alerts = document.querySelectorAll('.alert');
    
    // Set timeout to automatically close them
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Add current year to footer if needed
    const footerYear = document.querySelector('footer p');
    if (footerYear) {
        const currentYear = new Date().getFullYear();
        footerYear.textContent = footerYear.textContent.replace('{{ now.year }}', currentYear);
    }
});

// Format number as cases
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount) + ' cases';
}

// Format number as percentage
function formatPercent(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value / 100);
}

// Validate numeric input (allow only numbers and decimal point)
function validateNumericInput(input) {
    input.value = input.value.replace(/[^0-9.]/g, '');
    
    // Ensure only one decimal point
    const decimalCount = (input.value.match(/\./g) || []).length;
    if (decimalCount > 1) {
        const parts = input.value.split('.');
        input.value = parts[0] + '.' + parts.slice(1).join('');
    }
}

// Add numeric validation to all numeric inputs
document.addEventListener('DOMContentLoaded', function() {
    const numericInputs = document.querySelectorAll('input[type="number"]');
    numericInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            validateNumericInput(this);
        });
    });
});
