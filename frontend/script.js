// Sistema de Toast Notifications
const Toast = {
    init() {
        this.toastContainer = document.createElement('div');
        this.toastContainer.className = 'toast-container';
        document.body.appendChild(this.toastContainer);
    },
    show(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const iconMap = { success: 'fa-check-circle', error: 'fa-times-circle', warning: 'fa-exclamation-circle', info: 'fa-info-circle' };
        toast.innerHTML = `<i class="fas ${iconMap[type] || 'fa-info-circle'} toast-icon"></i><span>${message}</span>`;
        this.toastContainer.appendChild(toast);
        void toast.offsetWidth;
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
};

// Sistema de Loading
const Loading = {
    show(message = 'Processando...') {
        let overlay = document.getElementById('loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `<div class="loading-spinner"></div><div class="loading-message"></div>`;
            document.body.appendChild(overlay);
        }
        overlay.querySelector('.loading-message').textContent = message;
        overlay.classList.remove('hidden');
    },
    hide() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.classList.add('hidden');
    }
};

// Sistema de Modal
const Modal = {
    show(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    },
    hide(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            modal.classList.add('hidden');
            document.body.style.overflow = '';
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Toast.init();
    
    // --- Referências aos Elementos ---
    const loginSection = document.getElementById('login-section');
    const panelSection = document.getElementById('panel-section');
    const loginForm = document.getElementById('login-form');
    const btnLogout = document.getElementById('btn-logout');
    const customerResultsContainer = document.getElementById('customer-results-container');
    const customerTableBody = document.querySelector('#customer-table tbody');
    const selectAllCustomersCheckbox = document.getElementById('select-all-customers');
    const btnBatchMigrar = document.getElementById('btn-batch-migrar');
    const sourceServerSelect = document.getElementById('source-server-select');
    const modalMigrar = document.getElementById('modal-migrar');
    const formMigrar = document.getElementById('form-migrar');
    const serverSelectModal = document.getElementById('server-select-modal');
    const migrarStatusMessage = document.getElementById('migrar-status');
    const customerDetailsModal = document.getElementById('customer-details-modal');
    const usernameDisplay = document.getElementById('username-display');
    const accountNumberInput = document.getElementById('account-number');

    // --- Estado da Aplicação ---
    let AUTH_TOKEN = null;
    let selectedCustomerIds = new Set();
    let allClientsData = [];
    let allAvailableServers = [];
    let searchTimeout;

    function show(element) { if (element) element.classList.remove('hidden'); }
    function hide(element) { if (element) element.classList.add('hidden'); }

    function showLogin() {
        hide(panelSection);
        show(loginSection);
        hide(document.getElementById('user-info'));
    }

    // --- Lógica da Aplicação ---
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        Loading.show('Autenticando...');
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: loginForm.username.value, password: loginForm.password.value }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Erro no login');
            
            AUTH_TOKEN = data.token;
            Toast.show('Login bem-sucedido!', 'success');
            usernameDisplay.textContent = loginForm.username.value;
            show(document.getElementById('user-info'));
            hide(loginSection);
            show(panelSection);
            
            loadInitialData();
        } catch (error) {
            Toast.show(error.message, 'error');
        } finally {
            Loading.hide();
        }
    });

    async function loadInitialData() {
        Loading.show('Carregando dados...');
        try {
            const res = await fetch('/api/servidores_e_planos', { headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` } });
            if (!res.ok) throw new Error((await res.json()).detail || 'Falha ao carregar servidores');
            const data = await res.json();
            allAvailableServers = data.servers;
            sourceServerSelect.innerHTML = '<option value="">Todos os servidores</option>';
            allAvailableServers.forEach(server => sourceServerSelect.add(new Option(server.name, server.id)));
        } catch (error) {
            Toast.show(error.message, 'error');
        } finally {
            Loading.hide();
        }
    }

    btnLogout.addEventListener('click', () => {
        AUTH_TOKEN = null;
        showLogin();
    });

    const performSearch = async () => {
        const accountNumber = accountNumberInput.value;
        const sourceServerId = sourceServerSelect.value;
        
        if (!accountNumber && !sourceServerId) {
            hide(customerResultsContainer);
            customerTableBody.innerHTML = '';
            return;
        }

        try {
            const params = new URLSearchParams();
            if (accountNumber) params.append('account_number', accountNumber);
            if (sourceServerId) params.append('server_id', sourceServerId);

            const response = await fetch(`/api/search_customer?${params.toString()}`, { headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` } });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Erro na busca');

            allClientsData = data.clientes || [];
            displayCustomerResults(allClientsData);
        } catch (error) {
            Toast.show(error.message, 'error');
            hide(customerResultsContainer);
        }
    };

    accountNumberInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(performSearch, 500);
    });

    sourceServerSelect.addEventListener('change', performSearch);

    function displayCustomerResults(clients) {
        customerTableBody.innerHTML = '';
        clients.forEach(client => {
            const row = customerTableBody.insertRow();
            const serverName = client.server || 'N/A';
            row.innerHTML = `
                <td><input type="checkbox" class="customer-checkbox" value="${client.id}"></td>
                <td>${client.username || 'N/A'}</td>
                <td>${client.name || 'N/A'}</td>
                <td>${serverName}</td>
                <td>
                    <button class="btn-secondary small-button view-details-btn" data-id="${client.id}"><i class="fas fa-eye"></i> Ver Mais</button>
                    <button class="btn-action small-button migrate-single-btn" data-id="${client.id}"><i class="fas fa-exchange-alt"></i> Migrar</button>
                </td>
            `;
        });
        show(customerResultsContainer);
        updateBatchMigrateButtonState();
    }
    
    customerTableBody.addEventListener('click', e => {
        if (e.target.classList.contains('customer-checkbox')) {
            updateBatchMigrateButtonState();
            return;
        }
        const viewBtn = e.target.closest('.view-details-btn');
        if(viewBtn) {
            showCustomerDetails(viewBtn.dataset.id);
            return;
        }
        const migrateBtn = e.target.closest('.migrate-single-btn');
        if(migrateBtn) {
            handleSingleMigration(migrateBtn.dataset.id);
            return;
        }
    });

    selectAllCustomersCheckbox.addEventListener('change', e => {
        document.querySelectorAll('.customer-checkbox').forEach(cb => cb.checked = e.target.checked);
        updateBatchMigrateButtonState();
    });

    function updateBatchMigrateButtonState() {
        selectedCustomerIds.clear();
        document.querySelectorAll('.customer-checkbox:checked').forEach(cb => selectedCustomerIds.add(cb.value));
        selectedCustomerIds.size > 0 ? show(btnBatchMigrar) : hide(btnBatchMigrar);
    }

    function showCustomerDetails(customerId) {
        const client = allClientsData.find(c => String(c.id) === String(customerId));
        if (!client) return;
        const serverName = client.server || 'N/A';
        const packageName = client.package || 'N/A';
        document.getElementById('customer-details-content').innerHTML = `
            <p><strong>ID:</strong> ${client.id || 'N/A'}</p>
            <p><strong>Conta:</strong> ${client.username || 'N/A'}</p>
            <p><strong>Nome:</strong> ${client.name || 'N/A'}</p>
            <p><strong>Servidor:</strong> ${serverName}</p>
            <p><strong>Plano:</strong> ${packageName}</p>
        `;
        Modal.show('customer-details-modal');
    }
    document.getElementById('close-detail-modal').addEventListener('click', () => Modal.hide('customer-details-modal'));

    function handleSingleMigration(customerId) {
        selectedCustomerIds.clear();
        selectedCustomerIds.add(customerId);
        openMigrationModal();
    }

    btnBatchMigrar.addEventListener('click', openMigrationModal);

    function openMigrationModal() {
        if (selectedCustomerIds.size === 0) return;
        serverSelectModal.innerHTML = '<option value="" disabled selected>Selecione um novo servidor</option>';
        allAvailableServers.forEach(server => serverSelectModal.add(new Option(server.name, server.id)));
        migrarStatusMessage.innerHTML = '';
        Modal.show('modal-migrar');
    }

    formMigrar.addEventListener('submit', e => {
        e.preventDefault();
        batchMigrateCustomers();
    });
    
    document.getElementById('cancel-modal-migrar').addEventListener('click', () => Modal.hide('modal-migrar'));
    document.getElementById('close-modal-migrar').addEventListener('click', () => Modal.hide('modal-migrar'));

    async function batchMigrateCustomers() {
        const serverId = serverSelectModal.value;
        const selectedOption = serverSelectModal.options[serverSelectModal.selectedIndex];
        const serverName = selectedOption ? selectedOption.text : null;
        
        if (!serverId) return Toast.show('Selecione um servidor de destino.', 'error');

        const customersToMigrate = allClientsData
            .filter(client => selectedCustomerIds.has(String(client.id)) && client.package)
            .map(client => ({ 
                id: String(client.id), 
                username: String(client.username),
                package_name: String(client.package) // Envia o NOME do plano
            }));

        if (customersToMigrate.length !== selectedCustomerIds.size) {
            Toast.show('Aviso: Alguns clientes foram ignorados por falta de informações do Plano.', 'warning', 6000);
        }
        if (customersToMigrate.length === 0) return Toast.show('Nenhum cliente válido para migrar.', 'error');

        const payload = { 
            customers: customersToMigrate, 
            server_id: serverId, 
            server_name: serverName
        };
        Loading.show(`Processando ${customersToMigrate.length} cliente(s)...`);
        
        try {
            const response = await fetch('/api/batch_migrar', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${AUTH_TOKEN}` },
                body: JSON.stringify(payload),
            });
            const data = await response.json();

            if (!response.ok) {
                let errorMsg = "Erro no processamento.";
                if (data.detail) {
                    if (Array.isArray(data.detail)) {
                        errorMsg = data.detail.map(err => `${err.loc.join(' > ')}: ${err.msg}`).join('; ');
                    } else {
                        errorMsg = data.detail;
                    }
                }
                throw new Error(errorMsg);
            }

            migrarStatusMessage.innerHTML = `<p class="message success">${data.message}</p>`;
            if (data.results && data.results.length > 0) {
                migrarStatusMessage.innerHTML += '<h4>Resultados Detalhados:</h4><ul>';
                data.results.forEach(res => {
                    const statusClass = res.migration_status.includes('sucesso') ? 'success' : 'error';
                    const maxplayerStatus = res.maxplayer_status;
                    let maxplayerClass = 'info';
                    if (maxplayerStatus.includes('sucesso')) maxplayerClass = 'success';
                    if (maxplayerStatus.includes('Não') || maxplayerStatus.includes('Erro') || maxplayerStatus.includes('Falha')) maxplayerClass = 'error';

                    migrarStatusMessage.innerHTML += `
                        <li class="message ${statusClass}">
                            <strong>${res.username}:</strong> 
                            Migração Netplay: ${res.migration_status} | 
                            Migração Maxplayer: <strong class="message ${maxplayerClass}" style="padding: 2px 5px; border-radius: 4px;">${maxplayerStatus}</strong>
                        </li>
                    `;
                });
                migrarStatusMessage.innerHTML += '</ul>';
            }

            setTimeout(() => {
                Modal.hide('modal-migrar');
                performSearch();
            }, 8000);

        } catch (error) {
            console.error('Erro detalhado na migração:', error);
            const errorMessage = `Falha na operação: ${error.message}`;
            migrarStatusMessage.innerHTML = `<p class="message error">${errorMessage}</p>`;
            Toast.show(errorMessage, 'error', 8000);
        } finally {
            Loading.hide();
        }
    }

    // --- Inicialização ---
    showLogin();
});