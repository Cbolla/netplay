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

        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        };

        const icon = document.createElement('i');
        icon.className = `fas ${iconMap[type] || 'fa-info-circle'} toast-icon`;

        const text = document.createElement('span');
        text.textContent = message;

        toast.appendChild(icon);
        toast.appendChild(text);
        this.toastContainer.appendChild(toast);

        // Trigger reflow to enable animation
        void toast.offsetWidth;
        toast.classList.add('show');

        // Auto dismiss
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
};

// Sistema de Loading
const Loading = {
    show(message = 'Processando...') {
        console.log('Loading.show called:', message); // DEBUG
        let overlay = document.getElementById('loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.className = 'loading-overlay';
            document.body.appendChild(overlay);
        }
        
        // Atualiza a mensagem
        const loadingMessageElem = overlay.querySelector('.loading-message');
        if (loadingMessageElem) {
            loadingMessageElem.textContent = message;
        }

        overlay.classList.remove('hidden');
    },

    hide() {
        console.log('Loading.hide called.'); // DEBUG
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.classList.add('hidden');
    },

    updateProgress(percent) {
        const progressBar = document.getElementById('progress-bar');
        const progressContainer = document.querySelector('.progress-container');
        
        if (progressBar) {
            progressContainer.classList.remove('hidden');
            progressBar.style.width = `${percent}%`;
        }
    }
};

// Sistema de Modal
const Modal = {
    show(modalId) {
        console.log(`Modal.show called for ID: ${modalId}`); // DEBUG
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden'); // <--- ADICIONADO: Remove a classe hidden
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            console.log(`Modal '${modalId}' should now be active.`); // DEBUG
        } else {
            console.error(`Modal with ID '${modalId}' not found.`); // DEBUG
        }
    },

    hide(modalId) {
        console.log(`Modal.hide called for ID: ${modalId}`); // DEBUG
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            modal.classList.add('hidden'); // <--- ADICIONADO: Adiciona a classe hidden ao esconder
            document.body.style.overflow = '';
            console.log(`Modal '${modalId}' should now be hidden.`); // DEBUG
        } else {
             console.warn(`Modal with ID '${modalId}' not found when trying to hide.`); // DEBUG
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Inicializa sistemas
    Toast.init();
    
    // --- Referências aos Elementos HTML ---
    // Usamos 'let' e try-catch para capturar erros na aquisição de elementos
    let loginSection, panelSection, loginForm, loginMessage, btnLogout, btnTrocarServidor,
        trocarServidorOptions, btnClienteIndividual, searchCustomerForm, searchMessage,
        customerResultsContainer, customerTableBody, selectAllCustomersCheckbox, btnBatchMigrar,
        sourceServerSelect, modalMigrar, closeModalMigrarBtn, formMigrar, serverSelectModal,
        packageSelectModal, migrarStatusMessage, customerDetailsModal, cancelModalMigrarBtn,
        usernameDisplay; // Adicionado para user-info

    try {
        loginSection = document.getElementById('login-section');
        panelSection = document.getElementById('panel-section');
        loginForm = document.getElementById('login-form');
        loginMessage = document.getElementById('login-message');
        btnLogout = document.getElementById('btn-logout');
        btnTrocarServidor = document.getElementById('btn-trocar-servidor');
        trocarServidorOptions = document.getElementById('trocar-servidor-options');
        btnClienteIndividual = document.getElementById('btn-cliente-individual');
        searchCustomerForm = document.getElementById('search-customer-form');
        searchMessage = document.getElementById('search-message');
        customerResultsContainer = document.getElementById('customer-results-container');
        customerTableBody = document.querySelector('#customer-table tbody');
        selectAllCustomersCheckbox = document.getElementById('select-all-customers');
        btnBatchMigrar = document.getElementById('btn-batch-migrar');
        sourceServerSelect = document.getElementById('source-server-select');
        modalMigrar = document.getElementById('modal-migrar');
        closeModalMigrarBtn = document.getElementById('close-modal-migrar');
        formMigrar = document.getElementById('form-migrar');
        serverSelectModal = document.getElementById('server-select-modal');
        packageSelectModal = document.getElementById('package-select-modal');
        migrarStatusMessage = document.getElementById('migrar-status');
        customerDetailsModal = document.getElementById('customer-details-modal');
        cancelModalMigrarBtn = document.getElementById('cancel-modal-migrar');
        usernameDisplay = document.getElementById('username-display'); // Referência ao span de username


        // DEBUG: Loga o status de cada elemento adquirido para depuração
        console.log("Elementos HTML adquiridos:");
        console.log({
            loginSection: loginSection,
            panelSection: panelSection,
            clienteIndividualSection: document.getElementById('cliente-individual-section'), // Re-check this one explicitly
            customerResultsContainer: customerResultsContainer,
            customerTableBody: customerTableBody,
            selectAllCustomersCheckbox: selectAllCustomersCheckbox,
            btnBatchMigrar: btnBatchMigrar,
            sourceServerSelect: sourceServerSelect,
            modalMigrar: modalMigrar,
            customerDetailsModal: customerDetailsModal
        });

        // Verificação crítica: se algum elemento essencial é null, interrompa.
        if (!loginSection || !panelSection || !document.getElementById('cliente-individual-section')) {
            console.error("Erro: Um ou mais elementos HTML essenciais não foram encontrados no DOM. Verifique seus IDs no HTML.");
            Toast.show("Erro crítico: Interface incompleta. Verifique o console.", 'error');
            Loading.hide(); // Garante que o loading não fique travado
            return; // Impede a continuação do script se elementos não forem encontrados
        }

    } catch (e) {
        console.error("Erro FATAL ao adquirir referências de elementos HTML:", e);
        Toast.show("Erro crítico: A inicialização da interface falhou. Verifique o console.", 'error');
        Loading.hide(); // Garante que o loading não fique travado
        return; // Impede a continuação do script
    }

    // --- Estado da Aplicação ---
    let AUTH_TOKEN = null;
    let selectedCustomerIds = new Set();
    let allClientsData = [];
    let currentDetailModal = null;
    let allAvailableServers = []; // NOVO: Armazena todos os servidores disponíveis
    let allAvailablePackages = []; // NOVO: Armazena todos os planos disponíveis

    // --- Funções Auxiliares ---
    function show(element) {
        if (element) element.classList.remove('hidden');
    }

    function hide(element) {
        if (element) element.classList.add('hidden');
    }

    function resetAllSections() {
        console.log("resetAllSections called."); // DEBUG
        // Oculta seções principais
        hide(loginSection); // Garante que o login seja escondido
        hide(panelSection);
        hide(trocarServidorOptions);
        hide(document.getElementById('cliente-individual-section')); // Usa getElementById diretamente para segurança
        hide(customerResultsContainer);
        hide(modalMigrar);
        if (currentDetailModal) Modal.hide(currentDetailModal.id); // Esconde modal de detalhes se aberto

        // Limpa mensagens e formulários
        loginMessage.textContent = '';
        searchMessage.textContent = '';
        migrarStatusMessage.textContent = '';
        loginForm.reset();
        searchCustomerForm.reset();

        // Reseta estados de seleção e dados
        selectedCustomerIds.clear();
        allClientsData = [];
        customerTableBody.innerHTML = '';
        selectAllCustomersCheckbox.checked = false;
        hide(btnBatchMigrar);

        // NENHUMA seção é mostrada por padrão aqui, apenas resetada.
        // A visibilidade será controlada por showLogin() ou showPanel().
    }

    // Função para mostrar apenas a tela de login
    function showLogin() {
        resetAllSections(); // Esconde tudo primeiro
        show(loginSection); // Mostra explicitamente a seção de login
        hide(document.getElementById('user-info')); // Esconde info do usuário
        if (usernameDisplay) usernameDisplay.textContent = ''; // Limpa o nome de usuário
    }

    // --- Gerenciamento de Login ---
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = loginForm.username.value;
        const password = loginForm.password.value;

        try {
            Loading.show('Autenticando...');
            loginMessage.textContent = 'Autenticando...';
            loginMessage.className = 'message';

            console.log('Login: Enviando requisição para o backend.'); // DEBUG

            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json();

            if (response.ok) {
                AUTH_TOKEN = data.token || data.access_token;
                Toast.show('Login bem-sucedido!', 'success');
                // Adiciona o nome de usuário ao header
                if (usernameDisplay) {
                    usernameDisplay.textContent = username;
                    show(document.getElementById('user-info')); // Mostra a div de user-info
                }
                showPanel(); // Esta função agora controla a visibilidade (chama resetAllSections)
            } else {
                throw new Error(data.detail || 'Erro no login. Verifique suas credenciais.');
            }
        } catch (error) {
            console.error('Erro de login:', error); // DEBUG
            loginMessage.textContent = error.message;
            loginMessage.classList.add('error');
            Toast.show(error.message, 'error');
        } finally {
            Loading.hide();
        }
    });

    btnLogout.addEventListener('click', () => {
        AUTH_TOKEN = null;
        Toast.show('Você foi desconectado.', 'info');
        showLogin(); // Volta para o login (chama resetAllSections internamente)
    });

    // --- Gerenciamento do Painel ---
    // Função para mostrar apenas a tela do painel
    function showPanel() {
        resetAllSections(); // Esconde tudo primeiro
        show(panelSection); // Depois mostra o painel
    }

    btnTrocarServidor.addEventListener('click', () => {
        if (trocarServidorOptions.classList.contains('hidden')) {
            show(trocarServidorOptions);
            hide(document.getElementById('cliente-individual-section')); // Usa getElementById diretamente
            hide(customerResultsContainer);
            hide(modalMigrar);
            if (currentDetailModal) Modal.hide(currentDetailModal.id);
        } else {
            hide(trocarServidorOptions);
        }
    });

    btnClienteIndividual.addEventListener('click', async () => {
        hide(trocarServidorOptions);
        show(document.getElementById('cliente-individual-section')); // Usa getElementById diretamente
        resetSearchSection();

        try {
            Loading.show('Carregando servidores...');
            console.log('Cliente Individual: Enviando requisição para carregar servidores.'); // DEBUG
            const resServers = await fetch('/api/servidores_e_planos');
            const data = await resServers.json(); // Renomeado para evitar conflito

            allAvailableServers = data.servers; // Armazena globalmente
            allAvailablePackages = data.packages; // Armazena globalmente
            
            sourceServerSelect.innerHTML = '<option value="">Todos os servidores</option>';
            allAvailableServers.forEach(server => {
                const option = document.createElement('option');
                option.value = server.id;
                option.textContent = server.name;
                sourceServerSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Erro ao carregar servidores:', error); // DEBUG
            Toast.show('Erro ao carregar lista de servidores', 'error');
        } finally {
            Loading.hide();
        }
    });

    function resetSearchSection() {
        hide(customerResultsContainer);
        hide(modalMigrar);
        if (currentDetailModal) Modal.hide(currentDetailModal.id);

        searchMessage.textContent = '';
        searchCustomerForm.reset();
        selectedCustomerIds.clear();
        allClientsData = [];
        customerTableBody.innerHTML = '';
        selectAllCustomersCheckbox.checked = false;
        hide(btnBatchMigrar);
    }

    // --- Pesquisa de Clientes ---
    searchCustomerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await performSearch();
    });

    async function performSearch() {
        const accountNumber = searchCustomerForm.elements['account-number'].value;
        const sourceServerId = sourceServerSelect.value;

        if (!accountNumber && !sourceServerId) {
            Toast.show('Informe um número de conta ou selecione um servidor', 'warning');
            return;
        }

        try {
            Loading.show('Buscando clientes...');
            searchMessage.textContent = 'Buscando cliente(s)...';
            searchMessage.className = 'message';
            console.log('Perform Search: Iniciando busca de clientes.'); // DEBUG

            const params = new URLSearchParams();
            if (accountNumber) params.append('account_number', accountNumber);
            if (sourceServerId) params.append('server_id', sourceServerId);

            console.log('Perform Search: Parâmetros enviados:', params.toString()); // DEBUG

            const response = await fetch(`/api/search_customer?${params.toString()}`, {
                headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` }
            });

            if (!response.ok) {
                // Tenta ler o erro do backend se a resposta não for ok
                const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(errorData.detail || response.statusText);
            }

            const data = await response.json();

            if (data.clientes && data.clientes.length > 0) {
                displayCustomerResults(data.clientes);
                searchMessage.textContent = `${data.clientes.length} cliente(s) encontrado(s)`;
                searchMessage.classList.add('success');
                Toast.show(`${data.clientes.length} cliente(s) encontrado(s)`, 'success');
            } else {
                throw new Error('Nenhum cliente encontrado com os filtros fornecidos');
            }
        } catch (error) {
            console.error('Erro na busca:', error); // DEBUG
            searchMessage.textContent = error.message;
            searchMessage.classList.add('error');
            hide(customerResultsContainer);
            Toast.show(error.message, 'error');
        } finally {
            Loading.hide();
        }
    }

    function displayCustomerResults(clients) {
        allClientsData = clients;
        customerTableBody.innerHTML = '';
        selectedCustomerIds.clear();
        selectAllCustomersCheckbox.checked = false;
        hide(btnBatchMigrar);

        clients.forEach(client => {
            const row = customerTableBody.insertRow();
            row.setAttribute('data-customer-id', client.id);
            
            // Checkbox
            const checkboxCell = row.insertCell();
            checkboxCell.setAttribute('data-label', 'Selecionar');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'customer-checkbox';
            checkbox.value = client.id;
            checkbox.addEventListener('change', updateBatchMigrateButtonState);
            checkboxCell.appendChild(checkbox);

            // Dados do cliente
            const usernameCell = row.insertCell();
            usernameCell.setAttribute('data-label', 'Conta');
            usernameCell.textContent = client.username || 'N/A';

            const nameCell = row.insertCell();
            nameCell.setAttribute('data-label', 'Nome');
            nameCell.textContent = client.name || 'N/A';

            const serverCell = row.insertCell();
            serverCell.setAttribute('data-label', 'Servidor');
            serverCell.textContent = client.server || 'N/A';

            // Ações
            const actionsCell = row.insertCell();
            actionsCell.setAttribute('data-label', 'Ações');
            const viewMoreBtn = document.createElement('button');
            viewMoreBtn.innerHTML = '<i class="fas fa-eye"></i> Ver Mais';
            viewMoreBtn.classList.add('btn-secondary', 'small-button');
            viewMoreBtn.addEventListener('click', () => showCustomerDetails(client.id));
            actionsCell.appendChild(viewMoreBtn);
        });

        show(customerResultsContainer);
        updateBatchMigrateButtonState(); // Garante que o estado do botão está correto após a exibição dos resultados
    }

    // --- Seleção de Clientes ---
    selectAllCustomersCheckbox.addEventListener('change', () => {
        const checkboxes = document.querySelectorAll('.customer-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = selectAllCustomersCheckbox.checked;
        });
        updateBatchMigrateButtonState();
    });

    function updateBatchMigrateButtonState() {
        selectedCustomerIds.clear();
        const checkboxes = document.querySelectorAll('.customer-checkbox:checked');
        checkboxes.forEach(checkbox => {
            selectedCustomerIds.add(checkbox.value);
        });

        console.log('Clientes selecionados (IDs):', Array.from(selectedCustomerIds)); // DEBUG: Mostra IDs selecionados
        console.log('Número de clientes selecionados:', selectedCustomerIds.size); // DEBUG: Mostra a contagem

        if (selectedCustomerIds.size > 0) {
            show(btnBatchMigrar);
        } else {
            hide(btnBatchMigrar);
        }

        // Atualiza "Selecionar Todos"
        const allCheckboxes = document.querySelectorAll('.customer-checkbox');
        selectAllCustomersCheckbox.checked = allCheckboxes.length > 0 && 
                                            selectedCustomerIds.size === allCheckboxes.length;
    }

    // --- Detalhes do Cliente ---
    function showCustomerDetails(customerId) {
        const client = allClientsData.find(c => c.id === customerId);
        if (!client) {
            Toast.show('Detalhes do cliente não encontrados', 'error');
            return;
        }

        const detailsContent = customerDetailsModal.querySelector('.modal-body'); // Ajustado para pegar o corpo do modal
        detailsContent.innerHTML = `
            <p><strong>ID:</strong> ${client.id}</p>
            <p><strong>Nome:</strong> ${client.name}</p>
            <p><strong>Conta:</strong> ${client.username}</p>
            <p><strong>Servidor:</strong> ${client.server}</p>
            <p><strong>Plano:</strong> ${client.package}</p>
            <p><strong>Vencimento:</strong> ${client.vencimento}</p>
            <p><strong>Status:</strong> ${client.status}</p>
        `;

        currentDetailModal = customerDetailsModal; // Armazena a referência para o modal atual
        Modal.show('customer-details-modal');

        document.getElementById('close-detail-modal').addEventListener('click', () => {
            Modal.hide('customer-details-modal');
            currentDetailModal = null;
        });
    }
    // Listener global para fechar modais clicando fora
    window.addEventListener('click', (event) => {
        if (event.target === modalMigrar) {
            Modal.hide('modal-migrar');
        }
        if (currentDetailModal && event.target === currentDetailModal) {
            Modal.hide('customer-details-modal');
            currentDetailModal = null;
        }
    });

    // NOVO: Função para popular a seleção de planos com base no servidor
    function populatePackageSelect(selectedServerId) {
        packageSelectModal.innerHTML = '<option value="">Selecione (opcional)</option>';
        const filteredPackages = allAvailablePackages.filter(pkg => 
            !selectedServerId || pkg.server_id === selectedServerId
        );
        filteredPackages.forEach(pkg => {
            const option = document.createElement('option');
            option.value = pkg.id;
            option.textContent = `${pkg.name} (${pkg.server_name})`;
            packageSelectModal.appendChild(option);
        });
    }

    // NOVO: Listener para o select de servidor no modal de migração
    serverSelectModal.addEventListener('change', () => {
        console.log("Server select changed to:", serverSelectModal.value); // DEBUG
        populatePackageSelect(serverSelectModal.value);
    });

    // --- Migração de Clientes ---
    btnBatchMigrar.addEventListener('click', async () => {
        if (selectedCustomerIds.size === 0) {
            Toast.show('Selecione pelo menos um cliente', 'error');
            return;
        }

        console.log('Batch Migrate Button Clicked: IDs to migrate:', Array.from(selectedCustomerIds)); // DEBUG

        try {
            Loading.show('Carregando opções...');
            console.log('Batch Migrate: Fazendo fetch de /api/servidores_e_planos...'); // DEBUG
            const res = await fetch('/api/servidores_e_planos', {
                headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` } // Adiciona cabeçalho de auth
            });

            console.log('Batch Migrate: Resposta do fetch de servidores/planos OK:', res.ok, 'Status:', res.status); // DEBUG
            
            if (!res.ok) { // Verifica se a resposta foi bem-sucedida
                 const errorText = await res.text(); // Pega o texto bruto do erro
                 console.error('Batch Migrate: Erro na resposta da API /servidores_e_planos:', errorText); // DEBUG
                 throw new Error(`Erro ao carregar servidores/planos: ${res.status} ${res.statusText}`);
            }

            const data = await res.json(); // Renomeado para evitar conflito
            console.log('Batch Migrate: Dados recebidos de servidores/planos:', data); // DEBUG

            allAvailableServers = data.servers; // Armazena globalmente
            allAvailablePackages = data.packages; // Armazena globalmente

            serverSelectModal.innerHTML = '<option value="">Selecione (opcional)</option>';
            allAvailableServers.forEach(server => { // Popula com todos os servidores
                const option = document.createElement('option');
                option.value = server.id;
                option.textContent = server.name;
                serverSelectModal.appendChild(option);
            });

            populatePackageSelect(serverSelectModal.value); // Chame para popular pacotes iniciais
            migrarStatusMessage.textContent = ''; // Limpa mensagens anteriores no modal

            console.log('Batch Migrate: Chamando Modal.show("modal-migrar")...'); // DEBUG
            Modal.show('modal-migrar'); // ABRE O MODAL
        } catch (error) {
            console.error('Erro ao carregar opções ou abrir modal:', error); // DEBUG
            Toast.show('Erro ao carregar opções de migração', 'error');
        } finally {
            Loading.hide();
        }
    });

    formMigrar.addEventListener('submit', async (e) => {
        e.preventDefault();
        const serverId = serverSelectModal.value;
        const packageId = packageSelectModal.value;

        if (selectedCustomerIds.size === 0) {
            Toast.show('Nenhum cliente selecionado', 'error');
            return;
        }

        if (!serverId && !packageId) {
            Toast.show('Selecione um servidor ou plano', 'error');
            return;
        }

        console.log('Form Migrate Submit: Iniciando migração em lote.'); // DEBUG
        await batchMigrateCustomers(serverId, packageId);
    });

    cancelModalMigrarBtn.addEventListener('click', () => {
        Modal.hide('modal-migrar');
    });

    async function batchMigrateCustomers(serverId, packageId) {
        const customerIds = Array.from(selectedCustomerIds);
        const total = customerIds.length;
        let successCount = 0;
        let failedResults = []; // Para coletar falhas detalhadas

        try {
            Loading.show(`Migrando ${total} cliente(s)...`);
            Loading.updateProgress(0);
            console.log('Batch Migrate Customers: Enviando para /api/batch_migrar.'); // DEBUG

            // Chama a rota de lote no seu backend, que por sua vez chama a API externa individualmente
            const response = await fetch('/api/batch_migrar', { 
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${AUTH_TOKEN}`
                },
                body: JSON.stringify({
                    customer_ids: customerIds,
                    server_id: serverId || null,
                    package_id: packageId || null
                }),
            });

            // Verifica se a resposta do seu backend foi OK
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: response.statusText })); // Tenta ler o erro do seu backend
                console.error('Batch Migrate Customers: Erro do backend na migração em lote:', errorData); // DEBUG
                throw new Error(errorData.detail.message || errorData.detail || 'Erro desconhecido no backend.');
            }

            const data = await response.json(); // Resposta do seu backend (com resultados individuais)
            console.log('Batch Migrate Customers: Resposta do backend:', data); // DEBUG

            // Processa os resultados individuais retornados pelo seu backend
            if (data.results && data.results.length > 0) {
                data.results.forEach(res => {
                    if (res.status === 'success') {
                        successCount++;
                    } else {
                        failedResults.push(res);
                    }
                });
            } else {
                // Se não há "results", mas o status geral é sucesso, assume que todos foram.
                // Isso cobre o caso onde o backend retorna { "message": "Todos migrados com sucesso!" }
                successCount = total; 
            }

            Loading.updateProgress(100);

            // Exibir resultados no modal
            migrarStatusMessage.innerHTML = ''; // Limpa a mensagem antes de adicionar novos resultados
            migrarStatusMessage.classList.remove('success', 'error', 'warning');

            let finalMessage = '';
            let finalType = 'success';

            if (successCount === total) {
                finalMessage = `Todos os ${total} clientes migrados com sucesso!`;
            } else if (successCount > 0 && successCount < total) {
                finalMessage = `${successCount} de ${total} clientes migrados com sucesso. Alguns falharam.`;
                finalType = 'warning';
            } else {
                finalMessage = `Nenhum cliente migrado. Todas as migrações falharam.`;
                finalType = 'error';
            }

            migrarStatusMessage.innerHTML = `<p>${finalMessage}</p>`;
            migrarStatusMessage.classList.add(`message`, finalType);

            if (failedResults.length > 0) {
                migrarStatusMessage.innerHTML += '<h4>Detalhes das Falhas:</h4>';
                let resultsHtml = '<ul>';
                failedResults.forEach(res => {
                    resultsHtml += `<li class="message error"><strong>${res.customer_id}:</strong> ${res.message || 'Erro desconhecido'}</li>`;
                });
                    resultsHtml += '</ul>';
                migrarStatusMessage.innerHTML += resultsHtml;
            }
            
            // Re-busca e fecha modal após um tempo
            setTimeout(async () => {
                Modal.hide('modal-migrar');
                Toast.show(finalMessage, finalType);
                await performSearch(); // Re-busca para atualizar a tabela
                resetSearchSection(); // Limpa seleção e campos de busca
            }, 3000); 
            
        } catch (error) {
            console.error('Erro na migração em lote (catch principal):', error); // DEBUG
            migrarStatusMessage.innerHTML = `<p class="message error">Erro durante a migração: ${error.message || 'Erro desconhecido'}</p>`;
            Toast.show('Erro durante a migração em lote', 'error');
        } finally {
            Loading.hide();
        }
    }

    // --- Inicialização ---
    showLogin(); // Começa mostrando a tela de login
});