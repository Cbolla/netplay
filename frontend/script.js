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
            throw new Error(data.detail || 'Erro na requisição');
        }

        return data;
    } catch (error) {
        console.error('Erro na API:', error);
        throw error;
    }
}

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
    const statusFilterSelect = document.getElementById('customer-status-filter');

    const resellerSelect = document.getElementById('reseller-select');

    // --- Elementos de Link Fixo do Revendedor ---

    // --- Estado da Aplicação ---
    let AUTH_TOKEN = null;
    let CURRENT_RESELLER = null;
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

            // Define CURRENT_RESELLER com os dados da resposta
            CURRENT_RESELLER = {
                id: data.reseller_id,
                username: data.username,
                token: data.token,
                netplay_user_id: data.netplay_user_id || null
            };

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
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Falha ao carregar servidores');

            allAvailableServers = data.servers || [];
            sourceServerSelect.innerHTML = '<option value="">Todos os servidores</option>';
            allAvailableServers.forEach(server => sourceServerSelect.add(new Option(server.name, server.id)));

            // Carregar lista de revendas
            await loadResellersForSelect();

            // Carregar link fixo do revendedor
            await loadResellerFixedLink();

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
        const statusValue = 'ACTIVE';
        const selectedIndex = resellerSelect ? resellerSelect.selectedIndex : -1;
        const selectedOption = selectedIndex >= 0 ? resellerSelect.options[selectedIndex] : null;
        // Extrai valores do option
        const resellerId = selectedOption && selectedOption.dataset ? selectedOption.dataset.resellerId : '';
        const netplayUserId = selectedOption && selectedOption.dataset ? selectedOption.dataset.userId : '';

        try {
            const params = new URLSearchParams();
            if (accountNumber) params.append('account_number', accountNumber);
            if (sourceServerId) params.append('server_id', sourceServerId);
            // Status fixo para ACTIVE (remoção do filtro de status do UI)
            params.append('status', statusValue);

            // Configurar perPage - sempre usar 9999 para carregar todos os clientes
            // A paginação será feita no frontend
            const perPageValue = (pageSizeSelect && pageSizeSelect.value) ?
                (pageSizeSelect.value === 'all' ? '9999' : pageSizeSelect.value) : '9999';
            params.append('perPage', perPageValue);

            if (netplayUserId) {
                params.append('userId', netplayUserId);
            } else if (resellerId) {
                params.append('reseller_id', resellerId);
            } else if (CURRENT_RESELLER && CURRENT_RESELLER.netplay_user_id) {
                params.append('userId', CURRENT_RESELLER.netplay_user_id);
            }
            const response = await fetch(`/api/search_customer?${params.toString()}`, { headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` } });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Erro na busca');
            let results = data.clientes || [];
            allClientsData = results;
            displayCustomerResults(allClientsData);
        } catch (error) {
            Toast.show(error.message, 'error');
        }
    };

    accountNumberInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(performSearch, 500);
    });

    sourceServerSelect.addEventListener('change', performSearch);
    // Removido: statusFilterSelect && statusFilterSelect.addEventListener('change', performSearch);

    resellerSelect && resellerSelect.addEventListener('change', performSearch);

    function displayCustomerResults(clients) {
        customerFilteredData = clients || [];
        customerCurrentPage = 1;
        renderCustomerTablePage();
        show(customerResultsContainer);
    }

    customerTableBody.addEventListener('click', e => {
        if (e.target.classList.contains('customer-checkbox')) {
            updateBatchMigrateButtonState();
            return;
        }
        const viewBtn = e.target.closest('.view-details-btn');
        if (viewBtn) {
            showCustomerDetails(viewBtn.dataset.id);
            return;
        }
        const migrateBtn = e.target.closest('.migrate-single-btn');
        if (migrateBtn) {
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
                    migrarStatusMessage.innerHTML += `
                        <li class="message ${statusClass}">
                            <strong>${res.username}:</strong> ${res.migration_status}
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


    // --- Funcionalidade de Gerenciamento de Revendas ---

    // Função para carregar revendas no select
    async function loadResellersForSelect() {
        try {
            console.log('Carregando revendas para o select...');
            const response = await fetch('/api/admin/resellers', {
                headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` }
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Erro ao carregar revendas');
            }

            // Limpar opções existentes
            resellerSelect.innerHTML = '<option value="" data-reseller-id="" data-user-id="">Todas as revendas</option>';

            // Criar um Set para rastrear user_ids já adicionados (evitar duplicatas)
            const addedUserIds = new Set();

            // Adicionar opções das revendas do banco de dados
            if (data.resellers && data.resellers.length > 0) {
                data.resellers.forEach(reseller => {
                    // Verificar se já foi adicionado
                    const userId = reseller.netplay_user_id;
                    if (userId && addedUserIds.has(userId)) {
                        return; // Pular duplicatas
                    }

                    const option = document.createElement('option');
                    option.value = reseller.id; // compatibilidade
                    option.dataset.resellerId = reseller.id;
                    if (userId) {
                        option.dataset.userId = userId;
                        addedUserIds.add(userId); // Marcar como adicionado
                    }
                    option.textContent = reseller.email || reseller.username || reseller.netplay_username || `Revenda ${reseller.id}`;
                    resellerSelect.appendChild(option);
                });
                console.log(`${data.resellers.length} revendas carregadas no select`);

                // Após carregar revendas locais, também carregar user_ids do NetPlay e mesclar evitando duplicados
                try {
                    const resp2 = await fetch('/api/admin/netplay_user_ids', { headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` } });
                    const data2 = await resp2.json();
                    if (!resp2.ok) throw new Error(data2.detail || 'Erro ao obter user_ids');

                    (data2.user_ids || []).forEach(uid => {
                        if (!addedUserIds.has(uid)) {
                            const option = document.createElement('option');
                            option.value = uid;
                            option.dataset.userId = uid;
                            option.textContent = uid;
                            resellerSelect.appendChild(option);
                            addedUserIds.add(uid);
                        }
                    });
                    console.log('Merge de user_ids do NetPlay concluído');
                } catch (e2) {
                    console.warn('Não foi possível mesclar user_ids do NetPlay:', e2);
                }
            } else {
                console.log('Nenhuma revenda local encontrada, buscando user_ids do NetPlay...');
                try {
                    const resp2 = await fetch('/api/admin/netplay_user_ids', { headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` } });
                    const data2 = await resp2.json();
                    if (!resp2.ok) throw new Error(data2.detail || 'Erro ao obter user_ids');
                    (data2.user_ids || []).forEach(uid => {
                        if (!addedUserIds.has(uid)) {
                            const option = document.createElement('option');
                            option.value = uid;
                            option.dataset.userId = uid;
                            option.textContent = uid;
                            resellerSelect.appendChild(option);
                            addedUserIds.add(uid);
                        }
                    });
                    console.log(`${(data2.user_ids || []).length} user_ids carregados no select`);
                } catch (e2) {
                    console.error('Erro ao obter user_ids do NetPlay:', e2);
                    Toast.show('Erro ao obter user_ids do NetPlay.', 'error');
                }
            }

            // Seleciona por padrão o userId da conta logada, se existir no select
            if (CURRENT_RESELLER && CURRENT_RESELLER.netplay_user_id) {
                const idx = Array.from(resellerSelect.options).findIndex(opt => opt.dataset.userId === String(CURRENT_RESELLER.netplay_user_id));
                if (idx >= 0) {
                    resellerSelect.selectedIndex = idx;
                }
            }

            // Dispara a busca com o filtro padrão (userId do login)
            // IMPORTANTE: Aguardar um pouco para garantir que o select foi atualizado
            setTimeout(() => performSearch(), 100);
        } catch (e) {
            console.error('Erro ao carregar revendas:', e);
            Toast.show(e.message || 'Erro ao carregar revendas', 'error');
        }
    }

    // Função para carregar o link fixo do revendedor
    async function loadResellerFixedLink() {
        try {
            console.log('loadResellerFixedLink chamada');
            console.log('CURRENT_RESELLER:', CURRENT_RESELLER);

            const resellerFixedLinkInput = document.getElementById('reseller-fixed-link');
            const copyResellerLinkBtn = document.getElementById('copy-reseller-link-btn');

            if (!resellerFixedLinkInput) {
                console.error('Elemento reseller-fixed-link não encontrado');
                return;
            }

            if (CURRENT_RESELLER && CURRENT_RESELLER.id) {
                const baseUrl = window.location.origin;
                const fixedLink = `${baseUrl}/r${CURRENT_RESELLER.id}/client`;

                resellerFixedLinkInput.value = fixedLink;
                if (copyResellerLinkBtn) {
                    copyResellerLinkBtn.disabled = false;
                }

                console.log('Link fixo do revendedor carregado:', fixedLink);
            } else {
                console.log('CURRENT_RESELLER não definido ou sem ID');
                resellerFixedLinkInput.placeholder = 'Erro: dados do revendedor não encontrados';
            }
        } catch (error) {
            console.error('Erro ao carregar link fixo:', error);
        }
    }

    // Event listener para copiar link fixo do revendedor
    const copyResellerLinkBtn = document.getElementById('copy-reseller-link-btn');
    if (copyResellerLinkBtn) {
        copyResellerLinkBtn.addEventListener('click', async () => {
            const resellerFixedLinkInput = document.getElementById('reseller-fixed-link');
            try {
                await navigator.clipboard.writeText(resellerFixedLinkInput.value);
                Toast.show('Link fixo copiado para a área de transferência!', 'success');
            } catch (error) {
                // Fallback para navegadores mais antigos
                resellerFixedLinkInput.select();
                document.execCommand('copy');
                Toast.show('Link fixo copiado!', 'success');
            }
        });
    }

    // Carregar links quando a página for carregada
    // Remover estas linhas:
    // document.addEventListener('DOMContentLoaded', () => {
    //     setTimeout(loadGeneratedLinks, 1000);
    // });

    // Paginação da tabela de clientes
    let customerCurrentPage = 1;
    let customerPageSize = 100; // default - corresponde ao valor selecionado no HTML
    let customerFilteredData = [];

    const pageSizeSelect = document.getElementById('customer-page-size');
    const btnPrevPage = document.getElementById('btn-prev-page');
    const btnNextPage = document.getElementById('btn-next-page');
    const pageInfo = document.getElementById('customer-page-info');

    function updatePaginationControls() {
        const totalItems = customerFilteredData.length;
        const totalPages = customerPageSize === 'all' ? 1 : Math.max(1, Math.ceil(totalItems / customerPageSize));
        pageInfo.textContent = customerPageSize === 'all'
            ? `Exibindo todos (${totalItems})`
            : `Página ${customerCurrentPage} de ${totalPages} (Total: ${totalItems})`;
        btnPrevPage.disabled = customerPageSize === 'all' || customerCurrentPage <= 1;
        btnNextPage.disabled = customerPageSize === 'all' || customerCurrentPage >= totalPages;
    }

    function renderCustomerTablePage() {
        customerTableBody.innerHTML = '';
        let itemsToRender = customerFilteredData;
        if (customerPageSize !== 'all') {
            const start = (customerCurrentPage - 1) * customerPageSize;
            const end = start + customerPageSize;
            itemsToRender = customerFilteredData.slice(start, end);
        }
        itemsToRender.forEach(client => {
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
        updatePaginationControls();
        updateBatchMigrateButtonState();
    }

    // Handlers
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', () => {
            const val = pageSizeSelect.value;
            customerPageSize = val === 'all' ? 'all' : parseInt(val, 10);
            customerCurrentPage = 1;
            renderCustomerTablePage();
        });
    }
    if (btnPrevPage) {
        btnPrevPage.addEventListener('click', () => {
            if (customerPageSize !== 'all' && customerCurrentPage > 1) {
                customerCurrentPage -= 1;
                renderCustomerTablePage();
            }
        });
    }
    if (btnNextPage) {
        btnNextPage.addEventListener('click', () => {
            if (customerPageSize !== 'all') {
                const totalPages = Math.max(1, Math.ceil(customerFilteredData.length / customerPageSize));
                if (customerCurrentPage < totalPages) {
                    customerCurrentPage += 1;
                    renderCustomerTablePage();
                }
            }
        });
    }

    // ========================================
    // Barra de Status dos Servidores
    // ========================================
    const serversIndicators = document.getElementById('servers-indicators');
    const refreshServersStatusBtn = document.getElementById('refresh-servers-status');
    let serversStatusInterval;

    const SERVERS_LIST = [
        'SEVEN', 'GALAXY', 'LUNAR', 'SPEED', 'OLYMPUS',
        'EXPLOSION', 'TITA', 'SKY', 'SOLAR', 'URANO',
        'ATENA', 'ANDROMEDA', 'HADES', 'VENUS', 'FIRE'
    ];

    let lastServersStatus = {}; // Armazena o último status conhecido
    let lastCheckTime = null; // Armazena o horário da última verificação

    async function loadServersStatus() {
        if (!serversIndicators) return;

        try {
            const response = await fetch('/api/servers/status');
            const data = await response.json();

            if (data.success && data.servers) {
                lastServersStatus = data.servers;
                lastCheckTime = new Date();
                renderServersIndicators(lastServersStatus, false);
            }
        } catch (error) {
            console.error('Erro ao carregar status dos servidores:', error);
        }
    }

    function renderServersIndicators(serversStatus, isChecking = false) {
        if (!serversIndicators) return;

        serversIndicators.innerHTML = '';

        SERVERS_LIST.forEach(serverName => {
            const indicator = document.createElement('div');
            indicator.className = 'server-indicator';

            const dot = document.createElement('div');
            dot.className = 'server-indicator-dot';

            if (isChecking) {
                dot.classList.add('checking');
            } else {
                const status = serversStatus[serverName];
                if (status && status.online) {
                    dot.classList.add('online');
                } else {
                    dot.classList.add('offline');
                }
            }

            const name = document.createElement('span');
            name.className = 'server-indicator-name';
            name.textContent = serverName;

            indicator.appendChild(dot);
            indicator.appendChild(name);
            serversIndicators.appendChild(indicator);
        });

        // Adicionar timestamp da última verificação
        if (lastCheckTime) {
            const timestamp = document.createElement('div');
            timestamp.className = 'servers-last-check';
            const timeString = lastCheckTime.toLocaleTimeString('pt-BR', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            timestamp.innerHTML = `<i class="fas fa-clock"></i> Última verificação: ${timeString}`;
            serversIndicators.appendChild(timestamp);
        }
    }

    // Carregar status ao fazer login
    const originalLoadInitialData = loadInitialData;
    loadInitialData = async function () {
        await originalLoadInitialData();
        await loadServersStatus();

        // Atualizar a cada 30 segundos
        if (serversStatusInterval) clearInterval(serversStatusInterval);
        serversStatusInterval = setInterval(loadServersStatus, 30000);
    };

    // Botão de refresh manual
    if (refreshServersStatusBtn) {
        refreshServersStatusBtn.addEventListener('click', async () => {
            const icon = refreshServersStatusBtn.querySelector('i');
            icon.classList.add('fa-spin');
            await loadServersStatus();
            setTimeout(() => icon.classList.remove('fa-spin'), 1000);
        });
    }

    // Limpar interval ao fazer logout
    const originalShowLogin = showLogin;
    showLogin = function () {
        originalShowLogin();
        if (serversStatusInterval) {
            clearInterval(serversStatusInterval);
            serversStatusInterval = null;
        }
    };

    // --- Inicialização ---
    showLogin();
});