/**
 * Targets Manager
 * 
 * Manages sales targets including CRUD operations, data validation,
 * UI updates and API interactions.
 */
class TargetsManager {
    /**
     * Constructor for TargetsManager
     * 
     * @param {Object} config - Configuration object
     * @param {string} config.formId - Target form ID
     * @param {string} config.tableId - Targets table ID
     * @param {string} config.notificationAreaId - Notification area ID
     * @param {Object} dateContextManager - Instance of DateContextManager
     */
    constructor(config, dateContextManager) {
        // Store configuration
        this.config = config;
        
        // Store reference to DateContextManager
        this.dateContextManager = dateContextManager;
        
        // Reference DOM elements
        this.form = document.getElementById(config.formId);
        this.table = document.getElementById(config.tableId);
        this.tableBody = this.table.querySelector('tbody');
        this.notificationArea = document.getElementById(config.notificationAreaId);
        
        // Cache form fields
        this.fields = {
            distributor: document.getElementById('targetDistributor'),
            region: document.getElementById('targetRegion'),
            state: document.getElementById('targetState'),
            territory: document.getElementById('targetTerritory'),
            targetAmount: document.getElementById('targetAmount'),
            notes: document.getElementById('targetNotes')
        };
        
        // Store current targets data
        this.targets = [];
        
        // Track if we're in edit mode
        this.editMode = false;
        this.currentEditId = null;
        
        // API endpoints
        this.apiEndpoints = {
            list: '/api/targets',
            create: '/api/targets',
            update: '/api/targets/{id}',
            delete: '/api/targets/{id}'
        };
    }
    
    /**
     * Initialize the TargetsManager
     */
    init() {
        // Register for date context changes
        this.dateContextManager.registerContextChangeListener({
            handleDateContextChange: this.handleDateContextChange.bind(this)
        });
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initial load of targets (if date context is valid)
        if (this.dateContextManager.isDateContextValid()) {
            this.loadTargets();
        }
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Form submission
        this.form.addEventListener('submit', this.handleFormSubmit.bind(this));
        
        // Reset button
        const resetButton = this.form.querySelector('button[type="reset"]');
        if (resetButton) {
            resetButton.addEventListener('click', this.handleFormReset.bind(this));
        }
        
        // Related fields updates (region, state, territory cascading selects)
        if (this.fields.region) {
            this.fields.region.addEventListener('change', this.handleRegionChange.bind(this));
        }
        
        if (this.fields.state) {
            this.fields.state.addEventListener('change', this.handleStateChange.bind(this));
        }
        
        // Input validation
        if (this.fields.targetAmount) {
            this.fields.targetAmount.addEventListener('input', this.validateNumericInput.bind(this));
        }
    }
    
    /**
     * Handle date context changes
     * @param {Object} dateContext - The new date context
     */
    handleDateContextChange(dateContext) {
        // Only load targets if we have a valid date context
        if (this.dateContextManager.isDateContextValid()) {
            this.loadTargets();
        } else {
            // Clear the table if the date context is not valid
            this.clearTargetsTable();
        }
    }
    
    /**
     * Load targets for the current date context
     */
    loadTargets() {
        const dateContext = this.dateContextManager.getCurrentDateContext();
        
        // Build query parameters
        const params = new URLSearchParams({
            financialYear: dateContext.financialYear,
            periodType: dateContext.periodType,
            periodIdentifier: dateContext.periodIdentifier
        });
        
        // Show loading indicator
        this.showNotification('Loading targets...', 'info');
        
        // Fetch targets from API
        fetch(`${this.apiEndpoints.list}?${params}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load targets');
                }
                return response.json();
            })
            .then(data => {
                this.targets = data;
                this.updateTargetsTable();
                this.clearNotification();
            })
            .catch(error => {
                console.error('Error loading targets:', error);
                this.showNotification('Failed to load targets: ' + error.message, 'error');
                
                // For demo/development, use sample data
                if (process.env.NODE_ENV === 'development') {
                    this.loadSampleTargets();
                }
            });
    }
    
    /**
     * Load sample targets data for development/demo purposes
     */
    loadSampleTargets() {
        // Sample targets data
        this.targets = [
            {
                id: 1,
                distributor: 'ABC Distributors',
                region: 'North',
                state: 'Punjab',
                territory: 'Ludhiana',
                targetAmount: 500000,
                notes: 'Focus on retail accounts'
            },
            {
                id: 2,
                distributor: 'XYZ Trading',
                region: 'South',
                state: 'Tamil Nadu',
                territory: 'Chennai',
                targetAmount: 750000,
                notes: 'New distributor, provide extra support'
            },
            {
                id: 3,
                distributor: 'Global Enterprises',
                region: 'West',
                state: 'Maharashtra',
                territory: 'Mumbai',
                targetAmount: 1200000,
                notes: ''
            }
        ];
        
        // Update the table with sample data
        this.updateTargetsTable();
        this.showNotification('Loaded sample data (development mode)', 'info', 3000);
    }
    
    /**
     * Update the targets table with current data
     */
    updateTargetsTable() {
        // Clear the table first
        this.clearTargetsTable();
        
        // Add each target as a row
        this.targets.forEach(target => {
            this.addTargetRow(target);
        });
        
        // Show empty state if no targets
        if (this.targets.length === 0) {
            this.showEmptyState();
        }
    }
    
    /**
     * Clear the targets table
     */
    clearTargetsTable() {
        this.tableBody.innerHTML = '';
    }
    
    /**
     * Show empty state in the table
     */
    showEmptyState() {
        const emptyRow = document.createElement('tr');
        const emptyCell = document.createElement('td');
        
        emptyCell.setAttribute('colspan', '7');
        emptyCell.className = 'text-center py-3 text-muted';
        emptyCell.textContent = 'No targets found for the selected period. Add a new target using the form above.';
        
        emptyRow.appendChild(emptyCell);
        this.tableBody.appendChild(emptyRow);
    }
    
    /**
     * Add a target row to the table
     * @param {Object} target - Target data object
     */
    addTargetRow(target) {
        const row = document.createElement('tr');
        row.setAttribute('data-id', target.id);
        
        // Create cells for each column
        const columns = [
            'distributor',
            'region',
            'state',
            'territory',
            'targetAmount'
        ];
        
        columns.forEach(column => {
            const cell = document.createElement('td');
            
            // Format amount as currency
            if (column === 'targetAmount') {
                cell.textContent = new Intl.NumberFormat('en-IN', {
                    style: 'currency',
                    currency: 'INR',
                    maximumFractionDigits: 0
                }).format(target[column]);
            } else {
                cell.textContent = target[column] || '-';
            }
            
            row.appendChild(cell);
        });
        
        // Add actions cell
        const actionsCell = document.createElement('td');
        actionsCell.className = 'text-end';
        
        // Edit button
        const editButton = document.createElement('button');
        editButton.className = 'btn btn-sm btn-outline-primary me-2';
        editButton.innerHTML = '<i class="bi bi-pencil"></i>';
        editButton.addEventListener('click', () => this.handleEditClick(target.id));
        actionsCell.appendChild(editButton);
        
        // Delete button
        const deleteButton = document.createElement('button');
        deleteButton.className = 'btn btn-sm btn-outline-danger';
        deleteButton.innerHTML = '<i class="bi bi-trash"></i>';
        deleteButton.addEventListener('click', () => this.handleDeleteClick(target.id));
        actionsCell.appendChild(deleteButton);
        
        row.appendChild(actionsCell);
        
        // Add the row to the table
        this.tableBody.appendChild(row);
    }
    
    /**
     * Handle form submission
     * @param {Event} event - Submit event
     */
    handleFormSubmit(event) {
        event.preventDefault();
        
        // Validate the form
        if (!this.validateForm()) {
            return;
        }
        
        // Get form data
        const targetData = this.getFormData();
        
        // Add date context
        const dateContext = this.dateContextManager.getCurrentDateContext();
        Object.assign(targetData, {
            financialYear: dateContext.financialYear,
            periodType: dateContext.periodType,
            periodIdentifier: dateContext.periodIdentifier
        });
        
        if (this.editMode) {
            this.updateTarget(this.currentEditId, targetData);
        } else {
            this.createTarget(targetData);
        }
    }
    
    /**
     * Validate the target form
     * @returns {boolean} True if valid, false otherwise
     */
    validateForm() {
        // Check if all required fields are filled
        const requiredFields = ['distributor', 'region', 'targetAmount'];
        let isValid = true;
        
        requiredFields.forEach(field => {
            const element = this.fields[field];
            if (!element.value.trim()) {
                element.classList.add('is-invalid');
                isValid = false;
            } else {
                element.classList.remove('is-invalid');
            }
        });
        
        // Validate target amount is a positive number
        if (this.fields.targetAmount.value && !/^\d+(\.\d{1,2})?$/.test(this.fields.targetAmount.value)) {
            this.fields.targetAmount.classList.add('is-invalid');
            isValid = false;
        }
        
        // Check if date context is valid
        if (!this.dateContextManager.isDateContextValid()) {
            this.showNotification('Please select a valid period before adding targets.', 'warning');
            isValid = false;
        }
        
        return isValid;
    }
    
    /**
     * Get form data as an object
     * @returns {Object} Form data
     */
    getFormData() {
        const data = {};
        
        Object.keys(this.fields).forEach(key => {
            data[key] = this.fields[key].value;
        });
        
        // Convert target amount to number
        if (data.targetAmount) {
            data.targetAmount = parseFloat(data.targetAmount);
        }
        
        return data;
    }
    
    /**
     * Set form data from a target object
     * @param {Object} target - Target data object
     */
    setFormData(target) {
        Object.keys(this.fields).forEach(key => {
            if (key in target) {
                this.fields[key].value = target[key];
            }
        });
    }
    
    /**
     * Create a new target
     * @param {Object} targetData - Target data to create
     */
    createTarget(targetData) {
        // Show loading indicator
        this.showNotification('Creating target...', 'info');
        
        // Send API request
        fetch(this.apiEndpoints.create, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(targetData)
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to create target');
                }
                return response.json();
            })
            .then(data => {
                // Add the new target to the array
                this.targets.push(data);
                
                // Update the table
                this.updateTargetsTable();
                
                // Reset the form
                this.resetForm();
                
                // Show success message
                this.showNotification('Target created successfully', 'success', 3000);
            })
            .catch(error => {
                console.error('Error creating target:', error);
                this.showNotification('Failed to create target: ' + error.message, 'error');
                
                // For demo/development, simulate success
                if (process.env.NODE_ENV === 'development') {
                    const newTarget = {
                        id: this.targets.length > 0 ? Math.max(...this.targets.map(t => t.id)) + 1 : 1,
                        ...targetData
                    };
                    
                    this.targets.push(newTarget);
                    this.updateTargetsTable();
                    this.resetForm();
                    this.showNotification('Target created successfully (development mode)', 'success', 3000);
                }
            });
    }
    
    /**
     * Update an existing target
     * @param {number} id - Target ID to update
     * @param {Object} targetData - New target data
     */
    updateTarget(id, targetData) {
        // Show loading indicator
        this.showNotification('Updating target...', 'info');
        
        // Send API request
        const url = this.apiEndpoints.update.replace('{id}', id);
        
        fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(targetData)
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to update target');
                }
                return response.json();
            })
            .then(data => {
                // Update the target in the array
                const index = this.targets.findIndex(target => target.id === id);
                if (index !== -1) {
                    this.targets[index] = data;
                }
                
                // Update the table
                this.updateTargetsTable();
                
                // Reset the form and edit mode
                this.exitEditMode();
                
                // Show success message
                this.showNotification('Target updated successfully', 'success', 3000);
            })
            .catch(error => {
                console.error('Error updating target:', error);
                this.showNotification('Failed to update target: ' + error.message, 'error');
                
                // For demo/development, simulate success
                if (process.env.NODE_ENV === 'development') {
                    const index = this.targets.findIndex(target => target.id === id);
                    if (index !== -1) {
                        this.targets[index] = { id, ...targetData };
                    }
                    
                    this.updateTargetsTable();
                    this.exitEditMode();
                    this.showNotification('Target updated successfully (development mode)', 'success', 3000);
                }
            });
    }
    
    /**
     * Delete a target
     * @param {number} id - Target ID to delete
     */
    deleteTarget(id) {
        // Show loading indicator
        this.showNotification('Deleting target...', 'info');
        
        // Send API request
        const url = this.apiEndpoints.delete.replace('{id}', id);
        
        fetch(url, {
            method: 'DELETE'
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to delete target');
                }
                
                // Remove the target from the array
                this.targets = this.targets.filter(target => target.id !== id);
                
                // Update the table
                this.updateTargetsTable();
                
                // Show success message
                this.showNotification('Target deleted successfully', 'success', 3000);
            })
            .catch(error => {
                console.error('Error deleting target:', error);
                this.showNotification('Failed to delete target: ' + error.message, 'error');
                
                // For demo/development, simulate success
                if (process.env.NODE_ENV === 'development') {
                    this.targets = this.targets.filter(target => target.id !== id);
                    this.updateTargetsTable();
                    this.showNotification('Target deleted successfully (development mode)', 'success', 3000);
                }
            });
    }
    
    /**
     * Handle edit button click
     * @param {number} id - Target ID to edit
     */
    handleEditClick(id) {
        // Find the target
        const target = this.targets.find(target => target.id === id);
        
        if (!target) {
            this.showNotification('Target not found', 'error');
            return;
        }
        
        // Enter edit mode
        this.enterEditMode(id);
        
        // Populate form with target data
        this.setFormData(target);
        
        // Scroll to form
        this.form.scrollIntoView({ behavior: 'smooth' });
    }
    
    /**
     * Handle delete button click
     * @param {number} id - Target ID to delete
     */
    handleDeleteClick(id) {
        // Confirm deletion
        if (confirm('Are you sure you want to delete this target?')) {
            this.deleteTarget(id);
        }
    }
    
    /**
     * Handle form reset
     * @param {Event} event - Reset event
     */
    handleFormReset(event) {
        // If in edit mode, exit edit mode
        if (this.editMode) {
            this.exitEditMode();
        }
    }
    
    /**
     * Enter edit mode
     * @param {number} id - Target ID being edited
     */
    enterEditMode(id) {
        this.editMode = true;
        this.currentEditId = id;
        
        // Update form button text
        const submitButton = this.form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.textContent = 'Update Target';
        }
        
        // Add edit mode class to form
        this.form.classList.add('edit-mode');
    }
    
    /**
     * Exit edit mode
     */
    exitEditMode() {
        this.editMode = false;
        this.currentEditId = null;
        
        // Reset form
        this.resetForm();
        
        // Update form button text
        const submitButton = this.form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.textContent = 'Add Target';
        }
        
        // Remove edit mode class from form
        this.form.classList.remove('edit-mode');
    }
    
    /**
     * Reset the form
     */
    resetForm() {
        this.form.reset();
        
        // Remove validation classes
        Object.values(this.fields).forEach(field => {
            field.classList.remove('is-invalid');
        });
    }
    
    /**
     * Handle region change (cascading dropdown)
     */
    handleRegionChange() {
        const region = this.fields.region.value;
        
        // Clear state and territory selects
        this.fields.state.innerHTML = '<option value="">Select State</option>';
        this.fields.territory.innerHTML = '<option value="">Select Territory</option>';
        
        // Populate states based on selected region
        if (region) {
            this.populateStates(region);
        }
    }
    
    /**
     * Handle state change (cascading dropdown)
     */
    handleStateChange() {
        const state = this.fields.state.value;
        
        // Clear territory select
        this.fields.territory.innerHTML = '<option value="">Select Territory</option>';
        
        // Populate territories based on selected state
        if (state) {
            this.populateTerritories(state);
        }
    }
    
    /**
     * Populate states based on region (would connect to API in production)
     * @param {string} region - Selected region
     */
    populateStates(region) {
        // In production, this would call an API endpoint to get states by region
        // For demo/development, use sample data
        
        const statesByRegion = {
            'North': ['Delhi', 'Haryana', 'Punjab', 'Uttar Pradesh'],
            'South': ['Andhra Pradesh', 'Karnataka', 'Kerala', 'Tamil Nadu', 'Telangana'],
            'East': ['Bihar', 'Jharkhand', 'Odisha', 'West Bengal'],
            'West': ['Gujarat', 'Maharashtra', 'Rajasthan'],
            'Central': ['Madhya Pradesh', 'Chhattisgarh']
        };
        
        const states = statesByRegion[region] || [];
        
        // Add states to select
        states.forEach(state => {
            const option = document.createElement('option');
            option.value = state;
            option.textContent = state;
            this.fields.state.appendChild(option);
        });
    }
    
    /**
     * Populate territories based on state (would connect to API in production)
     * @param {string} state - Selected state
     */
    populateTerritories(state) {
        // In production, this would call an API endpoint to get territories by state
        // For demo/development, use sample data
        
        const territoriesByState = {
            'Delhi': ['Delhi Central', 'Delhi East', 'Delhi West', 'Delhi South', 'Delhi North'],
            'Maharashtra': ['Mumbai', 'Pune', 'Nagpur', 'Nashik', 'Aurangabad'],
            'Tamil Nadu': ['Chennai', 'Coimbatore', 'Madurai', 'Tiruchirappalli', 'Salem'],
            'Gujarat': ['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Bhavnagar'],
            'Punjab': ['Ludhiana', 'Amritsar', 'Jalandhar', 'Patiala', 'Bathinda'],
            // Add more states and territories as needed
        };
        
        const territories = territoriesByState[state] || [];
        
        // Add territories to select
        territories.forEach(territory => {
            const option = document.createElement('option');
            option.value = territory;
            option.textContent = territory;
            this.fields.territory.appendChild(option);
        });
    }
    
    /**
     * Validate numeric input for target amount
     * @param {Event} event - Input event
     */
    validateNumericInput(event) {
        const input = event.target;
        const value = input.value;
        
        // Allow only numbers and up to two decimal places
        if (value && !/^\d*\.?\d{0,2}$/.test(value)) {
            input.value = input.dataset.lastValidValue || '';
        } else {
            input.dataset.lastValidValue = value;
        }
    }
    
    /**
     * Show a notification message
     * @param {string} message - Message to display
     * @param {string} type - Message type (success, error, warning, info)
     * @param {number} [timeout] - Auto-hide timeout in milliseconds
     */
    showNotification(message, type, timeout) {
        if (!this.notificationArea) return;
        
        // Clear any existing notification
        this.clearNotification();
        
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show mt-3`;
        alert.setAttribute('role', 'alert');
        
        // Add message
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Add to notification area
        this.notificationArea.appendChild(alert);
        
        // Set up auto-hide if timeout is provided
        if (timeout) {
            setTimeout(() => {
                this.clearNotification();
            }, timeout);
        }
    }
    
    /**
     * Clear the notification area
     */
    clearNotification() {
        if (this.notificationArea) {
            this.notificationArea.innerHTML = '';
        }
    }
}

// Initialize TargetsManager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const dateContextManager = new DateContextManager('fy-select', 'period-type-select', 'period-identifier-select');
    dateContextManager.loadFinancialYears().then(() => {
        dateContextManager.onPeriodTypeChange();
    });
    
    const targetsManager = new TargetsManager({
        formId: 'targets-form',
        tableId: 'targets-table',
        notificationAreaId: 'notification'
    }, dateContextManager);
    targetsManager.init();
}); 