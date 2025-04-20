/**
 * ActualsManager - A class to manage sales actuals data
 * Handles saving, loading, and updating actual sales figures
 */
class ActualsManager {
    /**
     * Constructor
     * @param {string} formId - ID of the actuals form
     * @param {string} tableId - ID of the actuals table
     * @param {DateContextManager} dateContextManager - Date context manager instance
     */
    constructor(formId, tableId, dateContextManager) {
        // Form elements
        this.form = document.getElementById(formId);
        this.table = document.getElementById(tableId);
        this.dateContextManager = dateContextManager;
        
        // Cache for distributors and actuals data
        this.distributors = [];
        this.actuals = [];
        
        // Initialization flag
        this.initialized = false;
    }
    
    /**
     * Initialize the actuals manager
     * @returns {Promise} - Resolves when initialization is complete
     */
    async init() {
        if (this.initialized) return Promise.resolve();
        
        try {
            // Load distributors
            await this.loadDistributors();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Load existing actuals
            await this.loadActuals();
            
            // Render the actuals table
            this.renderActualsTable();
            
            this.initialized = true;
            return Promise.resolve();
        } catch (error) {
            console.error('Error initializing ActualsManager:', error);
            return Promise.reject(error);
        }
    }
    
    /**
     * Load distributors from the API
     * @returns {Promise} - Resolves when distributors are loaded
     */
    async loadDistributors() {
        try {
            const response = await fetch('/api/distributors');
            const data = await response.json();
            this.distributors = data.distributors || [];
            
            // Populate distributor fields in the form
            this.populateDistributorFields();
            
            return Promise.resolve();
        } catch (error) {
            console.error('Error loading distributors:', error);
            return Promise.reject(error);
        }
    }
    
    /**
     * Populate distributor fields in the form
     */
    populateDistributorFields() {
        const container = document.querySelector('.distributor-actuals-container');
        if (!container) return;
        
        // Clear existing fields
        container.innerHTML = '';
        
        // Add fields for each distributor
        this.distributors.forEach(distributor => {
            const row = document.createElement('div');
            row.classList.add('row', 'mb-3', 'distributor-row');
            row.setAttribute('data-distributor-id', distributor.id);
            
            row.innerHTML = `
                <div class="col-md-6">
                    <label class="form-label">${distributor.name}</label>
                </div>
                <div class="col-md-6">
                    <div class="input-group">
                        <span class="input-group-text">₹</span>
                        <input type="number" class="form-control actual-value" name="actual_${distributor.id}" 
                               placeholder="Enter actual value" min="0" step="0.01">
                    </div>
                </div>
            `;
            
            container.appendChild(row);
        });
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Listen for form submission
        if (this.form) {
            this.form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmit();
            });
        }
        
        // Listen for date context changes
        if (this.dateContextManager) {
            const fySelect = this.dateContextManager.financialYearSelect;
            const periodTypeSelect = this.dateContextManager.periodTypeSelect;
            const periodIdentifierSelect = this.dateContextManager.periodIdentifierSelect;
            
            if (fySelect) {
                fySelect.addEventListener('change', () => {
                    this.dateContextManager.onFinancialYearChange();
                    this.loadActuals();
                });
            }
            
            if (periodTypeSelect) {
                periodTypeSelect.addEventListener('change', () => {
                    this.dateContextManager.onPeriodTypeChange();
                    this.loadActuals();
                });
            }
            
            if (periodIdentifierSelect) {
                periodIdentifierSelect.addEventListener('change', () => {
                    this.loadActuals();
                });
            }
        }
        
        // Listen for delete and edit actions in the table
        if (this.table) {
            this.table.addEventListener('click', (e) => {
                if (e.target.classList.contains('btn-delete')) {
                    const actualId = e.target.getAttribute('data-actual-id');
                    this.deleteActual(actualId);
                } else if (e.target.classList.contains('btn-edit')) {
                    const actualId = e.target.getAttribute('data-actual-id');
                    this.editActual(actualId);
                }
            });
        }
    }
    
    /**
     * Load actuals for the current date context
     * @returns {Promise} - Resolves when actuals are loaded
     */
    async loadActuals() {
        if (!this.dateContextManager) return Promise.resolve();
        
        try {
            const financialYear = this.dateContextManager.financialYearSelect.value;
            const periodType = this.dateContextManager.periodTypeSelect.value;
            const periodIdentifier = this.dateContextManager.periodIdentifierSelect.value;
            
            if (!financialYear || !periodType || !periodIdentifier) {
                this.actuals = [];
                this.renderActualsTable();
                return Promise.resolve();
            }
            
            // Construct query parameters
            const params = new URLSearchParams({
                financial_year: financialYear,
                period_type: periodType,
                period_identifier: periodIdentifier
            });
            
            const response = await fetch(`/api/actuals?${params.toString()}`);
            const data = await response.json();
            this.actuals = data.actuals || [];
            
            // Update form with existing actuals
            this.updateFormWithActuals();
            
            // Render the actuals table
            this.renderActualsTable();
            
            return Promise.resolve();
        } catch (error) {
            console.error('Error loading actuals:', error);
            return Promise.reject(error);
        }
    }
    
    /**
     * Update form fields with existing actuals
     */
    updateFormWithActuals() {
        const distributorRows = document.querySelectorAll('.distributor-row');
        
        // Reset all input fields
        distributorRows.forEach(row => {
            const input = row.querySelector('.actual-value');
            if (input) input.value = '';
        });
        
        // Update fields with existing actuals
        this.actuals.forEach(actual => {
            const row = document.querySelector(`.distributor-row[data-distributor-id="${actual.distributor_id}"]`);
            if (row) {
                const input = row.querySelector('.actual-value');
                if (input) input.value = actual.value;
            }
        });
    }
    
    /**
     * Render the actuals table
     */
    renderActualsTable() {
        if (!this.table) return;
        
        const tbody = this.table.querySelector('tbody');
        if (!tbody) return;
        
        // Clear existing rows
        tbody.innerHTML = '';
        
        // Add rows for each actual
        this.actuals.forEach(actual => {
            const distributor = this.getDistributorById(actual.distributor_id);
            if (!distributor) return;
            
            const target = actual.target || 0;
            const percentage = target > 0 ? ((actual.value / target) * 100).toFixed(2) : 'N/A';
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${distributor.name}</td>
                <td>${actual.period_identifier}</td>
                <td>₹${actual.value.toLocaleString()}</td>
                <td>₹${target.toLocaleString()}</td>
                <td>${percentage}%</td>
                <td>
                    <button class="btn btn-sm btn-primary btn-edit" data-actual-id="${actual.id}">Edit</button>
                    <button class="btn btn-sm btn-danger btn-delete" data-actual-id="${actual.id}">Delete</button>
                </td>
            `;
            
            tbody.appendChild(row);
        });
        
        // Show message if no actuals
        if (this.actuals.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td colspan="6" class="text-center">No actuals found for the selected period.</td>
            `;
            tbody.appendChild(row);
        }
    }
    
    /**
     * Handle form submission
     */
    async handleFormSubmit() {
        if (!this.dateContextManager) return;
        
        try {
            const financialYear = this.dateContextManager.financialYearSelect.value;
            const periodType = this.dateContextManager.periodTypeSelect.value;
            const periodIdentifier = this.dateContextManager.periodIdentifierSelect.value;
            
            if (!financialYear || !periodType || !periodIdentifier) {
                alert('Please select a financial year, period type, and period identifier.');
                return;
            }
            
            // Collect actual values from the form
            const actualsData = [];
            const distributorRows = document.querySelectorAll('.distributor-row');
            
            distributorRows.forEach(row => {
                const distributorId = row.getAttribute('data-distributor-id');
                const input = row.querySelector('.actual-value');
                
                if (input && input.value) {
                    const value = parseFloat(input.value);
                    if (!isNaN(value) && value >= 0) {
                        actualsData.push({
                            distributor_id: distributorId,
                            value: value
                        });
                    }
                }
            });
            
            if (actualsData.length === 0) {
                alert('Please enter at least one actual value.');
                return;
            }
            
            // Prepare request payload
            const payload = {
                financial_year: financialYear,
                period_type: periodType,
                period_identifier: periodIdentifier,
                actuals: actualsData
            };
            
            // Send request to API
            const response = await fetch('/api/actuals', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Reload actuals
                await this.loadActuals();
                
                // Show success message
                alert('Actuals saved successfully.');
                
                // Reset form
                this.form.reset();
            } else {
                alert(result.message || 'Failed to save actuals.');
            }
        } catch (error) {
            console.error('Error saving actuals:', error);
            alert('Failed to save actuals. Please try again.');
        }
    }
    
    /**
     * Delete an actual
     * @param {string} actualId - ID of the actual to delete
     */
    async deleteActual(actualId) {
        if (!actualId) return;
        
        if (!confirm('Are you sure you want to delete this actual?')) return;
        
        try {
            const response = await fetch(`/api/actuals/${actualId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Reload actuals
                await this.loadActuals();
                
                // Show success message
                alert('Actual deleted successfully.');
            } else {
                alert(result.message || 'Failed to delete actual.');
            }
        } catch (error) {
            console.error('Error deleting actual:', error);
            alert('Failed to delete actual. Please try again.');
        }
    }
    
    /**
     * Edit an actual
     * @param {string} actualId - ID of the actual to edit
     */
    editActual(actualId) {
        if (!actualId) return;
        
        // Find the actual
        const actual = this.actuals.find(a => a.id === actualId);
        if (!actual) return;
        
        // Find the distributor row
        const row = document.querySelector(`.distributor-row[data-distributor-id="${actual.distributor_id}"]`);
        if (!row) return;
        
        // Set the value in the input field
        const input = row.querySelector('.actual-value');
        if (input) input.value = actual.value;
        
        // Scroll to the form
        this.form.scrollIntoView({ behavior: 'smooth' });
        
        // Focus the input field
        if (input) input.focus();
    }
    
    /**
     * Get distributor by ID
     * @param {string} distributorId - ID of the distributor
     * @returns {Object} - Distributor object
     */
    getDistributorById(distributorId) {
        return this.distributors.find(d => d.id === distributorId);
    }
}

// Initialize ActualsManager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const dateContextManager = new DateContextManager('fy-select', 'period-type-select', 'period-identifier-select');
    dateContextManager.loadFinancialYears().then(() => {
        dateContextManager.onPeriodTypeChange();
    });
    
    const actualsManager = new ActualsManager('actuals-form', 'actuals-table', dateContextManager);
    actualsManager.init();
}); 