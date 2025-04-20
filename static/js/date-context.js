/**
 * DateContextManager - A class to manage date context selection for targets and actuals
 * Handles loading financial years, period types, and period identifiers
 */
class DateContextManager {
    /**
     * Constructor
     * @param {string} financialYearId - ID of the financial year select element
     * @param {string} periodTypeId - ID of the period type select element
     * @param {string} periodIdentifierId - ID of the period identifier select element
     */
    constructor(financialYearId, periodTypeId, periodIdentifierId) {
        this.financialYearSelect = document.getElementById(financialYearId);
        this.periodTypeSelect = document.getElementById(periodTypeId);
        this.periodIdentifierSelect = document.getElementById(periodIdentifierId);
        
        // Current date for default values
        this.currentDate = new Date();
        this.currentYear = this.currentDate.getFullYear();
        this.currentMonth = this.currentDate.getMonth() + 1; // JS months are 0-indexed
    }
    
    /**
     * Load financial years into the select element
     * Creates financial years from 5 years ago to 5 years in the future
     * @returns {Promise} - Resolves when years are loaded
     */
    loadFinancialYears() {
        return new Promise((resolve) => {
            // Clear existing options
            this.financialYearSelect.innerHTML = '';
            
            // Get current financial year (April to March)
            let currentFinancialYear;
            if (this.currentMonth >= 4) { // April onwards
                currentFinancialYear = `${this.currentYear}-${this.currentYear + 1}`;
            } else { // January to March
                currentFinancialYear = `${this.currentYear - 1}-${this.currentYear}`;
            }
            
            // Add options for 5 years before and after current financial year
            for (let i = -5; i <= 5; i++) {
                const startYear = this.currentYear + i;
                const endYear = startYear + 1;
                const financialYear = `${startYear}-${endYear}`;
                
                const option = document.createElement('option');
                option.value = financialYear;
                option.textContent = financialYear;
                
                // Set current financial year as selected
                if (financialYear === currentFinancialYear) {
                    option.selected = true;
                }
                
                this.financialYearSelect.appendChild(option);
            }
            
            resolve();
        });
    }
    
    /**
     * Handle period type change
     * Loads appropriate period identifiers based on selected period type
     */
    onPeriodTypeChange() {
        const periodType = this.periodTypeSelect.value;
        const financialYear = this.financialYearSelect.value;
        
        if (!financialYear) return;
        
        // Parse financial year
        const [startYearStr, endYearStr] = financialYear.split('-');
        const startYear = parseInt(startYearStr, 10);
        const endYear = parseInt(endYearStr, 10);
        
        // Clear existing options
        this.periodIdentifierSelect.innerHTML = '';
        
        switch (periodType) {
            case 'Weekly':
                this.loadWeeklyPeriods(startYear, endYear);
                break;
            case 'Monthly':
                this.loadMonthlyPeriods(startYear, endYear);
                break;
            case 'Yearly':
                this.loadYearlyPeriods(startYear, endYear);
                break;
        }
    }
    
    /**
     * Handle financial year change
     * Reloads period identifiers based on new financial year
     */
    onFinancialYearChange() {
        this.onPeriodTypeChange();
    }
    
    /**
     * Load weekly periods for the selected financial year
     * @param {number} startYear - Start year of financial year
     * @param {number} endYear - End year of financial year
     */
    loadWeeklyPeriods(startYear, endYear) {
        // Financial year starts on April 1st and ends on March 31st
        const startDate = new Date(startYear, 3, 1); // April 1st
        const endDate = new Date(endYear, 2, 31); // March 31st
        
        // Get the Monday of the week containing April 1st
        const firstMonday = new Date(startDate);
        const dayOfWeek = firstMonday.getDay(); // 0 = Sunday, 1 = Monday, ...
        const daysToAdd = dayOfWeek === 0 ? 1 : dayOfWeek === 1 ? 0 : -(dayOfWeek - 1);
        firstMonday.setDate(firstMonday.getDate() + daysToAdd);
        
        // Generate weekly periods
        let currentWeekStart = new Date(firstMonday);
        let weekNumber = 1;
        
        while (currentWeekStart <= endDate) {
            // Calculate end of week (Sunday)
            const weekEnd = new Date(currentWeekStart);
            weekEnd.setDate(weekEnd.getDate() + 6);
            
            // Format dates as strings
            const startDateStr = this.formatDate(currentWeekStart);
            const endDateStr = this.formatDate(weekEnd);
            
            // Create option
            const option = document.createElement('option');
            option.value = `${startDateStr} to ${endDateStr}`;
            option.textContent = `Week ${weekNumber}: ${startDateStr} to ${endDateStr}`;
            
            // Set current week as selected
            const now = new Date();
            if (now >= currentWeekStart && now <= weekEnd) {
                option.selected = true;
            }
            
            this.periodIdentifierSelect.appendChild(option);
            
            // Move to next week
            currentWeekStart.setDate(currentWeekStart.getDate() + 7);
            weekNumber++;
        }
    }
    
    /**
     * Load monthly periods for the selected financial year
     * @param {number} startYear - Start year of financial year
     * @param {number} endYear - End year of financial year
     */
    loadMonthlyPeriods(startYear, endYear) {
        const months = [
            'April', 'May', 'June', 'July', 'August', 'September',
            'October', 'November', 'December', 'January', 'February', 'March'
        ];
        
        // First 9 months are in startYear, last 3 are in endYear
        for (let i = 0; i < 12; i++) {
            const month = months[i];
            const year = i < 9 ? startYear : endYear;
            const monthValue = `${month} ${year}`;
            
            const option = document.createElement('option');
            option.value = monthValue;
            option.textContent = monthValue;
            
            // Set current month as selected
            const currentMonth = this.currentDate.getMonth();
            const adjustedCurrentMonth = (currentMonth + 9) % 12; // Adjust for financial year (April = 0)
            
            if (adjustedCurrentMonth === i && 
                ((i < 9 && this.currentYear === startYear) || 
                 (i >= 9 && this.currentYear === endYear))) {
                option.selected = true;
            }
            
            this.periodIdentifierSelect.appendChild(option);
        }
    }
    
    /**
     * Load yearly periods
     * @param {number} startYear - Start year of financial year
     * @param {number} endYear - End year of financial year
     */
    loadYearlyPeriods(startYear, endYear) {
        const option = document.createElement('option');
        option.value = `${startYear}-${endYear}`;
        option.textContent = `Financial Year ${startYear}-${endYear}`;
        option.selected = true;
        
        this.periodIdentifierSelect.appendChild(option);
    }
    
    /**
     * Format date as YYYY-MM-DD
     * @param {Date} date - Date to format
     * @returns {string} - Formatted date
     */
    formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        
        return `${year}-${month}-${day}`;
    }
}

// Initialize once DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a targets or sales page
    const targetForm = document.querySelector('.target-form');
    const salesForm = document.querySelector('.sales-form');
    
    if (targetForm) {
        window.targetDateContext = new DateContextManager('target-fy', 'target-period-type', 'target-period-identifier');
        window.targetDateContext.init();
    }
    
    if (salesForm) {
        window.salesDateContext = new DateContextManager('sales-fy', 'sales-period-type', 'sales-period-identifier');
        window.salesDateContext.init();
    }
}); 