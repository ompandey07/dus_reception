// Global variables
let currentDate = new Date();
let allBookings = [];
let selectedDate = null;
let currentMonthNepaliData = null;

// Initialize page on load
window.addEventListener('load', function() {
    setTimeout(() => {
        document.getElementById('topBarPreloader').classList.add('hide');
    }, 500);
    
    loadMonthData();
    loadBookings();
    
    document.getElementById('creatorFilter').addEventListener('change', loadBookings);
    setupModalBackdropHandlers();
});

// Setup modal backdrop click handlers
function setupModalBackdropHandlers() {
    const modals = ['addBookingModal', 'viewBookingsModal', 'editBookingModal'];
    
    modals.forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    if (modalId === 'addBookingModal') closeAddModal();
                    else if (modalId === 'viewBookingsModal') closeViewModal();
                    else if (modalId === 'editBookingModal') closeEditModal();
                }
            });
        }
    });
}

// Get CSRF Token
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

function showPreloader() {
    const preloader = document.getElementById('topBarPreloader');
    preloader.classList.remove('hide');
    preloader.style.opacity = '1';
    preloader.style.visibility = 'visible';
}

function hidePreloader() {
    document.getElementById('topBarPreloader').classList.add('hide');
}

// Determine shift class based on shift type
function getShiftClass(shiftType) {
    switch(shiftType) {
        case 'morning':
            return 'shift-morning';
        case 'evening':
            return 'shift-evening';
        case 'fullday':
            return 'shift-fullday';
        default:
            return '';
    }
}

// Get combined shift classes for multiple bookings
function getCombinedShiftClasses(bookings) {
    if (bookings.length === 0) return '';
    if (bookings.length === 1) return getShiftClass(bookings[0].shift_type);
    
    const shiftTypes = bookings.map(b => b.shift_type);
    const hasMorning = shiftTypes.includes('morning');
    const hasEvening = shiftTypes.includes('evening');
    const hasFullday = shiftTypes.includes('fullday');
    
    if (hasFullday) {
        return 'shift-fullday';
    } else if (hasMorning && hasEvening) {
        return 'has-multiple-shifts';
    } else if (hasMorning) {
        return 'shift-morning';
    } else if (hasEvening) {
        return 'shift-evening';
    }
    
    return '';
}

// Load month data with Nepali dates from backend
async function loadMonthData() {
    try {
        showPreloader();
        
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth() + 1;
        
        const response = await fetch(`/api/calendar-data/?year=${year}&month=${month}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (response.ok) {
            const data = await response.json();
            currentMonthNepaliData = data;
            renderCalendar();
        } else {
            showToast('Failed to load calendar data', 'error');
        }
    } catch (error) {
        console.error('Error loading calendar data:', error);
        showToast('Error loading calendar data', 'error');
    } finally {
        hidePreloader();
    }
}

// Render calendar with backend Nepali dates and shift-based fill patterns
function renderCalendar() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                       'July', 'August', 'September', 'October', 'November', 'December'];
    document.getElementById('currentMonth').textContent = `${monthNames[month]} ${year}`;
    
    if (currentMonthNepaliData && currentMonthNepaliData.calendar_days.length > 0) {
        const firstDayData = currentMonthNepaliData.calendar_days[0];
        if (firstDayData.nepali_date) {
            document.getElementById('currentMonthNepali').textContent = 
                `${firstDayData.nepali_date.month_name} ${firstDayData.nepali_date.year}`;
        }
    }
    
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysInPrevMonth = new Date(year, month, 0).getDate();
    
    let calendarHTML = '';
    
    const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    weekdays.forEach(day => {
        calendarHTML += `<div class="calendar-header">${day}</div>`;
    });
    
    let dayCount = 1;
    let nextMonthDay = 1;
    const totalCells = 42;
    
    for (let i = 0; i < totalCells; i++) {
        let dayNum, cellDate, isCurrentMonth = false, isOtherMonth = false;
        
        if (i < firstDay) {
            dayNum = daysInPrevMonth - firstDay + i + 1;
            cellDate = new Date(year, month - 1, dayNum);
            isOtherMonth = true;
        } else if (dayCount <= daysInMonth) {
            dayNum = dayCount++;
            cellDate = new Date(year, month, dayNum);
            isCurrentMonth = true;
        } else {
            dayNum = nextMonthDay++;
            cellDate = new Date(year, month + 1, dayNum);
            isOtherMonth = true;
        }
        
        const today = new Date();
        const isToday = cellDate.toDateString() === today.toDateString();
        
        const localDateStr = cellDate.getFullYear() + '-' + 
                            String(cellDate.getMonth() + 1).padStart(2, '0') + '-' + 
                            String(cellDate.getDate()).padStart(2, '0');
        
        let nepaliDateDisplay = '';
        if (currentMonthNepaliData && currentMonthNepaliData.calendar_days) {
            const dayData = currentMonthNepaliData.calendar_days.find(d => d.date === localDateStr);
            if (dayData && dayData.nepali_date) {
                nepaliDateDisplay = `${dayData.nepali_date.month_name} ${dayData.nepali_date.day}`;
            }
        }
        
        const dayBookings = allBookings.filter(b => b.booking_date === localDateStr);
        const hasBooking = dayBookings.length > 0;
        const bookingCount = dayBookings.length;
        
        let classes = 'calendar-day';
        if (isOtherMonth) classes += ' other-month';
        if (isToday) classes += ' today';
        if (hasBooking) {
            classes += ' has-booking';
            // Add shift-based styling
            const shiftClass = getCombinedShiftClasses(dayBookings);
            if (shiftClass) classes += ' ' + shiftClass;
        }
        
        // Build events HTML with color indicators
        let eventsHTML = '';
        if (hasBooking) {
            dayBookings.forEach((booking, idx) => {
                if (idx < 2) {
                    const shiftLabel = getShiftLabel(booking.shift_type);
                    eventsHTML += `
                        <div class="day-event" 
                             style="border-left: 3px solid ${booking.color}; padding-left: 6px;" 
                             title="${escapeHtml(booking.client_name)} - ${booking.event_type_display} (${booking.start_time}-${booking.end_time}) ${shiftLabel}">
                            ${escapeHtml(booking.client_name)}
                        </div>
                    `;
                }
            });
            if (dayBookings.length > 2) {
                eventsHTML += `<div class="day-event-more">+${dayBookings.length - 2} more</div>`;
            }
        }
        
        calendarHTML += `
            <div class="${classes}" onclick="handleDateClick('${localDateStr}')">
                <div class="day-number">${dayNum}</div>
                <div class="day-nepali">${nepaliDateDisplay}</div>
                <div class="day-events">
                    ${eventsHTML}
                </div>
            </div>
        `;
    }
    
    const calendarGrid = document.querySelector('.calendar-grid');
    if (calendarGrid) {
        calendarGrid.innerHTML = calendarHTML;
    }
}

function getShiftLabel(shiftType) {
    switch(shiftType) {
        case 'morning':
            return '[Morning]';
        case 'evening':
            return '[Evening]';
        case 'fullday':
            return '[Full Day]';
        default:
            return '';
    }
}

function previousMonth() {
    currentDate.setMonth(currentDate.getMonth() - 1);
    loadMonthData();
    loadBookings();
}

function nextMonth() {
    currentDate.setMonth(currentDate.getMonth() + 1);
    loadMonthData();
    loadBookings();
}

async function loadBookings() {
    try {
        showPreloader();
        
        const filter = document.getElementById('creatorFilter').value;
        const url = filter ? `/api/bookings/?created_by=${filter}` : '/api/bookings/';
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (response.ok) {
            const data = await response.json();
            allBookings = data.bookings || [];
            renderCalendar();
            renderBookingsList();
        } else {
            showToast('Failed to load bookings', 'error');
        }
    } catch (error) {
        console.error('Error loading bookings:', error);
        showToast('Error loading bookings', 'error');
    } finally {
        hidePreloader();
    }
}

function renderBookingsList() {
    const container = document.getElementById('bookingsList');
    const countEl = document.getElementById('bookingCount');
    
    const sortedBookings = [...allBookings].sort((a, b) => {
        const dateA = new Date(a.booking_date + 'T' + a.start_time);
        const dateB = new Date(b.booking_date + 'T' + b.start_time);
        return dateA - dateB;
    });
    
    const today = new Date();
    const todayStr = today.getFullYear() + '-' + 
                     String(today.getMonth() + 1).padStart(2, '0') + '-' + 
                     String(today.getDate()).padStart(2, '0');
    const upcomingBookings = sortedBookings.filter(b => b.booking_date >= todayStr);
    
    countEl.textContent = upcomingBookings.length;
    
    if (upcomingBookings.length === 0) {
        container.innerHTML = '<p class="text-center text-gray-500 py-8">No upcoming bookings</p>';
        return;
    }
    
    container.innerHTML = upcomingBookings.slice(0, 10).map(booking => `
        <div class="booking-card" style="border-left: 4px solid ${booking.color}">
            <div class="booking-card-header">
                <div class="booking-client">${escapeHtml(booking.client_name)}</div>
                <div class="booking-time" style="color: ${booking.color}">${booking.start_time} - ${booking.end_time}</div>
            </div>
            <div class="booking-detail">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect width="18" height="18" x="3" y="4" rx="2" ry="2"></rect>
                    <line x1="16" x2="16" y1="2" y2="6"></line>
                    <line x1="8" x2="8" y1="2" y2="6"></line>
                    <line x1="3" x2="21" y1="10" y2="10"></line>
                </svg>
                ${formatDate(booking.booking_date)} ${getShiftLabel(booking.shift_type)}
            </div>
            <div class="booking-detail">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                    <circle cx="12" cy="10" r="3"></circle>
                </svg>
                ${escapeHtml(booking.event_type_display)}
            </div>
            <div class="booking-detail">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                </svg>
                Advance: Rs. ${booking.advance_given}
            </div>
            <div class="booking-detail">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                </svg>
                ${escapeHtml(booking.created_by)}
            </div>
            <div class="booking-actions">
                <button onclick="viewBookingDetail(${booking.id})" class="btn-view">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                    View
                </button>
                <button onclick="editBooking(${booking.id})" class="btn-edit">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"></path>
                    </svg>
                    Edit
                </button>
                <button onclick="deleteBooking(${booking.id}, '${escapeHtml(booking.client_name)}')" class="btn-delete">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 6h18"></path>
                        <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                        <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                    </svg>
                    Delete
                </button>
            </div>
        </div>
    `).join('');
}

async function viewBookingDetail(bookingId) {
    try {
        showPreloader();
        
        const response = await fetch(`/api/bookings/${bookingId}/detail/`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (response.ok) {
            const data = await response.json();
            const booking = data.booking;
            selectedDate = booking.booking_date;
            const dayBookings = allBookings.filter(b => b.booking_date === selectedDate);
            const bookingCount = dayBookings.length;
            openDetailModal(booking);
            document.getElementById('addInViewButton').style.display = (bookingCount < 2) ? 'block' : 'none';
        } else {
            showToast('Failed to load booking details', 'error');
        }
    } catch (error) {
        console.error('Error loading booking detail:', error);
        showToast('Error loading booking details', 'error');
    } finally {
        hidePreloader();
    }
}

function openDetailModal(booking) {
    const modal = document.getElementById('viewBookingsModal');
    const modalContent = modal.querySelector('.modal-content');
    
    document.getElementById('selectedDateDisplay').textContent = `${booking.booking_date_formatted} (${booking.booking_date_nepali})`;
    
    const container = document.getElementById('dateBookingsList');
    const shiftLabel = getShiftLabel(booking.shift_type);
    
    container.innerHTML = `
        <div class="bg-gradient-to-br from-purple-50 to-indigo-50 p-6 border-l-4" style="border-color: ${booking.color}">
            <div class="flex justify-between items-start mb-6">
                <div>
                    <h4 class="font-bold text-2xl text-gray-800 mb-2">${escapeHtml(booking.client_name)}</h4>
                    <p class="text-base font-semibold" style="color: ${booking.color}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        ${booking.start_time} - ${booking.end_time} ${shiftLabel}
                    </p>
                </div>
            </div>
            
            <div class="detail-grid">
                <div class="detail-item">
                    <p class="detail-label">English Date</p>
                    <p class="detail-value">${booking.booking_date_formatted}</p>
                </div>
                <div class="detail-item">
                    <p class="detail-label">Nepali Date</p>
                    <p class="detail-value nepali">${booking.booking_date_nepali}</p>
                </div>
                <div class="detail-item">
                    <p class="detail-label">Event Type</p>
                    <p class="detail-value">${escapeHtml(booking.event_type_display)}</p>
                </div>
                <div class="detail-item">
                    <p class="detail-label">Phone Number</p>
                    <p class="detail-value">${escapeHtml(booking.phone_number)}</p>
                </div>
                ${booking.email ? `
                <div class="detail-item">
                    <p class="detail-label">Email</p>
                    <p class="detail-value">${escapeHtml(booking.email)}</p>
                </div>
                ` : ''}
                ${booking.menu_type ? `
                <div class="detail-item">
                    <p class="detail-label">Menu Type</p>
                    <p class="detail-value">${escapeHtml(booking.menu_type)}</p>
                </div>
                ` : ''}
                ${booking.no_of_packs ? `
                <div class="detail-item">
                    <p class="detail-label">No. of Packs</p>
                    <p class="detail-value">${escapeHtml(booking.no_of_packs)}</p>
                </div>
                ` : ''}
                <div class="detail-item">
                    <p class="detail-label">Advance Given</p>
                    <p class="detail-value font-bold">Rs. ${booking.advance_given}</p>
                </div>
                <div class="detail-item sm:col-span-2">
                    <p class="detail-label">Created By</p>
                    <p class="detail-value">${escapeHtml(booking.created_by)}</p>
                </div>
                <div class="detail-item sm:col-span-2">
                    <p class="detail-label">Created At</p>
                    <p class="detail-value">${booking.created_at}</p>
                </div>
            </div>
            
            <div class="flex gap-3 mt-6">
                <button onclick="closeViewModal(); editBooking(${booking.id})" class="btn-edit flex-1">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"></path>
                    </svg>
                    Edit Booking
                </button>
                <button onclick="deleteBooking(${booking.id}, '${escapeHtml(booking.client_name)}')" class="btn-delete flex-1">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 6h18"></path>
                        <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                        <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                    </svg>
                    Delete Booking
                </button>
            </div>
        </div>
    `;
    
    modal.classList.remove('hidden', 'closing');
    modal.classList.add('flex');
    modalContent.classList.remove('closing');
    setTimeout(() => {
        modal.style.display = 'flex';
    }, 10);
}

function handleDateClick(dateStr) {
    selectedDate = dateStr;
    const bookings = allBookings.filter(b => b.booking_date === dateStr);
    
    if (bookings.length === 0) {
        openAddModal(dateStr);
    } else if (bookings.length === 1) {
        viewBookingDetail(bookings[0].id);
    } else {
        openDateBookingsModal(dateStr, bookings);
    }
}

function openDateBookingsModal(dateStr, bookings) {
    const modal = document.getElementById('viewBookingsModal');
    const modalContent = modal.querySelector('.modal-content');
    
    document.getElementById('selectedDateDisplay').textContent = `${formatDate(dateStr)} - ${bookings.length} Bookings`;
    
    const container = document.getElementById('dateBookingsList');
    container.innerHTML = bookings.map(booking => {
        const shiftLabel = getShiftLabel(booking.shift_type);
        return `
        <div class="bg-gray-50 p-4 border-l-4" style="border-color: ${booking.color}">
            <div class="flex justify-between items-start mb-3">
                <div>
                    <h4 class="font-bold text-lg text-gray-800">${escapeHtml(booking.client_name)}</h4>
                    <p class="text-sm font-semibold" style="color: ${booking.color}">${booking.start_time} - ${booking.end_time} ${shiftLabel}</p>
                </div>
            </div>
            
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                <div>
                    <p class="text-gray-600">Event Type:</p>
                    <p class="font-semibold text-gray-800">${escapeHtml(booking.event_type_display)}</p>
                </div>
                <div>
                    <p class="text-gray-600">Phone:</p>
                    <p class="font-semibold text-gray-800">${escapeHtml(booking.phone_number)}</p>
                </div>
                ${booking.email ? `
                <div>
                    <p class="text-gray-600">Email:</p>
                    <p class="font-semibold text-gray-800">${escapeHtml(booking.email)}</p>
                </div>
                ` : ''}
                ${booking.menu_type ? `
                <div>
                    <p class="text-gray-600">Menu Type:</p>
                    <p class="font-semibold text-gray-800">${escapeHtml(booking.menu_type)}</p>
                </div>
                ` : ''}
                ${booking.no_of_packs ? `
                <div>
                    <p class="text-gray-600">No. of Packs:</p>
                    <p class="font-semibold text-gray-800">${escapeHtml(booking.no_of_packs)}</p>
                </div>
                ` : ''}
                <div>
                    <p class="text-gray-600">Advance Given:</p>
                    <p class="font-semibold text-gray-800">Rs. ${booking.advance_given}</p>
                </div>
                <div class="sm:col-span-2">
                    <p class="text-gray-600">Created By:</p>
                    <p class="font-semibold text-gray-800">${escapeHtml(booking.created_by)}</p>
                </div>
            </div>
            
            <div class="flex gap-2 mt-4">
                <button onclick="viewBookingDetail(${booking.id})" class="btn-view">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                    View
                </button>
                <button onclick="editBooking(${booking.id})" class="btn-edit">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"></path>
                    </svg>
                    Edit
                </button>
                <button onclick="deleteBooking(${booking.id}, '${escapeHtml(booking.client_name)}')" class="btn-delete">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 6h18"></path>
                        <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                        <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                    </svg>
                    Delete
                </button>
            </div>
        </div>
    `;}).join('');
    
    document.getElementById('addInViewButton').style.display = (bookings.length < 2) ? 'block' : 'none';
    
    modal.classList.remove('hidden', 'closing');
    modal.classList.add('flex');
    modalContent.classList.remove('closing');
    setTimeout(() => {
        modal.style.display = 'flex';
    }, 10);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function openAddModal(dateStr = null) {
    closeViewModal();
    closeEditModal();

    const modal = document.getElementById('addBookingModal');
    const modalContent = modal.querySelector('.modal-content');
    
    const now = new Date();
    const today = now.getFullYear() + '-' + 
                  String(now.getMonth() + 1).padStart(2, '0') + '-' + 
                  String(now.getDate()).padStart(2, '0');
    const currentTime = String(now.getHours()).padStart(2, '0') + ':' + 
                        String(now.getMinutes()).padStart(2, '0');
    
    document.getElementById('bookingDate').value = dateStr || today;
    document.getElementById('startTime').value = currentTime;
    
    const endTime = new Date(now.getTime() + 60 * 60 * 1000);
    document.getElementById('endTime').value = String(endTime.getHours()).padStart(2, '0') + ':' + 
                                               String(endTime.getMinutes()).padStart(2, '0');
    
    // Reset advance given field
    document.getElementById('advanceGiven').value = '';
    
    modal.classList.remove('hidden', 'closing');
    modal.classList.add('flex');
    modalContent.classList.remove('closing');
    setTimeout(() => {
        modal.style.display = 'flex';
    }, 10);
}

function closeAddModal() {
    const modal = document.getElementById('addBookingModal');
    const modalContent = modal.querySelector('.modal-content');
    
    modal.classList.add('closing');
    modalContent.classList.add('closing');
    
    setTimeout(() => {
        modal.classList.add('hidden');
        modal.classList.remove('flex', 'closing');
        modal.style.display = 'none';
        modalContent.classList.remove('closing');
        document.getElementById('addBookingForm').reset();
    }, 200);
}

function closeViewModal() {
    const modal = document.getElementById('viewBookingsModal');
    const modalContent = modal.querySelector('.modal-content');
    
    modal.classList.add('closing');
    modalContent.classList.add('closing');
    
    setTimeout(() => {
        modal.classList.add('hidden');
        modal.classList.remove('flex', 'closing');
        modal.style.display = 'none';
        modalContent.classList.remove('closing');
    }, 200);
}

function closeEditModal() {
    const modal = document.getElementById('editBookingModal');
    const modalContent = modal.querySelector('.modal-content');
    
    modal.classList.add('closing');
    modalContent.classList.add('closing');
    
    setTimeout(() => {
        modal.classList.add('hidden');
        modal.classList.remove('flex', 'closing');
        modal.style.display = 'none';
        modalContent.classList.remove('closing');
        document.getElementById('editBookingForm').reset();
    }, 200);
}

async function editBooking(bookingId) {
    const booking = allBookings.find(b => b.id === bookingId);
    if (!booking) return;
    
    selectedDate = booking.booking_date;
    closeViewModal();
    
    setTimeout(() => {
        document.getElementById('editBookingId').value = booking.id;
        document.getElementById('editClientName').value = booking.client_name;
        document.getElementById('editBookingDate').value = booking.booking_date;
        document.getElementById('editStartTime').value = booking.start_time;
        document.getElementById('editEndTime').value = booking.end_time;
        document.getElementById('editPhoneNumber').value = booking.phone_number;
        document.getElementById('editEmail').value = booking.email || '';
        document.getElementById('editEventType').value = booking.event_type;
        document.getElementById('editMenuType').value = booking.menu_type || '';
        document.getElementById('editNoOfPacks').value = booking.no_of_packs || '';
        document.getElementById('editAdvanceGiven').value = booking.advance_given;
        
        const modal = document.getElementById('editBookingModal');
        const modalContent = modal.querySelector('.modal-content');
        
        modal.classList.remove('hidden', 'closing');
        modal.classList.add('flex');
        modalContent.classList.remove('closing');
        setTimeout(() => {
            modal.style.display = 'flex';
        }, 10);
    }, 250);
}

async function deleteBooking(bookingId, clientName) {
    if (!confirm(`Are you sure you want to delete booking for "${clientName}"?`)) {
        return;
    }

    try {
        showPreloader();
        const response = await fetch(`/api/bookings/${bookingId}/delete/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (response.ok) {
            showToast('Booking deleted successfully', 'success');
            closeViewModal();
            loadBookings();
        } else {
            const data = await response.json();
            showToast(data.error || 'Failed to delete booking', 'error');
        }
    } catch (error) {
        console.error('Error deleting booking:', error);
        showToast('Error deleting booking', 'error');
    } finally {
        hidePreloader();
    }
}

document.getElementById('addBookingForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    
    const clientName = document.getElementById('clientName').value.trim();
    const bookingDate = document.getElementById('bookingDate').value;
    const startTime = document.getElementById('startTime').value;
    const endTime = document.getElementById('endTime').value;
    const phoneNumber = document.getElementById('phoneNumber').value.trim();
    const email = document.getElementById('email').value.trim();
    const eventType = document.getElementById('eventType').value;
    const menuType = document.getElementById('menuType').value.trim();
    const noOfPacks = document.getElementById('noOfPacks').value.trim();
    const advanceGiven = document.getElementById('advanceGiven').value;
    
    if (!clientName || !bookingDate || !startTime || !endTime || !phoneNumber || !eventType) {
        showToast('Please fill all required fields', 'error');
        return;
    }
    
    // Validate advance given is not empty and is a valid number
    if (!advanceGiven || advanceGiven === '' || isNaN(parseFloat(advanceGiven))) {
        showToast('Please enter a valid advance amount', 'error');
        document.getElementById('advanceGiven').focus();
        return;
    }
    
    if (parseFloat(advanceGiven) < 0) {
        showToast('Advance amount cannot be negative', 'error');
        document.getElementById('advanceGiven').focus();
        return;
    }
    
    if (endTime <= startTime) {
        showToast('End time must be after start time', 'error');
        return;
    }
    
    const button = event.target.querySelector('button[type="submit"]');
    const buttonText = document.getElementById('addButtonText');
    const buttonIcon = document.getElementById('addButtonIcon');
    
    showPreloader();
    button.disabled = true;
    button.classList.add('opacity-75');
    buttonIcon.innerHTML = `<div class="spinner-dots"><div class="spinner-dot"></div><div class="spinner-dot"></div><div class="spinner-dot"></div></div>`;
    buttonText.textContent = 'Creating...';
    
    try {
        const response = await fetch('/api/bookings/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                client_name: clientName,
                booking_date: bookingDate,
                start_time: startTime,
                end_time: endTime,
                phone_number: phoneNumber,
                email: email,
                event_type: eventType,
                menu_type: menuType,
                no_of_packs: noOfPacks,
                advance_given: advanceGiven
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            hidePreloader();
            showToast('Booking created successfully!', 'success');
            closeAddModal();
            loadBookings();
        } else {
            hidePreloader();
            showToast(data.error || 'Failed to create booking', 'error');
        }
    } catch (error) {
        hidePreloader();
        console.error('Error:', error);
        showToast('An error occurred. Please try again.', 'error');
    } finally {
        button.disabled = false;
        button.classList.remove('opacity-75');
        buttonIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle><line x1="19" x2="19" y1="8" y2="14"></line><line x1="22" x2="16" y1="11" y2="11"></line></svg>`;
        buttonText.textContent = 'Create Booking';
    }
});

document.getElementById('editBookingForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    
    const bookingId = document.getElementById('editBookingId').value;
    const clientName = document.getElementById('editClientName').value.trim();
    const bookingDate = document.getElementById('editBookingDate').value;
    const startTime = document.getElementById('editStartTime').value;
    const endTime = document.getElementById('editEndTime').value;
    const phoneNumber = document.getElementById('editPhoneNumber').value.trim();
    const email = document.getElementById('editEmail').value.trim();
    const eventType = document.getElementById('editEventType').value;
    const menuType = document.getElementById('editMenuType').value.trim();
    const noOfPacks = document.getElementById('editNoOfPacks').value.trim();
    const advanceGiven = document.getElementById('editAdvanceGiven').value;
    
    if (!clientName || !bookingDate || !startTime || !endTime || !phoneNumber || !eventType) {
        showToast('Please fill all required fields', 'error');
        return;
    }
    
    // Validate advance given
    if (!advanceGiven || advanceGiven === '' || isNaN(parseFloat(advanceGiven))) {
        showToast('Please enter a valid advance amount', 'error');
        document.getElementById('editAdvanceGiven').focus();
        return;
    }
    
    if (parseFloat(advanceGiven) < 0) {
        showToast('Advance amount cannot be negative', 'error');
        document.getElementById('editAdvanceGiven').focus();
        return;
    }
    
    if (endTime <= startTime) {
        showToast('End time must be after start time', 'error');
        return;
    }
    
    const button = event.target.querySelector('button[type="submit"]');
    const buttonText = document.getElementById('editButtonText');
    const buttonIcon = document.getElementById('editButtonIcon');
    
    showPreloader();
    button.disabled = true;
    button.classList.add('opacity-75');
    buttonIcon.innerHTML = `<div class="spinner-dots"><div class="spinner-dot"></div><div class="spinner-dot"></div><div class="spinner-dot"></div></div>`;
    buttonText.textContent = 'Updating...';
    
    try {
        const response = await fetch(`/api/bookings/${bookingId}/update/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                client_name: clientName,
                booking_date: bookingDate,
                start_time: startTime,
                end_time: endTime,
                phone_number: phoneNumber,
                email: email,
                event_type: eventType,
                menu_type: menuType,
                no_of_packs: noOfPacks,
                advance_given: advanceGiven
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            hidePreloader();
            showToast('Booking updated successfully!', 'success');
            closeEditModal();
            loadBookings();
        } else {
            hidePreloader();
            showToast(data.error || 'Failed to update booking', 'error');
        }
    } catch (error) {
        hidePreloader();
        console.error('Error:', error);
        showToast('An error occurred. Please try again.', 'error');
    } finally {
        button.disabled = false;
        button.classList.remove('opacity-75');
        buttonIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>`;
        buttonText.textContent = 'Update Booking';
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const floatingBtn = document.createElement('div');
    floatingBtn.className = 'add-booking-btn';
    floatingBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" x2="12" y1="5" y2="19"></line>
            <line x1="5" x2="19" y1="12" y2="12"></line>
        </svg>
    `;
    floatingBtn.onclick = () => openAddModal();
    document.body.appendChild(floatingBtn);
});