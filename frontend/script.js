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
                token: data.token
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
            if (!res.ok) throw new Error((await res.json()).detail || 'Falha ao carregar servidores');
            const data = await res.json();
            allAvailableServers = data.servers;
            sourceServerSelect.innerHTML = '<option value="">Todos os servidores</option>';
            allAvailableServers.forEach(server => sourceServerSelect.add(new Option(server.name, server.id)));
            
            // Carregar links gerados automaticamente após o login
            await loadGeneratedLinks();
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
                    <button class="btn-primary small-button generate-link-btn" data-username="${client.username}" data-id="${client.id}"><i class="fas fa-link"></i> Gerar Link</button>
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
        const generateLinkBtn = e.target.closest('.generate-link-btn');
        if(generateLinkBtn) {
            handleGenerateClientLink(generateLinkBtn.dataset.username, generateLinkBtn.dataset.id);
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

    // --- Funcionalidade de Geração de Links para Clientes ---
    const generateClientLinkForm = document.getElementById('generate-client-link-form');
    const generatedLinkContainer = document.getElementById('generated-link-container');
    const generatedLinkInput = document.getElementById('generated-link');
    const copyLinkBtn = document.getElementById('copy-link-btn');

    // Função para gerar link diretamente da tabela
    async function handleGenerateClientLink(username, clientId) {
        try {
            Loading.show();
            
            // Buscar dados do cliente para obter a senha
            const clientData = await getClientData(clientId);
            if (!clientData || !clientData.password) {
                Toast.show('Não foi possível obter os dados do cliente.', 'error');
                return;
            }
            
            const response = await apiRequest('/api/create_client_link', {
                method: 'POST',
                body: JSON.stringify({
                    client_username: username,
                    client_password: clientData.password
                })
            });
            
            if (response.success) {
                // Mostrar o link gerado
                generatedLinkInput.value = response.link_url;
                generatedLinkContainer.classList.remove('hidden');
                
                // Scroll para a seção do link
                generatedLinkContainer.scrollIntoView({ behavior: 'smooth' });
                
                // Recarregar a lista de links gerados
                loadGeneratedLinks();
                
                Toast.show('Link gerado com sucesso!', 'success');
            } else {
                Toast.show(`Erro na API: ${response.error}`, 'error');
            }
        } catch (error) {
            console.error('Erro ao gerar link:', error);
            Toast.show(`Erro ao gerar link: ${error.message}`, 'error');
        } finally {
            Loading.hide();
        }
    }
    
    // Função auxiliar para buscar dados do cliente
    async function getClientData(clientId) {
        try {
            const response = await apiRequest(`/api/client/${clientId}`);
            return response.success ? response.client : null;
        } catch (error) {
            console.error('Erro ao buscar dados do cliente:', error);
            return null;
        }
    }

    generateClientLinkForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(generateClientLinkForm);
        const clientUsername = formData.get('client_username');
        const clientPassword = formData.get('client_password');
        
        if (!clientUsername || !clientPassword) {
            Toast.show('Por favor, preencha todos os campos.', 'error');
            return;
        }
        
        try {
            // Chama a API para criar o link do cliente
            const response = await apiRequest('/api/create_client_link', {
                method: 'POST',
                body: JSON.stringify({
                    client_username: clientUsername,
                    client_password: clientPassword
                })
            });
            
            if (response.success) {
                // Exibe o link gerado
                generatedLinkInput.value = response.link_url;
                generatedLinkContainer.classList.remove('hidden');
                
                // Recarregar a lista de links gerados
                loadGeneratedLinks();
                
                Toast.show('Link gerado com sucesso!', 'success');
                
                // Scroll para mostrar o resultado
                generatedLinkContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                Toast.show('Erro ao gerar link: ' + (response.message || 'Erro desconhecido'), 'error');
            }
        } catch (error) {
            Toast.show('Erro ao gerar link: ' + error.message, 'error');
        }
    });

    // Funcionalidade de copiar link
    copyLinkBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(generatedLinkInput.value);
            Toast.show('Link copiado para a área de transferência!', 'success');
            
            // Feedback visual temporário
            const originalText = copyLinkBtn.innerHTML;
            copyLinkBtn.innerHTML = '<i class="fas fa-check"></i> Copiado!';
            copyLinkBtn.style.backgroundColor = '#10b981';
            
            setTimeout(() => {
                copyLinkBtn.innerHTML = originalText;
                copyLinkBtn.style.backgroundColor = '';
            }, 2000);
        } catch (err) {
            // Fallback para navegadores mais antigos
            generatedLinkInput.select();
            document.execCommand('copy');
            Toast.show('Link copiado para a área de transferência!', 'success');
        }
    });

    // --- Funcionalidade de Gerenciamento de Links Gerados ---
    const refreshLinksBtn = document.getElementById('refresh-links-btn');
    const generatedLinksContainer = document.getElementById('generated-links-container');
    const noLinksMessage = document.getElementById('no-links-message');
    const generatedLinksTbody = document.getElementById('generated-links-tbody');

    // Função para carregar links gerados
    async function loadGeneratedLinks() {
        try {
            console.log('Carregando links gerados...');
            const data = await apiRequest('/api/generated_links');
            console.log('Resposta da API:', data);
            
            if (data.success && data.links && data.links.length > 0) {
                console.log('Links encontrados:', data.links.length);
                displayGeneratedLinks(data.links);
                generatedLinksContainer.classList.remove('hidden');
                noLinksMessage.classList.add('hidden');
            } else {
                console.log('Nenhum link encontrado ou erro na resposta');
                generatedLinksContainer.classList.add('hidden');
                noLinksMessage.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Erro ao carregar links:', error);
            Toast.show('Erro ao carregar links gerados.', 'error');
        }
    }

    // Função para exibir links na tabela
    function displayGeneratedLinks(links) {
        generatedLinksTbody.innerHTML = '';
        
        links.forEach(link => {
            const row = document.createElement('tr');
            const createdDate = new Date(link.created_at).toLocaleDateString('pt-BR');
            const lastAccess = link.last_access ? new Date(link.last_access).toLocaleDateString('pt-BR') : 'Nunca';
            const status = link.is_active ? 'Ativo' : 'Inativo';
            const statusClass = link.is_active ? 'status-active' : 'status-inactive';
            
            row.innerHTML = `
                <td>${link.client_username}</td>
                <td>${createdDate}</td>
                <td>${lastAccess}</td>
                <td><span class="status-badge ${statusClass}">${status}</span></td>
                <td>
                    <div class="table-actions">
                        <button class="btn-table btn-copy-link" data-link="${link.link_url}" title="Copiar Link">
                            <i class="fas fa-copy"></i>
                        </button>
                        <button class="btn-table btn-delete-link" data-link-id="${link.id}" title="Excluir Link">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            
            generatedLinksTbody.appendChild(row);
        });
        
        // Adicionar event listeners para os botões da tabela
        addTableEventListeners();
    }

    // Função para adicionar event listeners aos botões da tabela
    function addTableEventListeners() {
        // Botões de copiar link
        document.querySelectorAll('.btn-copy-link').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const linkUrl = e.currentTarget.dataset.link;
                try {
                    await navigator.clipboard.writeText(linkUrl);
                    Toast.show('Link copiado para a área de transferência!', 'success');
                } catch (error) {
                    // Fallback para navegadores mais antigos
                    const textArea = document.createElement('textarea');
                    textArea.value = linkUrl;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    Toast.show('Link copiado para a área de transferência!', 'success');
                }
            });
        });
        
        // Botões de excluir link
        document.querySelectorAll('.btn-delete-link').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const linkId = e.currentTarget.dataset.linkId;
                if (confirm('Tem certeza que deseja excluir este link?')) {
                    await deleteGeneratedLink(linkId);
                }
            });
        });
    }

    // Função para excluir um link gerado
    async function deleteGeneratedLink(linkId) {
        try {
            Loading.show();
            const response = await apiRequest(`/api/generated_links/${linkId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            
            if (data.success) {
                Toast.show('Link excluído com sucesso!', 'success');
                loadGeneratedLinks(); // Recarregar a lista
            } else {
                Toast.show(data.error || 'Erro ao excluir link.', 'error');
            }
        } catch (error) {
            console.error('Erro ao excluir link:', error);
            Toast.show('Erro ao excluir link.', 'error');
        } finally {
            Loading.hide();
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
                copyResellerLinkBtn.disabled = false;
                
                console.log('Link fixo do revendedor carregado:', fixedLink);
            } else {
                console.log('CURRENT_RESELLER não definido ou sem ID');
                resellerFixedLinkInput.placeholder = 'Erro: dados do revendedor não encontrados';
            }
        } catch (error) {
            console.error('Erro ao carregar link fixo:', error);
        }
    }
    
    // Event listener para o botão de atualizar links
    if (refreshLinksBtn) {
        refreshLinksBtn.addEventListener('click', loadGeneratedLinks);
    }
    
    // Event listener para copiar link fixo do revendedor
    document.getElementById('copy-reseller-link-btn').addEventListener('click', async () => {
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

    // Carregar links quando a página for carregada
    // Remover estas linhas:
    // document.addEventListener('DOMContentLoaded', () => {
    //     setTimeout(loadGeneratedLinks, 1000);
    // });

    // --- Inicialização ---
    showLogin();
});