// Variáveis globais
let clientInfo = null;
let availableServers = [];
let clientToken = null;

// Variável global para reseller_id
let resellerId = null;

// Função para processar credenciais da URL e detectar reseller_id
function processUrlCredentials() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    // Detecta reseller_id do atributo data no body
    const bodyElement = document.body;
    if (bodyElement.hasAttribute('data-reseller-id')) {
        resellerId = parseInt(bodyElement.getAttribute('data-reseller-id'));
        const resellerName = bodyElement.getAttribute('data-reseller-name');
        
        // Manter título fixo
        document.title = 'Login IPTV | Netplay RPA';
        
        // Manter cabeçalho fixo
        const header = document.querySelector('.card-header h2');
        if (header) {
            header.innerHTML = `<i class="fas fa-tv"></i> Login IPTV`;
        }
        
        console.log('Reseller ID detectado:', resellerId);
        return true;
    }
    
    if (token) {
        try {
            // Armazena o token
            clientToken = token;
            
            // Faz login automaticamente usando o token
            setTimeout(() => {
                try {
                    handleTokenLogin();
                } catch (error) {
                    alert('Erro ao fazer login automático.');
                }
            }, 500);
            
            // Remove o parâmetro da URL para segurança
            const newUrl = window.location.origin + window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
            
            return true;
        } catch (error) {
            alert('Link inválido ou expirado.');
        }
    }
    return false;
}

// Elementos DOM (serão definidos no DOMContentLoaded)
let loginSection, migrationSection, clientLoginForm, clientMigrationForm;
let loadingOverlay, loadingMessage, loginMessage, migrationMessage;
let migrationModal, confirmMigrationBtn, cancelMigrationBtn;
let btnClientLogout, newServerSelect, clientUsername, clientPassword;

// Elementos de exibição de informações
const displayUsername = document.getElementById('display-username');
const displayCurrentServer = document.getElementById('display-current-server');
const displayPackage = document.getElementById('display-package');

// Elementos do modal de confirmação (definidos no DOMContentLoaded)

// Funções utilitárias
function showLoading(message = 'Processando...') {
    loadingMessage.textContent = message;
    loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    loadingOverlay.classList.add('hidden');
}

function showMessage(element, message, type = 'info') {
    element.textContent = message;
    element.className = `message ${type}`;
    element.classList.remove('hidden');
    
    // Auto-hide após 5 segundos para mensagens de sucesso
    if (type === 'success') {
        setTimeout(() => {
            element.classList.add('hidden');
        }, 5000);
    }
}

function hideMessage(element) {
    element.classList.add('hidden');
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
            throw new Error('Erro ao carregar servidores');
        }
    } catch (error) {
        alert('Erro ao carregar servidores disponíveis.');
    }
}

// Função para popular o select de servidores
function populateServerSelect() {
    if (!newServerSelect) {
        console.error('Elemento newServerSelect não encontrado!');
        return;
    }
    
    newServerSelect.innerHTML = '<option value="">Selecione um servidor...</option>';
    
    availableServers.forEach(server => {
        // Não mostrar o servidor atual como opção
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
    
    // Se há um token na URL, inclui no login para validar se o cliente pertence ao revendedor
    if (clientToken) {
        loginData.token = clientToken;
    }
    
    // Se há um reseller_id, inclui no login
    if (resellerId) {
        loginData.reseller_id = resellerId;
    }
    
    if (!loginData.username) {
        alert('Por favor, digite o número de usuário.');
        return;
    }
    
    // Se não há senha, remove do objeto
    if (!loginData.password) {
        delete loginData.password;
    }
    
    showLoading('Verificando credenciais...');
    hideMessage(loginMessage);
    
    try {
        const response = await apiRequest('/api/client/login', {
            method: 'POST',
            body: JSON.stringify(loginData)
        });
        
        if (response.success) {
            clientInfo = response.client_info;
            
            // Armazena o token, netplay_token ou reseller_id para uso na migração
        if (response.netplay_token) {
            clientInfo.netplay_token = response.netplay_token;
        } else if (response.token) {
            clientInfo.system_token = response.token;
        }
        
        if (response.reseller_id) {
            clientInfo.reseller_id = response.reseller_id;
        }
            
            showClientInterface();
            await loadServers();
        } else {
            alert('Falha na autenticação. Verifique suas credenciais.');
        }
    } catch (error) {
        alert(error.message || 'Erro ao fazer login.');
    } finally {
        hideLoading();
    }
}

// Função para fazer login usando token
async function handleTokenLogin() {
    if (!clientToken) {
        alert('Token de acesso não encontrado.');
        return;
    }
    
    showLoading('Fazendo login...');
    
    try {
        const response = await fetch('/api/client/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ token: clientToken })
        });
        
        if (response.ok) {
            const data = await response.json();
            clientInfo = data.client_info;
            await loadServers();
            showClientInterface();
        } else {
            const errorData = await response.json();
            alert(errorData.detail || 'Erro no login.');
        }
    } catch (error) {
        alert('Erro de conexão.');
    } finally {
        hideLoading();
    }
}

// Função para mostrar a interface do cliente
function showClientInterface() {
    if (loginSection) {
        loginSection.classList.add('hidden');
    }
    
    if (migrationSection) {
        migrationSection.classList.remove('hidden');
    }
    
    // Preencher informações do cliente
    if (displayUsername && clientInfo) {
        displayUsername.textContent = clientInfo.username;
    }
    
    if (displayCurrentServer && clientInfo) {
        displayCurrentServer.textContent = clientInfo.server_name || 'N/A';
    }
    
    if (displayPackage && clientInfo) {
        displayPackage.textContent = clientInfo.package_name || 'N/A';
    }
    
    populateServerSelect();
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
    
    const selectedServer = availableServers.find(s => s.id === serverId);
    const serverName = selectedServer ? selectedServer.name : 'servidor selecionado';
    
    try {
        // Solicitar confirmação para migração usando modal
        await showConfirmationModal();
        
        // Só mostrar loading após confirmação
        showLoading('Migrando servidor...');
    } catch (error) {
        return;
    }
    
    try {
        // Determina qual token usar para migração
        let migrateUrl = '/api/client/migrate';
        let migrateParams = new URLSearchParams();
        
        if (clientInfo.netplay_token) {
            // Login direto com credenciais da Netplay
            migrateParams.append('netplay_token', clientInfo.netplay_token);
        } else if (clientInfo.system_token) {
            // Login via link do revendedor
            migrateParams.append('token', clientInfo.system_token);
        } else if (clientToken) {
            // Fallback para token da URL
            migrateParams.append('token', clientToken);
        }
        
        // Se há reseller_id, inclui nos parâmetros
        if (clientInfo.reseller_id) {
            migrateParams.append('reseller_id', clientInfo.reseller_id);
        } else if (resellerId) {
            migrateParams.append('reseller_id', resellerId);
        }
        
        // Prepara o body da requisição
        const requestBody = { server_id: serverId };
        
        // Se está usando reseller_id, inclui o username do cliente
        if (clientInfo.reseller_id || resellerId) {
            requestBody.client_username = clientInfo.username;
        }
        
        const response = await apiRequest(`${migrateUrl}?${migrateParams.toString()}`, {
            method: 'POST',
            body: JSON.stringify(requestBody)
        });
        
        if (response.success) {
            const successMessage = response.message || 'Migração realizada com sucesso!';
            alert(successMessage);
            
            // Mostrar dica adicional após 3 segundos
            setTimeout(() => {
                alert('💡 Dica: Reinicie a TV da tomada ou feche e abra o App para puxar as atualizações.');
            }, 3000);
            
            // Atualizar informações do cliente
            clientInfo.server_id = serverId;
            clientInfo.server_name = serverName;
            displayCurrentServer.textContent = serverName;
            
            // Recarregar opções de servidor
            populateServerSelect();
            
            // Resetar formulário
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
    
    // Resetar formulários
    clientLoginForm.reset();
    clientMigrationForm.reset();
    
    // Limpar mensagens
    hideMessage(loginMessage);
    hideMessage(migrationMessage);
    
    // Mostrar tela de login
    migrationSection.classList.add('hidden');
    loginSection.classList.remove('hidden');
}

// Event listeners serão registrados no DOMContentLoaded principal

// Função para lidar com erros globais
window.addEventListener('error', function(event) {
    console.error('Erro global:', event.error);
    hideLoading();
});

// Função para lidar com promessas rejeitadas
window.addEventListener('unhandledrejection', function(event) {
    console.error('Promise rejeitada:', event.reason);
    hideLoading();
});

// Função para mostrar modal de confirmação
function showConfirmationModal() {
    return new Promise((resolve, reject) => {
        migrationModal.classList.add('show');
        
        const handleConfirm = () => {
            cleanup();
            resolve(true);
        };
        
        const handleCancel = () => {
            cleanup();
            reject(new Error('Cancelado pelo usuário'));
        };
        
        const handleKeyPress = (e) => {
            if (e.key === 'Enter') {
                handleConfirm();
            } else if (e.key === 'Escape') {
                handleCancel();
            }
        };
        
        const cleanup = () => {
            migrationModal.classList.remove('show');
            confirmMigrationBtn.removeEventListener('click', handleConfirm);
            cancelMigrationBtn.removeEventListener('click', handleCancel);
            document.removeEventListener('keydown', handleKeyPress);
        };
        
        confirmMigrationBtn.addEventListener('click', handleConfirm);
        cancelMigrationBtn.addEventListener('click', handleCancel);
        document.addEventListener('keydown', handleKeyPress);
    });
}

// Inicialização quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    // Define elementos DOM
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
    
    // Registrar event listeners
    if (clientLoginForm) {
        clientLoginForm.addEventListener('submit', handleClientLogin);
    }
    
    if (clientMigrationForm) {
        clientMigrationForm.addEventListener('submit', handleClientMigration);
    }
    
    if (btnClientLogout) {
        btnClientLogout.addEventListener('click', handleClientLogout);
    }
    
    // Event listeners para limpar mensagens foram removidos (usando alert agora)
    
    // Processa credenciais da URL se existirem
    processUrlCredentials();
});