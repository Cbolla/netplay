document.addEventListener('DOMContentLoaded', () => {
    // --- Referências aos Elementos HTML ---
    // Seção de Login
    const loginSection = document.getElementById('login-section');
    const panelSection = document.getElementById('panel-section');
    const loginForm = document.getElementById('login-form');
    const loginMessage = document.getElementById('login-message');
    const btnLogout = document.getElementById('btn-logout');

    // Botões Principais do Painel
    const btnTrocarServidor = document.getElementById('btn-trocar-servidor');
    const trocarServidorOptions = document.getElementById('trocar-servidor-options');
    const btnClienteIndividual = document.getElementById('btn-cliente-individual');
    const btnTodosClientes = document.getElementById('btn-todos-clientes'); // Botão placeholder

    // Seção de Busca de Cliente Individual
    const clienteIndividualSection = document.getElementById('cliente-individual-section');
    const searchCustomerForm = document.getElementById('search-customer-form');
    const searchMessage = document.getElementById('search-message');
    const customerDetails = document.getElementById('customer-details');
    const customerData = document.getElementById('customer-data');
    const btnMigrarCliente = document.getElementById('btn-migrar-cliente');

    // Elementos do Modal de Migração
    const modalMigrar = document.getElementById('modal-migrar');
    const closeModalMigrarBtn = document.getElementById('close-modal-migrar');
    const formMigrar = document.getElementById('form-migrar');
    const migrarCustomerIdInput = document.getElementById('migrar-customer-id');
    const serverSelectModal = document.getElementById('server-select-modal'); // ID correspondente ao HTML
    const packageSelectModal = document.getElementById('package-select-modal'); // ID correspondente ao HTML
    const migrarStatusMessage = document.getElementById('migrar-status');

    // --- Variáveis de Estado da Aplicação ---
    let currentCustomerId = null; // Armazena o ID do cliente atualmente selecionado para migração.

    // --- Funções Auxiliares de Visibilidade ---
    // Adiciona a classe 'hidden' para esconder o elemento.
    function show(element) {
        if (element) element.classList.remove('hidden');
    }

    // Remove a classe 'hidden' para mostrar o elemento.
    function hide(element) {
        if (element) element.classList.add('hidden');
    }

    // Reseta o estado de todas as seções para escondê-las e limpa mensagens/formulários.
    function resetAllSections() {
        hide(loginSection);
        hide(panelSection);
        hide(trocarServidorOptions);
        hide(clienteIndividualSection);
        hide(customerDetails);
        hide(modalMigrar); // Garante que o modal esteja escondido
        loginMessage.textContent = '';
        searchMessage.textContent = '';
        migrarStatusMessage.textContent = ''; // Limpa a mensagem de status do modal
        loginForm.reset();
        searchCustomerForm.reset();
        // Resetar os selects do modal para o estado inicial
        serverSelectModal.innerHTML = '<option value="">Selecione um servidor (opcional)</option>';
        packageSelectModal.innerHTML = '<option value="">Selecione um plano (opcional)</option>';
        currentCustomerId = null; // Limpa o ID do cliente selecionado
    }

    // Mostra apenas a seção de login.
    function showLogin() {
        resetAllSections();
        show(loginSection);
    }

    // Mostra apenas o painel principal.
    function showPanel() {
        resetAllSections();
        show(panelSection);
    }

    // --- Gerenciamento de Login ---
    // Adiciona um 'listener' ao formulário de login para lidar com o envio.
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Impede o comportamento padrão de recarregar a página ao enviar o formulário.
        const username = loginForm.username.value;
        const password = loginForm.password.value;

        loginMessage.textContent = 'Autenticando...';
        loginMessage.className = 'message'; // Reseta as classes de estilo da mensagem.

        try {
            // Envia as credenciais para o endpoint de login do backend.
            const response = await fetch('/api/login', {
                method: 'POST', // Método POST para login.
                headers: {
                    'Content-Type': 'application/json', // Indica que o corpo da requisição é JSON.
                },
                body: JSON.stringify({ username, password }), // Converte o objeto JavaScript para uma string JSON.
            });

            const data = await response.json(); // Tenta parsear a resposta como JSON.

            if (response.ok) { // Verifica se o status da resposta é 2xx (sucesso).
                loginMessage.textContent = 'Login bem-sucedido!';
                loginMessage.classList.add('success');
                showPanel(); // Mostra o painel principal após o login.
            } else {
                // Exibe a mensagem de erro vinda do backend ou uma mensagem genérica.
                loginMessage.textContent = data.detail || 'Erro no login. Verifique suas credenciais.';
                loginMessage.classList.add('error');
            }
        } catch (error) {
            console.error('Erro de rede ou servidor:', error);
            loginMessage.textContent = 'Erro ao conectar com o servidor. Verifique se o backend está rodando.';
            loginMessage.classList.add('error');
        }
    });

    // Listener para o botão de logout.
    btnLogout.addEventListener('click', () => {
        alert('Você foi desconectado.');
        showLogin(); // Volta para a tela de login.
    });

    // --- Gerenciamento de Botões do Painel ---
    // Listener para o botão "Trocar clientes de servidor".
    btnTrocarServidor.addEventListener('click', () => {
        // Alterna a visibilidade das opções (Cliente Individual / Todos Clientes).
        if (trocarServidorOptions.classList.contains('hidden')) {
            show(trocarServidorOptions);
            hide(clienteIndividualSection); // Garante que outras seções estejam fechadas.
            hide(customerDetails);
            hide(modalMigrar); // Garante que o modal esteja escondido.
        } else {
            hide(trocarServidorOptions);
        }
    });

    // Listener para o botão "1 - Cliente Individual".
    btnClienteIndividual.addEventListener('click', () => {
        hide(trocarServidorOptions); // Esconde as opções de troca.
        show(clienteIndividualSection); // Mostra a seção de busca de cliente.
        hide(customerDetails); // Garante que detalhes de cliente antigos estejam escondidos.
        hide(modalMigrar); // Garante que o modal esteja escondido.
        searchMessage.textContent = ''; // Limpa mensagens de busca.
        searchCustomerForm.reset(); // Limpa o campo de busca.
        currentCustomerId = null; // Reseta o ID do cliente atual.
    });

    // Listener para o botão "2 - Todos Clientes" (apenas placeholder).
    btnTodosClientes.addEventListener('click', () => {
        alert('Funcionalidade "Todos Clientes" não implementada.');
    });

    // --- Pesquisa de Cliente Individual ---
    // Listener para o formulário de busca de cliente.
    searchCustomerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const accountNumber = searchCustomerForm.elements['account-number'].value;

        searchMessage.textContent = 'Buscando cliente...';
        searchMessage.className = 'message';

        try {
            // Envia a requisição GET para buscar o cliente no backend.
            const response = await fetch(`/api/search_customer?account_number=${accountNumber}`);
            const data = await response.json();

            if (response.ok) {
                if (data.clientes && data.clientes.length > 0) {
                    searchMessage.textContent = `Cliente(s) encontrado(s): ${data.clientes.length}`;
                    searchMessage.classList.add('success');

                    // Para este exemplo, pegamos o primeiro cliente encontrado.
                    const client = data.clientes[0];
                    currentCustomerId = client.id; // Armazena o ID do cliente para uso posterior na migração.
                    migrarCustomerIdInput.value = client.id; // Define o ID no input hidden do modal.

                    // Preenche a div 'customer-data' com os detalhes do cliente formatados.
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
                    show(customerDetails); // Mostra a seção de detalhes do cliente.
                    show(btnMigrarCliente); // Mostra o botão de migrar.
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
    // Listener para o botão "Migrar Cliente" (que abre o modal).
    btnMigrarCliente.addEventListener('click', async () => {
        try {
            const response = await fetch(`/api/customers/${clienteId}`); // use o ID do cliente aqui
            const result = await response.json();
            const data = result.data;

            // Armazena os dados atuais do cliente
            const servidorAtualId = data.server_id;
            const servidorAtualNome = data.server;

            // Mostra no topo do modal
            textoServidorAtual.textContent = `Servidor atual: ${servidorAtualNome}`;

            // Limpa o select de servidores
            serverSelectModal.innerHTML = '';

            // Carrega os servidores disponíveis
            const resServers = await fetch('/api/servers');
            const allServers = await resServers.json();

            allServers.servers.forEach(server => {
                if (server.id !== servidorAtualId) {
                    const option = document.createElement('option');
                    option.value = server.id;
                    option.textContent = server.name;
                    serverSelectModal.appendChild(option);
                }
            });

            // Abre o modal
            modalMigrar.classList.remove('hidden');

            // Guarda o cliente selecionado
            selectedClientId = data.id;

        } catch (error) {
            alert('Erro ao buscar dados do cliente: ' + error.message);
        }
    });


    // Listener para fechar o Modal ao clicar no 'X'.
    closeModalMigrarBtn.addEventListener('click', () => {
        hide(modalMigrar);
        migrarStatusMessage.textContent = ''; // Limpa a mensagem ao fechar.
        formMigrar.reset(); // Reseta o formulário do modal.
    });

    // Listener para fechar o Modal ao clicar fora do conteúdo do modal.
    window.addEventListener('click', (event) => {
        if (event.target == modalMigrar) {
            hide(modalMigrar);
            migrarStatusMessage.textContent = ''; // Limpa a mensagem ao fechar.
            formMigrar.reset(); // Reseta o formulário do modal.
        }
    });

    // Listener para o formulário de migração dentro do modal.
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

        // Validação: Pelo menos um servidor ou plano deve ser selecionado para migrar.
        if (!serverId && !packageId) {
            migrarStatusMessage.textContent = 'Por favor, selecione um servidor ou um plano para migrar.';
            migrarStatusMessage.classList.add('error');
            return;
        }

        migrarStatusMessage.textContent = 'Realizando migração...';
        migrarStatusMessage.className = 'message';

        try {
            // Envia a requisição de migração para o backend.
            const response = await fetch('/api/migrar', {
                method: 'PUT', // O backend espera um PUT para esta rota (definido em main.py).
                headers: {
                    'Content-Type': 'application/json', // O backend espera JSON.
                },
                body: JSON.stringify({
                    customer_id: customerId,
                    server_id: serverId || null, // Envia null se não for selecionado (ou o valor vazio do select)
                    package_id: packageId || null // Envia null se não for selecionado (ou o valor vazio do select)
                }),
            });

            const data = await response.json();

            if (response.ok) {
                migrarStatusMessage.textContent = data.message || 'Migração realizada com sucesso!';
                migrarStatusMessage.classList.add('success');
                hide(modalMigrar); // Esconde o modal após o sucesso.
                // Informa o usuário para buscar novamente para ver as atualizações.
                searchMessage.textContent = 'Migração concluída! Busque o cliente novamente para ver as atualizações.';
                searchMessage.classList.add('success');
                searchCustomerForm.reset(); // Limpa o campo de busca.
                hide(customerDetails); // Esconde os detalhes do cliente antigo.
                currentCustomerId = null; // Reseta o ID do cliente.
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

    // --- Inicialização ---
    // Mostra a tela de login assim que a página é carregada (função showLogin chama resetAllSections).
    showLogin();
});
const btnMigrarCliente = document.querySelector('.btn-migrar');
const modalMigrar = document.getElementById('modal-migrar');
const serverSelectModal = document.getElementById('server-select-modal');
const textoServidorAtual = document.getElementById('texto-servidor-atual');
const btnConfirmarMigracao = document.getElementById('btn-confirmar-migracao');

let selectedClientId = null;

btnMigrarCliente.addEventListener('click', async (e) => {
    const clienteId = e.target.getAttribute('data-id');

    try {
        const response = await fetch(`/api/customers/${clienteId}`);
        const result = await response.json();
        const data = result.data;

        const servidorAtualId = data.server_id;
        const servidorAtualNome = data.server;

        textoServidorAtual.textContent = `Servidor atual: ${servidorAtualNome}`;
        serverSelectModal.innerHTML = '';

        const resServers = await fetch('/api/servers');
        const allServers = await resServers.json();

        allServers.servers.forEach(server => {
            if (server.id !== servidorAtualId) {
                const option = document.createElement('option');
                option.value = server.id;
                option.textContent = server.name;
                serverSelectModal.appendChild(option);
            }
        });

        modalMigrar.classList.remove('hidden');
        selectedClientId = data.id;

    } catch (error) {
        alert('Erro ao buscar dados do cliente: ' + error.message);
    }
});

btnConfirmarMigracao.addEventListener('click', async () => {
    const selectedServerId = serverSelectModal.value;

    try {
        const res = await fetch(`/api/customers/${selectedClientId}/server-migration`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                server_id: selectedServerId
            })
        });

        if (!res.ok) {
            const resData = await res.json();
            throw new Error(resData.detail || 'Erro desconhecido');
        }

        alert('Cliente migrado com sucesso!');
        modalMigrar.classList.add('hidden');

    } catch (error) {
        alert('Erro na migração: ' + error.message);
    }
});
