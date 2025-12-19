// Variáveis globais
let clientInfo = null;
let availableServers = [];
let clientToken = null;
let resellerId = null;

// Elementos DOM (serão definidos no DOMContentLoaded)
let loginSection, migrationSection, clientLoginForm, clientMigrationForm;
let loadingOverlay, loadingMessage, loginMessage, migrationMessage;
let migrationModal, confirmMigrationBtn, cancelMigrationBtn;
let btnClientLogout, newServerSelect, clientUsername, clientPassword;

// Elementos de exibição de informações
const displayUsername = document.getElementById('display-username');
const displayCurrentServer = document.getElementById('display-current-server');
const displayPackage = document.getElementById('display-package');

// Função para processar credenciais da URL e detectar reseller_id
function processUrlCredentials() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    // Detecta reseller_id do atributo data no body
    const bodyElement = document.body;
    if (bodyElement.hasAttribute('data-reseller-id')) {
        resellerId = parseInt(bodyElement.getAttribute('data-reseller-id'));

        // Ajustar UI para modo revenda
        document.title = 'Login IPTV | Netplay RPA';
        const header = document.querySelector('.card-header h2');
        if (header) {
            header.innerHTML = `<i class="fas fa-tv"></i> Login IPTV`;
        }
    }

    if (token) {
        try {
            clientToken = token;
            // Login automático
            setTimeout(() => {
                handleTokenLogin();
            }, 500);

            // Limpar URL
            const newUrl = window.location.origin + window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
        } catch (error) {
            console.error('Erro ao processar token:', error);
        }
    }
}

// Funções utilitárias
function showLoading(message = 'Processando...') {
    if (loadingMessage) loadingMessage.textContent = message;
    if (loadingOverlay) loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    if (loadingOverlay) loadingOverlay.classList.add('hidden');
}

function hideMessage(element) {
    if (element) element.classList.add('hidden');
}

// Função para fazer requisições à API
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

// Função para carregar servidores disponíveis
async function loadServers() {
    try {
        const response = await fetch('/api/client/servers');
        if (response.ok) {
            const data = await response.json();
            availableServers = data.servers || [];
            populateServerSelect();
        } else {
            console.error('Erro ao carregar servidores');
        }
    } catch (error) {
        console.error('Erro ao carregar servidores:', error);
    }
}

// Função para popular o select de servidores
function populateServerSelect() {
    if (!newServerSelect) return;

    newServerSelect.innerHTML = '<option value="">Selecione um servidor...</option>';

    availableServers.forEach(server => {
        if (clientInfo && server.id !== clientInfo.server_id) {
            const option = document.createElement('option');
            option.value = server.id;
            option.textContent = server.name;
            newServerSelect.appendChild(option);
        }
    });
}

// Função de login do cliente
async function handleClientLogin(event) {
    event.preventDefault();

    const formData = new FormData(clientLoginForm);
    const loginData = {
        username: formData.get('username')
    };

    if (clientToken) loginData.token = clientToken;
    if (resellerId) loginData.reseller_id = resellerId;

    if (!loginData.username) {
        alert('Por favor, digite o número de usuário.');
        return;
    }

    showLoading('Verificando credenciais...');

    try {
        const response = await apiRequest('/api/client/login', {
            method: 'POST',
            body: JSON.stringify(loginData)
        });

        if (response.success) {
            clientInfo = response.client_info;

            if (response.netplay_token) clientInfo.netplay_token = response.netplay_token;
            else if (response.token) clientInfo.system_token = response.token;

            if (response.reseller_id) clientInfo.reseller_id = response.reseller_id;

            showClientInterface();
            await loadServers();
        } else {
            alert('Falha na autenticação.');
        }
    } catch (error) {
        alert(error.message || 'Erro ao fazer login.');
    } finally {
        hideLoading();
    }
}

// Função para fazer login usando token
async function handleTokenLogin() {
    if (!clientToken) return;

    showLoading('Fazendo login...');

    try {
        const response = await fetch('/api/client/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: clientToken })
        });

        if (response.ok) {
            const data = await response.json();
            clientInfo = data.client_info;
            await loadServers();
            showClientInterface();
        }
    } catch (error) {
        console.error('Erro login token:', error);
    } finally {
        hideLoading();
    }
}

// Função para mostrar a interface do cliente
function showClientInterface() {
    if (loginSection) loginSection.classList.add('hidden');
    if (migrationSection) migrationSection.classList.remove('hidden');

    if (displayUsername && clientInfo) displayUsername.textContent = clientInfo.username;
    if (displayCurrentServer && clientInfo) displayCurrentServer.textContent = clientInfo.server_name || 'N/A';
    if (displayPackage && clientInfo) displayPackage.textContent = clientInfo.package_name || 'N/A';

    populateServerSelect();
}

// Função para mostrar modal de confirmação
function showConfirmationModal() {
    return new Promise((resolve, reject) => {
        if (!migrationModal) {
            if (confirm('Tem certeza que deseja migrar para este servidor?')) resolve(true);
            else reject(new Error('Cancelado'));
            return;
        }

        migrationModal.classList.add('show');

        const handleConfirm = () => {
            cleanup();
            resolve(true);
        };

        const handleCancel = () => {
            cleanup();
            reject(new Error('Cancelado'));
        };

        const cleanup = () => {
            migrationModal.classList.remove('show');
            confirmMigrationBtn.removeEventListener('click', handleConfirm);
            cancelMigrationBtn.removeEventListener('click', handleCancel);
        };

        confirmMigrationBtn.addEventListener('click', handleConfirm);
        cancelMigrationBtn.addEventListener('click', handleCancel);
    });
}

// Função para migração do cliente
async function handleClientMigration(event) {
    event.preventDefault();

    const formData = new FormData(clientMigrationForm);
    const serverId = formData.get('server_id');

    if (!serverId) {
        alert('Por favor, selecione um servidor.');
        return;
    }

    try {
        await showConfirmationModal();
        showLoading('Migrando servidor...');
    } catch (error) {
        return;
    }

    try {
        let migrateUrl = '/api/client/migrate';
        let migrateParams = new URLSearchParams();

        if (clientInfo.netplay_token) migrateParams.append('netplay_token', clientInfo.netplay_token);
        else if (clientInfo.system_token) migrateParams.append('token', clientInfo.system_token);
        else if (clientToken) migrateParams.append('token', clientToken);

        if (clientInfo.reseller_id) migrateParams.append('reseller_id', clientInfo.reseller_id);
        else if (resellerId) migrateParams.append('reseller_id', resellerId);

        const requestBody = { server_id: serverId };

        // Ler checkbox MaxPlayer
        const includeMaxplayer = document.getElementById('client-include-maxplayer')?.checked || false;
        requestBody.include_maxplayer = includeMaxplayer;

        if (clientInfo.reseller_id || resellerId) {
            requestBody.client_username = clientInfo.username;
        }

        const response = await apiRequest(`${migrateUrl}?${migrateParams.toString()}`, {
            method: 'POST',
            body: JSON.stringify(requestBody)
        });

        if (response.success) {
            let successMessage = response.message || 'Migração realizada com sucesso!';

            if (response.maxplayer_status) {
                successMessage += `\n\n📺 MaxPlayer: ${response.maxplayer_status}`;
            }

            alert(successMessage);

            setTimeout(() => {
                alert('💡 Dica: Reinicie a TV da tomada ou feche e abra o App para puxar as atualizações.');
            }, 3000);

            clientInfo.server_id = serverId;
            const selectedServer = availableServers.find(s => s.id === serverId);
            const serverName = selectedServer ? selectedServer.name : 'Novo Servidor';
            clientInfo.server_name = serverName;
            displayCurrentServer.textContent = serverName;

            populateServerSelect();
            clientMigrationForm.reset();
        } else {
            alert('Falha na migração.');
        }
    } catch (error) {
        alert(error.message || 'Erro ao migrar servidor.');
    } finally {
        hideLoading();
    }
}

// Função de logout
function handleClientLogout() {
    clientInfo = null;
    availableServers = [];
    clientLoginForm.reset();
    clientMigrationForm.reset();
    migrationSection.classList.add('hidden');
    loginSection.classList.remove('hidden');
}

// Função para buscar e exibir status dos servidores
async function fetchServerStatus() {
    const indicatorsContainer = document.getElementById('client-servers-indicators');
    const refreshButton = document.getElementById('client-refresh-servers-status');
    const lastUpdateEl = document.querySelector('.status-last-update');

    if (!indicatorsContainer) return;

    if (refreshButton) {
        const icon = refreshButton.querySelector('i');
        if (icon) icon.classList.add('fa-spin');
    }

    try {
        const response = await fetch('/api/servers/status');
        if (response.ok) {
            const data = await response.json();

            // NORMALIZAÇÃO DE DADOS (Objeto -> Array)
            let serversList = [];
            if (Array.isArray(data.servers)) {
                serversList = data.servers;
            } else if (typeof data.servers === 'object' && data.servers !== null) {
                serversList = Object.entries(data.servers).map(([key, value]) => {
                    if (typeof value === 'object') return { name: key, ...value };
                    return { name: key, status: value };
                });
            }

            // Flag de checagem client-side (vinda do backend ou inferida se tiver URL e sem status)
            const shouldCheckClientSide = data.client_side_check || (serversList.length > 0 && serversList[0].url && !serversList[0].status);

            if (shouldCheckClientSide && serversList.length > 0) {
                // Renderizar inicialmente como "verificando"
                const initialServers = serversList.map(s => ({
                    ...s,
                    status: s.status || 'checking',
                    latency: s.latency || '',
                    url: s.url || ''
                }));

                renderServerStatus(initialServers, indicatorsContainer);

                // Verificar cada servidor em paralelo (se tiver URL) e atualizar individualmente
                serversList.forEach(async (server) => {
                    if (!server.url) return;

                    const statusData = await checkServerConnectivity(server.url);
                    updateServerIndicator(server.name, statusData);
                });

                // Atualizar hora
                const now = new Date();
                const timeString = now.toLocaleTimeString('pt-BR');
                if (lastUpdateEl) lastUpdateEl.textContent = `Atualizado às ${timeString}`;

            } else {
                // Modo server-side antigo ou cacheado
                renderServerStatus(serversList, indicatorsContainer);

                if (lastUpdateEl && data.last_check) {
                    lastUpdateEl.textContent = `Atualizado às ${data.last_check}`;
                }
            }
        }
    } catch (error) {
        console.error('Erro ao buscar status:', error);
    } finally {
        if (refreshButton) {
            setTimeout(() => {
                const icon = refreshButton.querySelector('i');
                if (icon) icon.classList.remove('fa-spin');
            }, 500);
        }
    }
}

// Função auxiliar para checar conectividade
async function checkServerConnectivity(url) {
    if (!url) return { status: 'offline', latency: '-' };
    const startTime = Date.now();
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 8000); // 8 segundos timeout

        await fetch(url, {
            method: 'HEAD',
            mode: 'no-cors',
            cache: 'no-cache',
            signal: controller.signal
        });

        clearTimeout(timeoutId);
        const latency = Date.now() - startTime;
        return { status: 'online', latency: `${latency}ms` };
    } catch (e) {
        return { status: 'offline', latency: '-' };
    }
}

// Atualiza apenas um indicador na interface
function updateServerIndicator(name, statusData) {
    const indicatorsContainer = document.getElementById('client-servers-indicators');
    if (!indicatorsContainer) return;

    const indicators = Array.from(indicatorsContainer.children);
    const target = indicators.find(el => el.querySelector('.server-indicator-name').textContent === name);

    if (target) {
        const dot = target.querySelector('.server-indicator-dot');

        // Define classe baseada no status
        let statusClass = 'offline';
        if (statusData.status === 'online' || statusData.status === true) statusClass = 'online';
        else if (statusData.status === 'checking') statusClass = 'checking';

        // Atualizar classes
        dot.className = `server-indicator-dot ${statusClass}`;

        // Remover estilos inline de animação se não estiver checando
        if (statusClass !== 'checking') {
            dot.style.animation = 'none';
            dot.style.opacity = '1';
            dot.style.backgroundColor = '';
        }

        const latencyText = statusData.latency && statusData.latency !== '-' ? ` (${statusData.latency})` : '';
        const statusText = statusClass === 'online' ? 'Online' : 'Offline';
        target.title = `${name}: ${statusText}${latencyText}`;
    }
}

function renderServerStatus(servers, container) {
    container.innerHTML = '';

    if (!servers || servers.length === 0) {
        container.innerHTML = '<span class="status-empty">Nenhum servidor monitorado</span>';
        return;
    }

    servers.forEach(server => {
        let status = server.status || 'unknown';
        let statusClass = 'offline';
        let statusText = 'Offline';

        if (status === 'checking') {
            statusClass = 'checking';
            statusText = '...';
        } else if (status === 'online' || status === true || String(status).toLowerCase() === 'online') {
            statusClass = 'online';
            statusText = 'Online';
        }

        const indicator = document.createElement('div');
        indicator.className = 'server-indicator';

        const latencyText = server.latency ? ` (${server.latency})` : '';
        indicator.title = `${server.name}: ${statusText}${latencyText}`;

        // Estilo inline para checking se não tiver CSS classe
        let dotStyle = '';
        if (statusClass === 'checking') {
            dotStyle = 'opacity: 0.5; animation: pulse 1s infinite; background-color: orange;';
        }

        indicator.innerHTML = `
            <div class="server-indicator-dot ${statusClass}" style="${dotStyle}"></div>
            <span class="server-indicator-name">${server.name}</span>
        `;

        container.appendChild(indicator);
    });
}

// Inicialização
document.addEventListener('DOMContentLoaded', function () {
    loginSection = document.getElementById('login-section');
    migrationSection = document.getElementById('migration-section');
    clientLoginForm = document.getElementById('client-login-form');
    clientMigrationForm = document.getElementById('client-migration-form');
    loadingOverlay = document.getElementById('loading-overlay');
    loadingMessage = document.querySelector('.loading-message');
    loginMessage = document.getElementById('login-message');
    migrationMessage = document.getElementById('migration-message');
    migrationModal = document.getElementById('migration-modal');
    confirmMigrationBtn = document.getElementById('confirm-migration-btn');
    cancelMigrationBtn = document.getElementById('cancel-migration-btn');
    btnClientLogout = document.getElementById('btn-client-logout');
    newServerSelect = document.getElementById('new-server-select');
    clientUsername = document.getElementById('client-username');
    clientPassword = document.getElementById('client-password');

    if (clientLoginForm) clientLoginForm.addEventListener('submit', handleClientLogin);
    if (clientMigrationForm) clientMigrationForm.addEventListener('submit', handleClientMigration);
    if (btnClientLogout) btnClientLogout.addEventListener('click', handleClientLogout);

    const refreshBtn = document.getElementById('client-refresh-servers-status');
    if (refreshBtn) refreshBtn.addEventListener('click', fetchServerStatus);

    processUrlCredentials();
    setTimeout(fetchServerStatus, 1000);
    setInterval(fetchServerStatus, 60000);
});
