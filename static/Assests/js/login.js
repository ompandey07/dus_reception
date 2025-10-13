// Hide preloader on page load
window.addEventListener('load', function() {
    setTimeout(() => {
        const preloader = document.getElementById('topBarPreloader');
        if (preloader) {
            preloader.classList.add('hide');
        }
    }, 500);
});

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Show toast notification
function showToast(message, type = 'error') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    
    const isError = type === 'error';
    const borderColor = isError ? 'border-red-500' : 'border-green-500';
    const iconColor = isError ? '#ef4444' : '#10b981';
    const iconPath = isError 
        ? `<circle cx="12" cy="12" r="10"></circle><line x1="12" x2="12" y1="8" y2="12"></line><line x1="12" x2="12.01" y1="16" y2="16"></line>`
        : `<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>`;
    
    toast.className = `toast relative bg-white border-l-4 ${borderColor} p-4 shadow-lg min-w-[300px]`;
    
    toast.innerHTML = `
        <div class="flex items-start gap-3">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="${iconColor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
                ${iconPath}
            </svg>
            <div class="flex-1">
                <p class="font-semibold text-gray-800">${isError ? 'Error' : 'Success'}</p>
                <p class="text-sm text-gray-600">${message}</p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="text-gray-400 hover:text-gray-600">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" x2="6" y1="6" y2="18"></line>
                    <line x1="6" x2="18" y1="6" y2="18"></line>
                </svg>
            </button>
        </div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Show preloader
function showPreloader() {
    const preloader = document.getElementById('topBarPreloader');
    if (preloader) {
        preloader.classList.remove('hide');
        preloader.style.opacity = '1';
        preloader.style.visibility = 'visible';
    }
}

// Hide preloader
function hidePreloader() {
    const preloader = document.getElementById('topBarPreloader');
    if (preloader) {
        preloader.classList.add('hide');
    }
}

// Initialize login form handler
function initLoginForm(loginUrl) {
    const form = document.getElementById('loginForm');
    if (!form) return;
    
    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        
        const email = document.getElementById('emailInput').value.trim();
        const password = document.getElementById('passwordInput').value.trim();
        
        // Validation
        if (!email && !password) {
            showToast('Email and Password are required');
            return;
        }
        
        if (!email) {
            showToast('Email is required');
            return;
        }
        
        if (!password) {
            showToast('Password is required');
            return;
        }
        
        const button = document.getElementById('loginButton');
        const buttonText = document.getElementById('buttonText');
        const buttonIcon = document.getElementById('buttonIcon');
        
        // Show loading state
        showPreloader();
        button.disabled = true;
        button.classList.add('opacity-75');
        buttonIcon.innerHTML = `
            <div class="spinner-dots">
                <div class="spinner-dot"></div>
                <div class="spinner-dot"></div>
                <div class="spinner-dot"></div>
            </div>
        `;
        buttonText.textContent = 'Logging in...';
        
        try {
            const csrftoken = getCookie('csrftoken');
            
            const response = await fetch(loginUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });

            const data = await response.json();
            
            if (response.ok && data.success) {
                // Show success message briefly before redirect
                showToast(data.message || 'Login successful!', 'success');
                
                // Redirect to the appropriate dashboard
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 500);
            } else {
                hidePreloader();
                
                // Extract error message
                let errorMessage = 'Invalid email or password';
                
                if (data.error) {
                    errorMessage = data.error;
                } else if (data.email) {
                    errorMessage = Array.isArray(data.email) ? data.email[0] : data.email;
                } else if (data.password) {
                    errorMessage = Array.isArray(data.password) ? data.password[0] : data.password;
                } else if (data.non_field_errors) {
                    errorMessage = Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : data.non_field_errors;
                } else if (data.detail) {
                    errorMessage = data.detail;
                }
                
                showToast(errorMessage);
                
                // Reset button state
                resetButton(button, buttonText, buttonIcon);
            }
        } catch (error) {
            hidePreloader();
            console.error('Login error:', error);
            showToast('An error occurred. Please try again.');
            
            // Reset button state
            resetButton(button, buttonText, buttonIcon);
        }
    });
}

// Helper function to reset button state
function resetButton(button, buttonText, buttonIcon) {
    button.disabled = false;
    button.classList.remove('opacity-75');
    buttonIcon.innerHTML = `
        <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
        <polyline points="10 17 15 12 10 7"></polyline>
        <line x1="15" x2="3" y1="12" y2="12"></line>
    `;
    buttonText.textContent = 'Login';
}