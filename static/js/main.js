// Main JavaScript file for interactive functionality

document.addEventListener('DOMContentLoaded', function() {
    console.log('SecureKey Workspace Agent UI loaded');
    
    // Check API status
    checkApiStatus();
    
    // Initialize theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Initialize tooltips if Bootstrap's JS is loaded
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});

// Function to check API connection status
function checkApiStatus() {
    fetch('/health')
        .then(response => {
            if (!response.ok) {
                throw new Error('API connection failed');
            }
            return response.json();
        })
        .then(data => {
            console.log('API status:', data);
            if (data.status === 'healthy') {
                // Update UI to show API is connected
                document.querySelectorAll('.badge.bg-warning').forEach(badge => {
                    badge.classList.remove('bg-warning');
                    badge.classList.add('bg-success');
                    badge.textContent = 'Available';
                });
            }
        })
        .catch(error => {
            console.error('Error checking API status:', error);
        });
}

// Currently disabled functions that would be implemented in a complete version:

// Function to test Google Workspace connection
function testGoogleConnection() {
    // This would make an API call to test Google connection
    // For now it's just a placeholder
    console.log('Testing Google Workspace connection...');
}

// Function to test Notion connection
function testNotionConnection() {
    // This would make an API call to test Notion connection
    // For now it's just a placeholder
    console.log('Testing Notion connection...');
}

// Function to test GitHub connection
function testGitHubConnection() {
    // This would make an API call to test GitHub connection
    // For now it's just a placeholder

function toggleTheme() {
    const root = document.documentElement;
    const currentTheme = root.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    root.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.textContent = newTheme === 'dark' ? '☀️' : '🌙';
    }
}

    console.log('Testing GitHub connection...');
}