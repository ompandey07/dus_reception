// Initialize page on load
window.addEventListener('load', function() {
    setTimeout(() => {
        document.getElementById('topBarPreloader').classList.add('hide');
    }, 500);
    loadUsers();
});

// Get CSRF Token from cookies
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
    
    const config = {
        success: { 
            icon: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>', 
            color: '#10b981', 
            bg: 'bg-green-50' 
        },
        error: { 
            icon: '<circle cx="12" cy="12" r="10"></circle><line x1="12" x2="12" y1="8" y2="12"></line><line x1="12" x2="12.01" y1="16" y2="16"></line>', 
            color: '#ef4444', 
            bg: 'bg-red-50' 
        }
    };
    
    const typeConfig = config[type] || config.error;
    
    toast.className = `toast ${type} relative ${typeConfig.bg} p-3 sm:p-4 shadow-lg min-w-[280px] sm:min-w-[320px]`;
    
    toast.innerHTML = `
        <div class="flex items-start gap-2 sm:gap-3">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="${typeConfig.color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0 mt-0.5">
                ${typeConfig.icon}
            </svg>
            <div class="flex-1">
                <p class="font-bold text-gray-800 capitalize text-sm">${type}</p>
                <p class="text-xs sm:text-sm text-gray-700 mt-0.5">${message}</p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="text-gray-400 hover:text-gray-600 transition-colors ml-2">
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
    document.getElementById('topBarPreloader').classList.add('hide');
}

// Load users from API
async function loadUsers() {
    try {
        showPreloader();
        const response = await fetch('/auth/api/users/', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (response.ok) {
            const data = await response.json();
            renderUsers(data.users || data || []);
        } else {
            showToast('Failed to load users', 'error');
        }
    } catch (error) {
        console.error('Error loading users:', error);
        showToast('Error loading users', 'error');
    } finally {
        hidePreloader();
    }
}

// Render users in table
function renderUsers(users) {
    const tbody = document.getElementById('userTableBody');
    
    if (!users || users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-12 text-center text-gray-500">
                    <p class="font-semibold text-sm sm:text-base">No users registered yet</p>
                    <p class="text-xs sm:text-sm mt-1">Register a new user to get started</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = users.map(user => `
        <tr class="table-row">
            <td class="px-3 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-gray-800 font-semibold">#${user.id}</td>
            <td class="px-3 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-gray-800">${escapeHtml(user.full_name)}</td>
            <td class="px-3 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-gray-600">${user.created_by ? escapeHtml(user.created_by) : 'System'}</td>
            <td class="px-3 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-gray-600">${formatDate(user.created_at)}</td>
            <td class="px-3 sm:px-6 py-3 sm:py-4">
                <div class="flex items-center justify-center gap-2 flex-wrap">
                    <button 
                        onclick='openEditModal(${user.id}, "${escapeHtml(user.full_name)}", "${escapeHtml(user.login_email)}")'
                        class="action-btn px-2 sm:px-3 py-1.5 sm:py-2 bg-blue-500 text-white text-xs font-semibold hover:bg-blue-600 transition-all flex items-center gap-1"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"></path>
                        </svg>
                        Edit
                    </button>
                    <button 
                        onclick='deleteUser(${user.id}, "${escapeHtml(user.full_name)}")'
                        class="action-btn px-2 sm:px-3 py-1.5 sm:py-2 bg-red-500 text-white text-xs font-semibold hover:bg-red-600 transition-all flex items-center gap-1"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 6h18"></path>
                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                        </svg>
                        Delete
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format date string
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Open edit modal
function openEditModal(id, name, email) {
    document.getElementById('editUserId').value = id;
    document.getElementById('editFullName').value = name;
    document.getElementById('editEmail').value = email;
    document.getElementById('editPassword').value = '';
    
    const modal = document.getElementById('editModal');
    const modalContent = modal.querySelector('.modal-content');
    
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    modal.classList.remove('closing');
    modalContent.classList.remove('closing');
}

// Close edit modal
function closeEditModal() {
    const modal = document.getElementById('editModal');
    const modalContent = modal.querySelector('.modal-content');
    
    modal.classList.add('closing');
    modalContent.classList.add('closing');
    
    setTimeout(() => {
        modal.classList.add('hidden');
        modal.classList.remove('flex', 'closing');
        modalContent.classList.remove('closing');
        document.getElementById('editForm').reset();
    }, 200);
}

// Delete user
async function deleteUser(id, name) {
    if (!confirm(`Are you sure you want to delete "${name}"?`)) {
        return;
    }

    try {
        showPreloader();
        const response = await fetch(`/auth/api/users/${id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (response.ok) {
            showToast('User deleted successfully', 'success');
            loadUsers();
        } else {
            const data = await response.json();
            showToast(data.error || 'Failed to delete user', 'error');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        showToast('Error deleting user', 'error');
    } finally {
        hidePreloader();
    }
}

// Register form submit handler
document.getElementById('registerForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    
    const fullName = document.getElementById('fullNameInput').value.trim();
    const email = document.getElementById('emailInput').value.trim();
    const password = document.getElementById('passwordInput').value.trim();
    const confirmPassword = document.getElementById('confirmPasswordInput').value.trim();
    
    if (!fullName || !email || !password) {
        showToast('All fields are required', 'error');
        return;
    }
    
    if (password.length < 6) {
        showToast('Password must be at least 6 characters', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showToast('Passwords do not match', 'error');
        return;
    }
    
    const button = document.getElementById('registerButton');
    const buttonText = document.getElementById('buttonText');
    const buttonIcon = document.getElementById('buttonIcon');
    
    showPreloader();
    button.disabled = true;
    button.classList.add('opacity-75');
    buttonIcon.innerHTML = `<div class="spinner-dots"><div class="spinner-dot"></div><div class="spinner-dot"></div><div class="spinner-dot"></div></div>`;
    buttonText.textContent = 'Registering...';
    
    try {
        const response = await fetch("/auth/register/", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                full_name: fullName,
                login_email: email,
                password: password,
                confirm_password: confirmPassword
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            hidePreloader();
            showToast('User registered successfully!', 'success');
            document.getElementById('registerForm').reset();
            loadUsers();
        } else {
            hidePreloader();
            let errorMessage = 'Registration failed. Please try again.';
            if (data.full_name) errorMessage = Array.isArray(data.full_name) ? data.full_name[0] : data.full_name;
            else if (data.login_email) errorMessage = Array.isArray(data.login_email) ? data.login_email[0] : data.login_email;
            else if (data.password) errorMessage = Array.isArray(data.password) ? data.password[0] : data.password;
            else if (data.error) errorMessage = data.error;
            else if (data.detail) errorMessage = data.detail;
            showToast(errorMessage, 'error');
        }
    } catch (error) {
        hidePreloader();
        console.error('Error:', error);
        showToast('An error occurred. Please try again.', 'error');
    } finally {
        button.disabled = false;
        button.classList.remove('opacity-75');
        buttonIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><line x1="19" x2="19" y1="8" y2="14"></line><line x1="22" x2="16" y1="11" y2="11"></line></svg>`;
        buttonText.textContent = 'Register User';
    }
});

// Edit form submit handler
document.getElementById('editForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    
    const userId = document.getElementById('editUserId').value;
    const fullName = document.getElementById('editFullName').value.trim();
    const email = document.getElementById('editEmail').value.trim();
    const password = document.getElementById('editPassword').value.trim();
    
    if (!fullName || !email) {
        showToast('Full name and email are required', 'error');
        return;
    }

    if (password && password.length < 6) {
        showToast('Password must be at least 6 characters', 'error');
        return;
    }
    
    const button = document.getElementById('updateButton');
    const buttonText = document.getElementById('updateButtonText');
    const buttonIcon = document.getElementById('updateButtonIcon');
    
    showPreloader();
    button.disabled = true;
    button.classList.add('opacity-75');
    buttonIcon.innerHTML = `<div class="spinner-dots"><div class="spinner-dot"></div><div class="spinner-dot"></div><div class="spinner-dot"></div></div>`;
    buttonText.textContent = 'Updating...';
    
    try {
        const updateData = {
            full_name: fullName,
            login_email: email
        };
        
        if (password) {
            updateData.password = password;
        }

        const response = await fetch(`/auth/api/users/${userId}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(updateData)
        });

        const data = await response.json();
        
        if (response.ok) {
            hidePreloader();
            showToast('User updated successfully!', 'success');
            closeEditModal();
            loadUsers();
        } else {
            hidePreloader();
            let errorMessage = 'Update failed. Please try again.';
            if (data.full_name) errorMessage = Array.isArray(data.full_name) ? data.full_name[0] : data.full_name;
            else if (data.login_email) errorMessage = Array.isArray(data.login_email) ? data.login_email[0] : data.login_email;
            else if (data.password) errorMessage = Array.isArray(data.password) ? data.password[0] : data.password;
            else if (data.error) errorMessage = data.error;
            else if (data.detail) errorMessage = data.detail;
            showToast(errorMessage, 'error');
        }
    } catch (error) {
        hidePreloader();
        console.error('Error:', error);
        showToast('An error occurred. Please try again.', 'error');
    } finally {
        button.disabled = false;
        button.classList.remove('opacity-75');
        buttonIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>`;
        buttonText.textContent = 'Update User';
    }
});