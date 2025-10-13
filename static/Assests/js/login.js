// Hide preloader on page load
window.addEventListener('load', function() {
    setTimeout(() => {
        const preloader = document.getElementById('topBarPreloader');
        preloader.classList.add('hide');
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
function showToast(message) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = 'toast relative bg-white border-l-4 border-red-500 p-4 shadow-lg min-w-[300px]';
    
    toast.innerHTML = `
        <div class="flex items-start gap-3">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" x2="12" y1="8" y2="12"></line>
                <line x1="12" x2="12.01" y1="16" y2="16"></line>
            </svg>
            <div class="flex-1">
                <p class="font-semibold text-gray-800">Error</p>
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
    preloader.classList.remove('hide');
    preloader.style.opacity = '1';
    preloader.style.visibility = 'visible';
}

// Hide preloader
function hidePreloader() {
    const preloader = document.getElementById('topBarPreloader');
    preloader.classList.add('hide');
}

// Initialize login form handler
function initLoginForm(userType, loginUrl, dashboardUrl) {
    document.getElementById('loginForm').addEventListener('submit', async function(event) {
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
            
            if (response.ok) {
                window.location.href = dashboardUrl;
            } else {
                hidePreloader();
                
                // Extract error message
                let errorMessage = 'Invalid email or password';
                if (data.email) {
                    errorMessage = data.email[0];
                } else if (data.password) {
                    errorMessage = data.password[0];
                } else if (data.non_field_errors) {
                    errorMessage = data.non_field_errors[0];
                } else if (data.detail) {
                    errorMessage = data.detail;
                }
                
                showToast(errorMessage);
                
                // Reset button state
                button.disabled = false;
                button.classList.remove('opacity-75');
                buttonIcon.innerHTML = `
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
                    <polyline points="10 17 15 12 10 7"></polyline>
                    <line x1="15" x2="3" y1="12" y2="12"></line>
                `;
                buttonText.textContent = 'Login';
            }
        } catch (error) {
            hidePreloader();
            showToast('An error occurred. Please try again.');
            
            // Reset button state
            button.disabled = false;
            button.classList.remove('opacity-75');
            buttonIcon.innerHTML = `
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
                <polyline points="10 17 15 12 10 7"></polyline>
                <line x1="15" x2="3" y1="12" y2="12"></line>
            `;
            buttonText.textContent = 'Login';
        }
    });
}