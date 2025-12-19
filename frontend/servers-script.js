// Lista de servidores para monitorar
const SERVERS = [
    { name: 'SEVEN', url: 'http://vr766.com:80' },
    { name: 'GALAXY', url: 'http://galaxy.netpl4y.com' },
    { name: 'LUNAR', url: 'http://lunar.netpl4y.com' },
    { name: 'SPEED', url: 'http://obix.fun' },
    { name: 'OLYMPUS', url: 'http://olympus.netpl4y.com' },
    { name: 'EXPLOSION', url: 'http://explosion.netpl4y.com' },
    { name: 'TITA', url: 'http://tita.netpl4y.com' },
    { name: 'SKY', url: 'http://facilita.fun:80' },
    { name: 'SOLAR', url: 'http://solar.netpl4y.com' },
    { name: 'URANO', url: 'http://cdn.ofmp.site' },
    { name: 'ATENA', url: 'http://dns.whsv.top:80' },
    { name: 'ANDROMEDA', url: 'http://socio.gp4.fun' },
    { name: 'HADES', url: 'http://hades.netpl4y.com' },
    { name: 'VENUS', url: 'http://venus.netpl4y.com' },
    { name: 'FIRE', url: 'http://fire.netpl4y.com' }
];

// Estado da aplicação
let serversStatus = {};
let isRefreshing = false;

// Elementos DOM
const serversGrid = document.getElementById('servers-grid');
const onlineCount = document.getElementById('online-count');
const offlineCount = document.getElementById('offline-count');
const lastUpdateTime = document.getElementById('last-update-time');
const refreshBtn = document.getElementById('refresh-btn');
const loadingOverlay = document.getElementById('loading-overlay');

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    renderServers();
    checkServersStatus();

    // Auto-refresh a cada 30 segundos
    setInterval(checkServersStatus, 30000);

    // Botão de refresh manual
    refreshBtn.addEventListener('click', () => {
        if (!isRefreshing) {
            checkServersStatus();
        }
    });
});

// Renderizar cards dos servidores
function renderServers() {
    serversGrid.innerHTML = '';

    SERVERS.forEach(server => {
        const card = createServerCard(server);
        serversGrid.appendChild(card);
    });
}

// Criar card de servidor
function createServerCard(server) {
    const card = document.createElement('div');
    card.className = 'server-card';
    card.id = `server-${server.name.toLowerCase()}`;

    card.innerHTML = `
        <div class="server-header">
            <div class="server-name">
                <div class="status-indicator checking"></div>
                ${server.name}
            </div>
        </div>
        <div class="server-url">${server.url}</div>
        <div class="server-status checking">
            <i class="fas fa-spinner fa-spin"></i>
            Verificando...
        </div>
    `;

    return card;
}

// Verificar status de todos os servidores
async function checkServersStatus() {
    if (isRefreshing) return;

    isRefreshing = true;
    showLoading();

    // Animar botão de refresh
    refreshBtn.querySelector('i').classList.add('fa-spin');

    try {
        const response = await fetch('/api/servers/status');
        const data = await response.json();

        if (data.success) {
            serversStatus = data.servers;
            updateServerCards();
            updateStats();
            updateLastUpdateTime();
        }
    } catch (error) {
        console.error('Erro ao verificar status dos servidores:', error);
        showError();
    } finally {
        // Removido hideLoading()
        refreshBtn.querySelector('i').classList.remove('fa-spin');
        isRefreshing = false;
    }
}

// Atualizar cards com status
function updateServerCards() {
    SERVERS.forEach(server => {
        const card = document.getElementById(`server-${server.name.toLowerCase()}`);
        if (!card) return;

        const status = serversStatus[server.name];
        const indicator = card.querySelector('.status-indicator');
        const statusDiv = card.querySelector('.server-status');

        if (status && status.online) {
            // Online
            indicator.className = 'status-indicator online';
            statusDiv.className = 'server-status online';
            statusDiv.innerHTML = '<i class="fas fa-check-circle"></i> Online';
        } else {
            // Offline
            indicator.className = 'status-indicator offline';
            statusDiv.className = 'server-status offline';
            statusDiv.innerHTML = '<i class="fas fa-times-circle"></i> Offline';
        }
    });
}

// Atualizar estatísticas
function updateStats() {
    let online = 0;
    let offline = 0;

    Object.values(serversStatus).forEach(status => {
        if (status.online) {
            online++;
        } else {
            offline++;
        }
    });

    onlineCount.textContent = online;
    offlineCount.textContent = offline;
}

// Atualizar hora da última atualização
function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    lastUpdateTime.textContent = timeString;
}

// Mostrar loading
function showLoading() {
    loadingOverlay.classList.remove('hidden');
}

// Esconder loading
function hideLoading() {
    loadingOverlay.classList.add('hidden');
}

// Mostrar erro
function showError() {
    SERVERS.forEach(server => {
        const card = document.getElementById(`server-${server.name.toLowerCase()}`);
        if (!card) return;

        const indicator = card.querySelector('.status-indicator');
        const statusDiv = card.querySelector('.server-status');

        indicator.className = 'status-indicator offline';
        statusDiv.className = 'server-status offline';
        statusDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Erro ao verificar';
    });
}
