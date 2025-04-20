/**
 * targets-init.js
 * Initializes the targets management interface components
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the Date Context Manager
    const dateContextManager = new DateContextManager({
        financialYearSelectId: 'financial-year-select',
        periodTypeSelectId: 'period-type-select',
        periodIdentifierSelectId: 'period-identifier-select',
        periodLabelId: 'period-label',
        startYear: new Date().getFullYear() - 2,
        yearCount: 5
    });
    
    // Initialize the Targets Manager
    const targetsManager = new TargetsManager({
        formId: 'target-form',
        tableId: 'targets-table',
        saveButtonId: 'save-target-btn',
        resetButtonId: 'reset-target-btn',
        notificationId: 'notification',
        distributorFieldId: 'distributor-select',
        regionFieldId: 'region-select',
        stateFieldId: 'state-select',
        territoryFieldId: 'territory-select',
        targetAmountFieldId: 'target-amount',
        notesFieldId: 'target-notes',
        targetIdFieldId: 'target-id',
        periodLabelId: 'period-label'
    });
    
    // Initialize both managers
    dateContextManager.init();
    targetsManager.init();
    
    // Register the targets manager as a listener for date context changes
    dateContextManager.registerListener(function(dateContext) {
        // When date context changes, load targets for the new period
        if (dateContext.financialYear && dateContext.periodType && dateContext.periodIdentifier) {
            targetsManager.loadTargets(dateContext);
        }
    });
    
    // Load initial targets if date context is available
    const initialDateContext = dateContextManager.getCurrentDateContext();
    if (initialDateContext.financialYear && initialDateContext.periodType && initialDateContext.periodIdentifier) {
        targetsManager.loadTargets(initialDateContext);
    }
    
    console.log('Targets management interface initialized');
}); 