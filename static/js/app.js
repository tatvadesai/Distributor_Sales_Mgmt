/**
 * Enterprise Sales Management App JavaScript
 */

// Toast notification system
class ToastManager {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        document.body.appendChild(this.container);
        
        // Store deleted items for potential undo
        this.deletedItems = {};
        this.timeouts = {};
    }
    
    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - The type of toast (success, error, info)
     * @param {Object} options - Additional options
     * @param {number} options.duration - Duration in ms to show the toast
     * @param {boolean} options.showUndo - Whether to show undo button
     * @param {string} options.itemType - Type of item deleted (for undo)
     * @param {number} options.itemId - ID of item deleted (for undo)
     * @param {Object} options.itemData - Data of item deleted (for undo)
     */
    show(message, type = 'info', options = {}) {
        const defaults = {
            duration: 5000,
            showUndo: false,
            itemType: null,
            itemId: null,
            itemData: null
        };
        
        const settings = {...defaults, ...options};
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        // Toast content
        const contentDiv = document.createElement('div');
        contentDiv.className = 'toast-content';
        
        // Icon
        const icon = document.createElement('i');
        if (type === 'success') {
            icon.className = 'fas fa-check-circle';
        } else if (type === 'error') {
            icon.className = 'fas fa-exclamation-circle';
        } else {
            icon.className = 'fas fa-info-circle';
        }
        contentDiv.appendChild(icon);
        
        // Message
        const messageSpan = document.createElement('span');
        messageSpan.textContent = message;
        contentDiv.appendChild(messageSpan);
        
        toast.appendChild(contentDiv);
        
        // Add undo button if needed
        if (settings.showUndo && settings.itemType && settings.itemId) {
            const undoLink = document.createElement('a');
            undoLink.className = 'toast-action';
            undoLink.textContent = 'Undo';
            undoLink.addEventListener('click', () => this.undoDelete(settings.itemType, settings.itemId, settings.itemData));
            toast.appendChild(undoLink);
            
            // Store deleted item data
            this.deletedItems[`${settings.itemType}-${settings.itemId}`] = settings.itemData;
        }
        
        // Add to container
        this.container.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        // Remove after duration
        const toastId = Date.now();
        this.timeouts[toastId] = setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                this.container.removeChild(toast);
                delete this.timeouts[toastId];
            }, 300);
        }, settings.duration);
        
        return toastId;
    }
    
    /**
     * Undo a delete operation
     * @param {string} itemType - Type of item (distributor, target, actual)
     * @param {number} itemId - ID of the item
     * @param {Object} itemData - Data of the item
     */
    undoDelete(itemType, itemId, itemData) {
        const key = `${itemType}-${itemId}`;
        if (this.deletedItems[key]) {
            // Call API to restore the deleted item
            fetch(`/api/restore/${itemType}/${itemId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(itemData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.show(`${itemType} restored successfully!`, 'success');
                    // Reload the page to show the restored item
                    location.reload();
                } else {
                    this.show(`Error restoring ${itemType}: ${data.message}`, 'error');
                }
            })
            .catch(error => {
                this.show(`Error restoring ${itemType}: ${error}`, 'error');
            });
            
            // Remove from deleted items
            delete this.deletedItems[key];
        }
    }
    
    /**
     * Clear all toasts
     */
    clearAll() {
        for (const id in this.timeouts) {
            clearTimeout(this.timeouts[id]);
        }
        this.container.innerHTML = '';
        this.timeouts = {};
    }
}

// Initialize toast manager
const toastManager = new ToastManager();

/**
 * Direct delete functionality without confirmation modal
 * @param {string} itemType - Type of item to delete
 * @param {number} itemId - ID of the item
 * @param {string} itemName - Name of the item for display
 */
function directDelete(itemType, itemId, itemName) {
    // Get current item data for potential undo
    let endpoint = '';
    if (itemType === 'distributor') {
        endpoint = `/api/distributors/${itemId}`;
    } else if (itemType === 'target') {
        endpoint = `/api/targets/${itemId}`;
    } else if (itemType === 'actual') {
        endpoint = `/api/actuals/${itemId}`;
    }
    
    // First get item data
    fetch(endpoint)
        .then(response => response.json())
        .then(itemData => {
            // Make delete request
            fetch(`/${itemType}s/${itemId}/delete`, {
                method: 'POST',
            })
            .then(response => {
                // Check if the request was successful
                if (response.ok) {
                    // Remove the item from the DOM
                    const row = document.getElementById(`${itemType}-${itemId}`);
                    if (row) row.remove();
                    
                    // Show toast with undo option
                    toastManager.show(
                        `${itemType.charAt(0).toUpperCase() + itemType.slice(1)} '${itemName}' deleted.`,
                        'success',
                        {
                            showUndo: true,
                            itemType: itemType,
                            itemId: itemId,
                            itemData: itemData
                        }
                    );
                } else {
                    // Handle error
                    response.json().then(data => {
                        toastManager.show(`Error deleting ${itemType}: ${data.message}`, 'error');
                    }).catch(() => {
                        toastManager.show(`Error deleting ${itemType}`, 'error');
                    });
                }
            })
            .catch(error => {
                toastManager.show(`Error: ${error.message}`, 'error');
            });
        })
        .catch(error => {
            // If we can't get item data, still try to delete
            fetch(`/${itemType}s/${itemId}/delete`, {
                method: 'POST',
            })
            .then(response => {
                if (response.ok) {
                    const row = document.getElementById(`${itemType}-${itemId}`);
                    if (row) row.remove();
                    toastManager.show(`${itemType.charAt(0).toUpperCase() + itemType.slice(1)} deleted.`, 'success');
                } else {
                    toastManager.show(`Error deleting ${itemType}`, 'error');
                }
            });
        });
}

/**
 * Apply tab-specific class to body based on current URL
 */
function setTabClass() {
    const path = window.location.pathname;
    let tabClass = 'tab-dashboard';
    
    if (path.includes('/distributor')) {
        tabClass = 'tab-distributors';
    } else if (path.includes('/target')) {
        tabClass = 'tab-targets';
    } else if (path.includes('/actual')) {
        tabClass = 'tab-actuals';
    } else if (path.includes('/report')) {
        tabClass = 'tab-reports';
    } else if (path.includes('/backup')) {
        tabClass = 'tab-backup';
    } else if (path.includes('/dashboard')) {
        tabClass = 'tab-dashboard';
    }
    
    // Remove any existing tab classes
    document.body.classList.remove(
        'tab-dashboard', 
        'tab-distributors', 
        'tab-targets', 
        'tab-actuals', 
        'tab-reports', 
        'tab-backup'
    );
    
    // Add the current tab class
    document.body.classList.add(tabClass);
}

/**
 * Format flash messages as toasts
 */
function convertFlashToToast() {
    // Look for Flask flash messages
    const flashMessages = document.querySelectorAll('.alert');
    
    flashMessages.forEach(flash => {
        const message = flash.textContent.trim();
        let type = 'info';
        
        if (flash.classList.contains('alert-success')) {
            type = 'success';
        } else if (flash.classList.contains('alert-danger')) {
            type = 'error';
        }
        
        // Show as toast
        toastManager.show(message, type);
        
        // Remove original flash
        flash.remove();
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set tab class
    setTabClass();
    
    // Convert flash messages to toasts
    convertFlashToToast();
    
    // Setup action buttons with consistent styling
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.classList.add('btn-action-delete');
        
        // Replace onclick with directDelete
        if (btn.dataset.itemType && btn.dataset.itemId && btn.dataset.itemName) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                directDelete(
                    btn.dataset.itemType,
                    btn.dataset.itemId,
                    btn.dataset.itemName
                );
            });
        }
    });
    
    document.querySelectorAll('.btn-edit').forEach(btn => {
        btn.classList.add('btn-action-edit');
    });
    
    document.querySelectorAll('.btn-submit').forEach(btn => {
        btn.classList.add('btn-action-submit');
    });
}); 