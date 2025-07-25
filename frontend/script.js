document.addEventListener('DOMContentLoaded', () => {
    // --- Elementos HTML ---
    const loginSection = document.getElementById('login-section');
    const panelSection = document.getElementById('panel-section');
    const loginForm = document.getElementById('login-form');
    const loginMessage = document.getElementById('login-message');
    const btnLogout = document.getElementById('btn-logout');

    const btnTrocarServidor = document.getElementById('btn-trocar-servidor');
    const trocarServidorOptions = document.getElementById('trocar-servidor-options');
    const btnClienteIndividual = document.getElementById('btn-cliente-individual');
    const btnTodosClientes = document.getElementById('btn-todos-clientes');

    const clienteIndividualSection = document.getElementById('cliente-individual-section');
    const searchCustomerForm = document.getElementById('search-customer-form');
    const searchMessage = document.getElementById('search-message');
    const customerDetails = document.getElementById('customer-details');
    const customerData = document.getElementById('customer-data');
    const btnMigrarCliente = document.getElementById('btn-migrar-cliente');

    const modalMigrar = document.getElementById('modal-migrar');
    const closeModalMigrarBtn = document.getElementById('close-modal-migrar');
    const formMigrar = document.getElementById('form-migrar');
    const migrarCustomerIdInput = document.getElementById('migrar-customer-id');
    const serverSelectModal = document.getElementById('server-select-modal');
    const packageSelectModal = document.getElementById('package-select-modal');
    const migrarStatusMessage = document.getElementById('migrar-status');

    // --- Variáveis de Estado ---
    let currentCustomerId = null;

    // --- Funções de Visibilidade ---
    function show(element) {
        if (element) element.classList.remove('hidden');
    }

    function hide(element) {
        if (element) element.classList.add('hidden');
    }

    function resetAllSections() {
        hide(loginSection);
        hide(panelSection);
        hide(trocarServidorOptions);
        hide(clienteIndividualSection);
        hide(customerDetails);
        hide(modalMigrar);
        loginMessage.textContent = '';
        searchMessage.textContent = '';
        migrarStatusMessage.textContent = '';
        loginForm.reset();
        searchCustomerForm.reset();
        serverSelectModal.innerHTML = '<option value="">Selecione um servidor (opcional)</option>';
        packageSelectModal.innerHTML = '<option value="">Selecione um plano (opcional)</option>';
        currentCustomerId = null;
    }

    function showLogin() {
        resetAllSections();
        show(loginSection);
    }

    function showPanel() {
        resetAllSections();
        show(panelSection);
    }

    // --- Gerenciamento de Login ---
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = loginForm.username.value;
        const password = loginForm.password.value;

        loginMessage.textContent = 'Autenticando...';
        loginMessage.className = 'message';

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json();

            if (response.ok) {
                loginMessage.textContent = 'Login bem-sucedido!';
                loginMessage.classList.add('success');
                showPanel();
            } else {
                loginMessage.textContent = data.detail || 'Erro no login. Verifique suas credenciais.';
                loginMessage.classList.add('error');
            }
        } catch (error) {
            console.error('Erro de rede ou servidor:', error);
            loginMessage.textContent = 'Erro ao conectar com o servidor. Verifique se o backend está rodando.';
            loginMessage.classList.add('error');
        }
    });

    btnLogout.addEventListener('click', () => {
        alert('Você foi desconectado.');
        showLogin();
    });

    // --- Gerenciamento de Botões do Painel ---
    btnTrocarServidor.addEventListener('click', () => {
        if (trocarServidorOptions.classList.contains('hidden')) {
            show(trocarServidorOptions);
            hide(clienteIndividualSection);
            hide(customerDetails);
            hide(modalMigrar);
        } else {
            hide(trocarServidorOptions);
        }
    });

    btnClienteIndividual.addEventListener('click', () => {
        hide(trocarServidorOptions);
        show(clienteIndividualSection);
        hide(customerDetails);
        hide(modalMigrar);
        searchMessage.textContent = '';
        searchCustomerForm.reset();
        currentCustomerId = null;
    });

    btnTodosClientes.addEventListener('click', () => {
        alert('Funcionalidade "Todos Clientes" não implementada.');
    });

    // --- Pesquisa de Cliente Individual ---
    searchCustomerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const accountNumber = searchCustomerForm.elements['account-number'].value;

        searchMessage.textContent = 'Buscando cliente...';
        searchMessage.className = 'message';

        try {
            const response = await fetch(`/api/search_customer?account_number=${accountNumber}`);
            const data = await response.json();

            if (response.ok) {
                if (data.clientes && data.clientes.length > 0) {
                    searchMessage.textContent = `Cliente(s) encontrado(s): ${data.clientes.length}`;
                    searchMessage.classList.add('success');

                    const client = data.clientes[0];
                    currentCustomerId = client.id;
                    migrarCustomerIdInput.value = client.id;

                    customerData.innerHTML = `
                        <div class="cliente-box">
                            <p><strong>ID:</strong> ${client.id}</p>
                            <p><strong>Nome:</strong> ${client.name}</p>
                            <p><strong>Username:</strong> ${client.username}</p>
                            <p><strong>Servidor:</strong> ${client.server}</p>
                            <p><strong>Plano:</strong> ${client.package}</p>
                            <p><strong>Vencimento:</strong> ${client.vencimento}</p>
                            <p><strong>Status:</strong> ${client.status}</p>
                        </div>
                    `;
                    show(customerDetails);
                    show(btnMigrarCliente);
                } else {
                    searchMessage.textContent = 'Nenhum cliente encontrado com este número de conta.';
                    searchMessage.classList.add('error');
                    hide(customerDetails);
                    hide(btnMigrarCliente);
                    currentCustomerId = null;
                }
            } else {
                searchMessage.textContent = data.detail || 'Erro ao buscar cliente.';
                searchMessage.classList.add('error');
                hide(customerDetails);
                hide(btnMigrarCliente);
                currentCustomerId = null;
            }
        } catch (error) {
            console.error('Erro de rede ou servidor:', error);
            searchMessage.textContent = 'Erro ao conectar com o servidor para buscar cliente. Verifique se o backend está rodando.';
            searchMessage.classList.add('error');
            hide(customerDetails);
            hide(btnMigrarCliente);
            currentCustomerId = null;
        }
    });

    // --- Funcionalidade de Migração via Modal ---
    btnMigrarCliente.addEventListener('click', async () => {
        if (!currentCustomerId) {
            alert('Nenhum cliente selecionado para migrar.');
            return;
        }

        migrarStatusMessage.textContent = 'Carregando opções de migração...';
        migrarStatusMessage.className = 'message';

        serverSelectModal.innerHTML = '<option value="">Selecione um servidor (opcional)</option>';
        packageSelectModal.innerHTML = '<option value="">Selecione um plano (opcional)</option>';

        try {
            // UNIFICADO: Chama apenas a rota de servidores_e_planos
            const response = await fetch('/api/servidores_e_planos'); // Nova rota no backend
            const data = await response.json();

            if (response.ok) {
                // Preenche o select de servidores
                if (data.servers && data.servers.length > 0) {
                    data.servers.forEach(server => {
                        const option = document.createElement('option');
                        option.value = server.id;
                        option.textContent = server.name;
                        serverSelectModal.appendChild(option);
                    });
                } else {
                    serverSelectModal.innerHTML = '<option value="">Nenhum servidor disponível</option>';
                }

                // Preenche o select de planos
                if (data.packages && data.packages.length > 0) {
                    data.packages.forEach(pkg => {
                        const option = document.createElement('option');
                        option.value = pkg.id;
                        option.textContent = pkg.name;
                        packageSelectModal.appendChild(option);
                    });
                } else {
                    packageSelectModal.innerHTML = '<option value="">Nenhum plano disponível</option>';
                }

                migrarStatusMessage.textContent = 'Opções de migração carregadas. Selecione e confirme.';
                migrarStatusMessage.classList.add('success');
                show(modalMigrar); // Exibe o modal
            } else {
                migrarStatusMessage.textContent = data.detail || 'Erro ao carregar opções de migração.';
                migrarStatusMessage.classList.add('error');
                hide(modalMigrar);
            }

        } catch (error) {
            console.error('Erro ao carregar opções de migração:', error);
            migrarStatusMessage.textContent = 'Erro ao carregar opções de migração. Verifique sua conexão ou backend.';
            migrarStatusMessage.classList.add('error');
            hide(modalMigrar);
        }
    });

    closeModalMigrarBtn.addEventListener('click', () => {
        hide(modalMigrar);
        migrarStatusMessage.textContent = '';
        formMigrar.reset();
    });

    window.addEventListener('click', (event) => {
        if (event.target == modalMigrar) {
            hide(modalMigrar);
            migrarStatusMessage.textContent = '';
            formMigrar.reset();
        }
    });

    formMigrar.addEventListener('submit', async (e) => {
        e.preventDefault();
        const customerId = migrarCustomerIdInput.value;
        const serverId = serverSelectModal.value;
        const packageId = packageSelectModal.value;

        if (!customerId) {
            migrarStatusMessage.textContent = 'Erro: Nenhum cliente selecionado para migrar.';
            migrarStatusMessage.classList.add('error');
            return;
        }

        // Permitir migrar apenas servidor OU apenas plano OU ambos
        if (!serverId && !packageId) {
            migrarStatusMessage.textContent = 'Por favor, selecione um servidor ou um plano para migrar.';
            migrarStatusMessage.classList.add('error');
            return;
        }

        migrarStatusMessage.textContent = 'Realizando migração...';
        migrarStatusMessage.className = 'message';

        try {
            const response = await fetch('/api/migrar', {
                method: 'PUT', // O backend espera PUT para a migração
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    customer_id: customerId,
                    server_id: serverId || null,
                    package_id: packageId || null
                }),
            });

            const data = await response.json();

            if (response.ok) {
                migrarStatusMessage.textContent = data.message || 'Migração realizada com sucesso!';
                migrarStatusMessage.classList.add('success');
                hide(modalMigrar);
                searchMessage.textContent = 'Migração concluída! Busque o cliente novamente para ver as atualizações.';
                searchMessage.classList.add('success');
                searchCustomerForm.reset();
                hide(customerDetails);
                currentCustomerId = null;
            } else {
                migrarStatusMessage.textContent = data.detail || 'Erro na migração.';
                migrarStatusMessage.classList.add('error');
            }
        } catch (error) {
            console.error('Erro de rede ou servidor na migração:', error);
            migrarStatusMessage.textContent = 'Erro ao conectar com o servidor para migrar. Verifique sua conexão.';
            migrarStatusMessage.classList.add('error');
        }
    });

    showLogin();
});