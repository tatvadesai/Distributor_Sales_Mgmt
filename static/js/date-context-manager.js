/**
 * Date Context Manager
 * 
 * Manages the date context (financial year, period type, period identifier) for the application.
 * Handles populating select options and maintaining the current date context.
 */
class DateContextManager {
    /**
     * Constructor for the DateContextManager
     * 
     * @param {string} financialYearSelectId - ID of the financial year select element
     * @param {string} periodTypeSelectId - ID of the period type select element
     * @param {string} periodIdentifierSelectId - ID of the period identifier select element
     * @param {string} periodLabelId - ID of the element to display the current period
     */
    constructor(financialYearSelectId, periodTypeSelectId, periodIdentifierSelectId, periodLabelId) {
        this.financialYearSelect = document.getElementById(financialYearSelectId);
        this.periodTypeSelect = document.getElementById(periodTypeSelectId);
        this.periodIdentifierSelect = document.getElementById(periodIdentifierSelectId);
        this.periodLabel = document.getElementById(periodLabelId);
        
        this.contextChangeListeners = [];
        this.currentDateContext = {
            financialYear: null,
            periodType: null,
            periodIdentifier: null
        };
        
        // Financial years (typically -2 to +1 from current)
        this.financialYears = this.generateFinancialYears();
        
        // Period mapping
        this.periodMapping = {
            monthly: {
                values: Array.from({ length: 12 }, (_, i) => i + 1),
                labels: [
                    'April', 'May', 'June', 'July', 'August', 'September',
                    'October', 'November', 'December', 'January', 'February', 'March'
                ]
            },
            quarterly: {
                values: [1, 2, 3, 4],
                labels: ['Q1 (Apr-Jun)', 'Q2 (Jul-Sep)', 'Q3 (Oct-Dec)', 'Q4 (Jan-Mar)']
            },
            'half-yearly': {
                values: [1, 2],
                labels: ['H1 (Apr-Sep)', 'H2 (Oct-Mar)']
            },
            yearly: {
                values: [1],
                labels: ['Full Year']
            }
        };
    }
    
    /**
     * Generate financial years for selection
     * @returns {Array} Array of financial year objects with value and label
     */
    generateFinancialYears() {
        const currentYear = new Date().getFullYear();
        const years = [];
        
        // Generate financial years from (current - 2) to (current + 1)
        for (let i = -2; i <= 1; i++) {
            const startYear = currentYear + i;
            const endYear = startYear + 1;
            years.push({
                value: `${startYear}-${endYear}`,
                label: `${startYear}-${endYear}`
            });
        }
        
        return years;
    }
    
    /**
     * Initialize the date context manager
     */
    init() {
        this.populateFinancialYears();
        this.setupEventListeners();
        
        // Set default selections
        this.setDefaultSelections();
    }
    
    /**
     * Populate financial year select options
     */
    populateFinancialYears() {
        this.financialYearSelect.innerHTML = '';
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select Financial Year';
        this.financialYearSelect.appendChild(defaultOption);
        
        // Add financial years
        this.financialYears.forEach(year => {
            const option = document.createElement('option');
            option.value = year.value;
            option.textContent = year.label;
            this.financialYearSelect.appendChild(option);
        });
    }
    
    /**
     * Populate period identifier options based on selected period type
     */
    populatePeriodIdentifiers() {
        const periodType = this.periodTypeSelect.value;
        this.periodIdentifierSelect.innerHTML = '';
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select Period';
        this.periodIdentifierSelect.appendChild(defaultOption);
        
        if (periodType && this.periodMapping[periodType]) {
            const periods = this.periodMapping[periodType];
            
            for (let i = 0; i < periods.values.length; i++) {
                const option = document.createElement('option');
                option.value = periods.values[i];
                option.textContent = periods.labels[i];
                this.periodIdentifierSelect.appendChild(option);
            }
        }
    }
    
    /**
     * Set up event listeners for select elements
     */
    setupEventListeners() {
        // Financial year change
        this.financialYearSelect.addEventListener('change', () => {
            this.updateDateContext();
        });
        
        // Period type change
        this.periodTypeSelect.addEventListener('change', () => {
            this.populatePeriodIdentifiers();
            this.updateDateContext();
        });
        
        // Period identifier change
        this.periodIdentifierSelect.addEventListener('change', () => {
            this.updateDateContext();
        });
    }
    
    /**
     * Set default selections
     */
    setDefaultSelections() {
        // Default to current financial year
        const currentDate = new Date();
        const currentYear = currentDate.getFullYear();
        const currentMonth = currentDate.getMonth() + 1; // JavaScript months are 0-indexed
        
        // Financial year runs from April to March
        let financialYearStart = currentYear;
        if (currentMonth < 4) { // Before April
            financialYearStart = currentYear - 1;
        }
        
        const financialYear = `${financialYearStart}-${financialYearStart + 1}`;
        
        // Set financial year
        if (this.financialYearSelect.querySelector(`option[value="${financialYear}"]`)) {
            this.financialYearSelect.value = financialYear;
        }
        
        // Default to monthly period type
        this.periodTypeSelect.value = 'monthly';
        
        // Populate period identifiers
        this.populatePeriodIdentifiers();
        
        // Default to current month in financial year (1-indexed where 1 is April)
        let financialMonth;
        if (currentMonth >= 4) { // April to December
            financialMonth = currentMonth - 3;
        } else { // January to March
            financialMonth = currentMonth + 9;
        }
        
        if (this.periodIdentifierSelect.querySelector(`option[value="${financialMonth}"]`)) {
            this.periodIdentifierSelect.value = financialMonth;
        }
        
        // Update the date context with default values
        this.updateDateContext();
    }
    
    /**
     * Update the current date context and notify listeners
     */
    updateDateContext() {
        // Update current date context
        this.currentDateContext = {
            financialYear: this.financialYearSelect.value,
            periodType: this.periodTypeSelect.value,
            periodIdentifier: this.periodIdentifierSelect.value
        };
        
        // Update period label
        this.updatePeriodLabel();
        
        // Notify listeners of context change
        this.notifyContextChangeListeners();
    }
    
    /**
     * Update the period label with the current selection
     */
    updatePeriodLabel() {
        const label = this.getFormattedPeriodLabel();
        if (this.periodLabel) {
            this.periodLabel.textContent = label ? `Current Period: ${label}` : 'Current Period: Not Set';
        }
    }
    
    /**
     * Get a formatted label for the current period
     * @returns {string} Formatted period label
     */
    getFormattedPeriodLabel() {
        const { financialYear, periodType, periodIdentifier } = this.currentDateContext;
        
        if (!financialYear || !periodType || !periodIdentifier) {
            return '';
        }
        
        const periodLabel = this.periodMapping[periodType].labels[
            this.periodMapping[periodType].values.indexOf(Number(periodIdentifier))
        ];
        
        return `${financialYear} - ${periodLabel}`;
    }
    
    /**
     * Register a listener for date context changes
     * @param {Object} listener - Listener object with handleDateContextChange method
     */
    registerContextChangeListener(listener) {
        if (typeof listener.handleDateContextChange === 'function') {
            this.contextChangeListeners.push(listener);
        }
    }
    
    /**
     * Notify all registered listeners of a date context change
     */
    notifyContextChangeListeners() {
        this.contextChangeListeners.forEach(listener => {
            listener.handleDateContextChange(this.currentDateContext);
        });
    }
    
    /**
     * Get the current date context
     * @returns {Object} Current date context
     */
    getCurrentDateContext() {
        return { ...this.currentDateContext };
    }
    
    /**
     * Check if the current date context is valid
     * @returns {boolean} True if valid, false otherwise
     */
    isDateContextValid() {
        const { financialYear, periodType, periodIdentifier } = this.currentDateContext;
        return Boolean(financialYear && periodType && periodIdentifier);
    }
} 