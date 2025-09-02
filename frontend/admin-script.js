// Sistema de Toast Notifications
const Toast = {
    init() {
        this.toastContainer = document.getElementById('toast-container');
    },
    show(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const iconMap = { 
            success: 'fa-check-circle', 
            error: 'fa-times-circle', 
            warning: 'fa-exclamation-circle', 
            info: 'fa-info-circle' 
        };
        toast.innerHTML = `
            <i class="fas ${iconMap[type] || 'fa-info-circle'} toast-icon"></i>
            <span>${message}</span>
        `;
        this.toastContainer.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Remove toast
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
};

// Sistema de Loading
const Loading = {
    show(message = 'Carregando...') {
        const overlay = document.getElementById('loading-overlay');
        const messageEl = overlay.querySelector('.loading-message');
        messageEl.textContent = message;
        overlay.classList.remove('hidden');
    },
    hide() {
        const overlay = document.getElementById('loading-overlay');
        overlay.classList.add('hidden');
    }
};

// Sistema de Modal
const Modal = {
    show(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    },
    hide(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = '';
        }
    }
};

// Função para requisições à API
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Erro na requisição');
        }
        
        return data;
    } catch (error) {
        console.error('Erro na API:', error);
        throw error;
    }
}

// Estado da aplicação
let isAdminAuthenticated = false;
let selectedResellers = new Set();
let currentResellers = [];

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    Toast.init();
    initializeEventListeners();
    checkAuthStatus();
});

function initializeEventListeners() {
    // Login form
    const loginForm = document.getElementById('admin-login-form');
    loginForm.addEventListener('submit', handleAdminLogin);
    
    // Logout button
    const logoutBtn = document.getElementById('admin-logout');
    logoutBtn.addEventListener('click', handleLogout);
    
    // Tab navigation
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Refresh buttons
    document.getElementById('refresh-resellers').addEventListener('click', loadResellers);
    document.getElementById('refresh-logs').addEventListener('click', loadActivityLogs);
    
    // Select all checkbox
    document.getElementById('select-all-resellers').addEventListener('change', handleSelectAll);
    
    // Block selected button
    document.getElementById('block-selected').addEventListener('click', handleBlockSelected);
    
    // Modal close buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal');
            if (modal) {
                Modal.hide(modal.id);
            }
        });
    });
    
    // Block confirmation
    document.getElementById('confirm-block').addEventListener('click', confirmBlock);
    document.getElementById('confirm-unblock').addEventListener('click', confirmUnblock);
    
    // Logs limit change
    document.getElementById('logs-limit').addEventListener('change', loadActivityLogs);
}

function checkAuthStatus() {
    // Por simplicidade, sempre mostrar login primeiro
    showLoginSection();
}

function showLoginSection() {
    document.getElementById('login-section').classList.remove('hidden');
    document.getElementById('admin-panel').classList.add('hidden');
    isAdminAuthenticated = false;
}

function showAdminPanel() {
    document.getElementById('login-section').classList.add('hidden');
    document.getElementById('admin-panel').classList.remove('hidden');
    isAdminAuthenticated = true;
    
    // Carregar dados iniciais
    loadDashboardData();
}

async function handleAdminLogin(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const credentials = {
        username: formData.get('username'),
        password: formData.get('password')
    };
    
    Loading.show('Autenticando...');
    
    try {
        const response = await apiRequest('/api/admin/login', {
            method: 'POST',
            body: JSON.stringify(credentials)
        });
        
        if (response.success) {
            Toast.show('Login administrativo realizado com sucesso!', 'success');
            showAdminPanel();
        }
    } catch (error) {
        Toast.show(error.message, 'error');
    } finally {
        Loading.hide();
    }
}

function handleLogout() {
    isAdminAuthenticated = false;
    selectedResellers.clear();
    currentResellers = [];
    showLoginSection();
    Toast.show('Logout realizado com sucesso', 'info');
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
    
    // Load data for active tab
    if (tabName === 'resellers') {
        loadResellers();
    } else if (tabName === 'logs') {
        loadActivityLogs();
    }
}

async function loadDashboardData() {
    await Promise.all([
        loadStats(),
        loadResellers()
    ]);
}

async function loadStats() {
    try {
        const response = await apiRequest('/api/admin/stats');
        
        if (response.success) {
            const stats = response.stats;
            document.getElementById('total-resellers').textContent = stats.total_resellers;
            document.getElementById('active-resellers').textContent = stats.active_resellers;
            document.getElementById('blocked-resellers').textContent = stats.blocked_resellers;
            document.getElementById('active-sessions').textContent = stats.active_sessions;
            document.getElementById('total-clients').textContent = stats.total_clients;
        }
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
    }
}

async function loadResellers() {
    Loading.show('Carregando revendedores...');
    
    try {
        const response = await apiRequest('/api/admin/resellers');
        
        if (response.success) {
            currentResellers = response.resellers;
            displayResellers(currentResellers);
            updateBlockButtonState();
        }
    } catch (error) {
        Toast.show('Erro ao carregar revendedores: ' + error.message, 'error');
    } finally {
        Loading.hide();
    }
}

function displayResellers(resellers) {
    const tbody = document.getElementById('resellers-tbody');
    tbody.innerHTML = '';
    
    resellers.forEach(reseller => {
        const row = document.createElement('tr');
        
        // Status
        let statusBadge = '';
        if (reseller.is_blocked) {
            statusBadge = '<span class="status-badge status-blocked">Bloqueado</span>';
        } else if (reseller.is_online) {
            statusBadge = '<span class="status-badge status-online">Online</span>';
        } else {
            statusBadge = '<span class="status-badge status-offline">Offline</span>';
        }
        
        // Formatear datas
        const createdAt = new Date(reseller.created_at).toLocaleDateString('pt-BR');
        const lastActivity = reseller.last_activity ? 
            new Date(reseller.last_activity).toLocaleString('pt-BR') : 'Nunca';
        
        row.innerHTML = `
            <td>
                <input type="checkbox" class="reseller-checkbox" value="${reseller.id}" 
                       ${reseller.is_blocked ? 'disabled' : ''}>
            </td>
            <td>${statusBadge}</td>
            <td>${reseller.username}</td>
            <td>${reseller.netplay_username}</td>
            <td>${reseller.total_clients}</td>
            <td>${reseller.active_sessions}</td>
            <td>${lastActivity}</td>
            <td>${createdAt}</td>
            <td>
                <button class="action-btn view" onclick="viewResellerDetails(${reseller.id})">
                    <i class="fas fa-eye"></i>
                </button>
                ${reseller.is_blocked ? 
                    `<button class="action-btn unblock" onclick="showUnblockModal(${reseller.id})">
                        <i class="fas fa-check-circle"></i>
                    </button>` :
                    `<button class="action-btn block" onclick="showBlockModal([${reseller.id}])">
                        <i class="fas fa-ban"></i>
                    </button>`
                }
            </td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Add event listeners to checkboxes
    document.querySelectorAll('.reseller-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectedResellers);
    });
}

function handleSelectAll(e) {
    const checkboxes = document.querySelectorAll('.reseller-checkbox:not(:disabled)');
    checkboxes.forEach(checkbox => {
        checkbox.checked = e.target.checked;
    });
    updateSelectedResellers();
}

function updateSelectedResellers() {
    selectedResellers.clear();
    document.querySelectorAll('.reseller-checkbox:checked').forEach(checkbox => {
        selectedResellers.add(parseInt(checkbox.value));
    });
    updateBlockButtonState();
}

function updateBlockButtonState() {
    const blockBtn = document.getElementById('block-selected');
    blockBtn.disabled = selectedResellers.size === 0;
    blockBtn.textContent = selectedResellers.size > 0 ? 
        `Bloquear Selecionados (${selectedResellers.size})` : 'Bloquear Selecionados';
}

function handleBlockSelected() {
    if (selectedResellers.size > 0) {
        showBlockModal(Array.from(selectedResellers));
    }
}

function showBlockModal(resellerIds) {
    const modal = document.getElementById('block-modal');
    const message = document.getElementById('block-message');
    const confirmBtn = document.getElementById('confirm-block');
    
    if (resellerIds.length === 1) {
        const reseller = currentResellers.find(r => r.id === resellerIds[0]);
        message.textContent = `Tem certeza que deseja bloquear o revendedor "${reseller.username}"?`;
    } else {
        message.textContent = `Tem certeza que deseja bloquear ${resellerIds.length} revendedores selecionados?`;
    }
    
    confirmBtn.dataset.resellerIds = JSON.stringify(resellerIds);
    Modal.show('block-modal');
}

function showUnblockModal(resellerId) {
    const modal = document.getElementById('unblock-modal');
    const message = document.getElementById('unblock-message');
    const confirmBtn = document.getElementById('confirm-unblock');
    
    const reseller = currentResellers.find(r => r.id === resellerId);
    message.textContent = `Tem certeza que deseja desbloquear o revendedor "${reseller.username}"?`;
    
    confirmBtn.dataset.resellerId = resellerId;
    Modal.show('unblock-modal');
}

async function confirmBlock() {
    const confirmBtn = document.getElementById('confirm-block');
    const resellerIds = JSON.parse(confirmBtn.dataset.resellerIds);
    const reason = document.getElementById('block-reason').value.trim();
    
    Loading.show('Bloqueando revendedor(es)...');
    
    try {
        const response = await apiRequest('/api/admin/block', {
            method: 'POST',
            body: JSON.stringify({
                reseller_ids: resellerIds,
                reason: reason || 'Bloqueado pelo administrador'
            })
        });
        
        if (response.success) {
            Toast.show(response.message, 'success');
            Modal.hide('block-modal');
            document.getElementById('block-reason').value = '';
            selectedResellers.clear();
            await Promise.all([loadStats(), loadResellers()]);
        }
    } catch (error) {
        Toast.show('Erro ao bloquear: ' + error.message, 'error');
    } finally {
        Loading.hide();
    }
}

async function confirmUnblock() {
    const confirmBtn = document.getElementById('confirm-unblock');
    const resellerId = parseInt(confirmBtn.dataset.resellerId);
    
    Loading.show('Desbloqueando revendedor...');
    
    try {
        const response = await apiRequest('/api/admin/unblock', {
            method: 'POST',
            body: JSON.stringify({ reseller_id: resellerId })
        });
        
        if (response.success) {
            Toast.show(response.message, 'success');
            Modal.hide('unblock-modal');
            await Promise.all([loadStats(), loadResellers()]);
        }
    } catch (error) {
        Toast.show('Erro ao desbloquear: ' + error.message, 'error');
    } finally {
        Loading.hide();
    }
}

async function loadActivityLogs() {
    const limit = document.getElementById('logs-limit').value;
    Loading.show('Carregando logs...');
    
    try {
        const response = await apiRequest(`/api/admin/logs?limit=${limit}`);
        
        if (response.success) {
            displayActivityLogs(response.logs);
        }
    } catch (error) {
        Toast.show('Erro ao carregar logs: ' + error.message, 'error');
    } finally {
        Loading.hide();
    }
}

function displayActivityLogs(logs) {
    const tbody = document.getElementById('logs-tbody');
    tbody.innerHTML = '';
    
    logs.forEach(log => {
        const row = document.createElement('tr');
        
        const timestamp = new Date(log.timestamp).toLocaleString('pt-BR');
        
        // Action color coding
        let actionClass = '';
        if (log.action.includes('BLOCK')) actionClass = 'text-red-600';
        else if (log.action.includes('UNBLOCK')) actionClass = 'text-green-600';
        else if (log.action.includes('LOGIN')) actionClass = 'text-blue-600';
        
        row.innerHTML = `
            <td>${timestamp}</td>
            <td>${log.username}</td>
            <td><span class="${actionClass}">${log.action}</span></td>
            <td>${log.details || '-'}</td>
            <td>${log.ip_address || '-'}</td>
        `;
        
        tbody.appendChild(row);
    });
}

async function viewResellerDetails(resellerId) {
    Loading.show('Carregando detalhes...');
    
    try {
        const response = await apiRequest(`/api/admin/reseller/${resellerId}/customers`);
        
        if (response.success) {
            const reseller = currentResellers.find(r => r.id === resellerId);
            Toast.show(`${reseller.username} possui ${response.total} clientes`, 'info');
        }
    } catch (error) {
        Toast.show('Erro ao carregar detalhes: ' + error.message, 'error');
    } finally {
        Loading.hide();
    }
}

// Atualização automática das estatísticas a cada 30 segundos
setInterval(() => {
    if (isAdminAuthenticated) {
        loadStats();
    }
}, 30000);