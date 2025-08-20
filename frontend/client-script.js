// Variáveis globais
let clientInfo = null;
let availableServers = [];
let clientToken = null;

// Função para processar credenciais da URL
function processUrlCredentials() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (token) {
        try {
            // Armazena o token
            clientToken = token;
            
            // Faz login automaticamente usando o token
            setTimeout(() => {
                handleTokenLogin();
            }, 500);
            
            // Remove o parâmetro da URL para segurança
            const newUrl = window.location.origin + window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
            
            return true;
        } catch (error) {
            console.error('Erro ao processar token da URL:', error);
            showMessage(loginMessage, 'Link inválido ou expirado.', 'error');
        }
    }
    return false;
}

// Elementos DOM
const loginSection = document.getElementById('login-section');
const migrationSection = document.getElementById('migration-section');
const clientLoginForm = document.getElementById('client-login-form');
const clientMigrationForm = document.getElementById('client-migration-form');
const loadingOverlay = document.getElementById('loading-overlay');
const loadingMessage = document.querySelector('.loading-message');
const loginMessage = document.getElementById('login-message');
const migrationMessage = document.getElementById('migration-message');
const btnClientLogout = document.getElementById('btn-client-logout');
const newServerSelect = document.getElementById('new-server-select');

// Elementos de exibição de informações
const displayUsername = document.getElementById('display-username');
const displayCurrentServer = document.getElementById('display-current-server');
const displayPackage = document.getElementById('display-package');

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
        }
    } catch (error) {
        console.error('Erro ao carregar servidores:', error);
    }
}

// Função para popular o select de servidores
function populateServerSelect() {
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
        username: formData.get('username'),
        password: formData.get('password')
    };
    
    if (!loginData.username || !loginData.password) {
        showMessage(loginMessage, 'Por favor, preencha todos os campos.', 'error');
        return;
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
            showClientInterface();
            await loadServers();
        } else {
            showMessage(loginMessage, 'Falha na autenticação.', 'error');
        }
    } catch (error) {
        showMessage(loginMessage, error.message || 'Erro ao fazer login.', 'error');
    } finally {
        hideLoading();
    }
}

// Função para fazer login usando token
async function handleTokenLogin() {
    if (!clientToken) {
        showMessage(loginMessage, 'Token não encontrado.', 'error');
        return;
    }
    
    showLoading('Verificando acesso...');
    hideMessage(loginMessage);
    
    try {
        const response = await apiRequest('/api/client/login', {
            method: 'POST',
            body: JSON.stringify({ token: clientToken })
        });
        
        if (response.success) {
            clientInfo = response.client_info;
            showClientInterface();
            await loadServers();
        } else {
            showMessage(loginMessage, 'Link inválido ou expirado.', 'error');
        }
    } catch (error) {
        showMessage(loginMessage, error.message || 'Erro ao acessar com o link.', 'error');
    } finally {
        hideLoading();
    }
}

// Função para mostrar a interface do cliente
function showClientInterface() {
    loginSection.classList.add('hidden');
    migrationSection.classList.remove('hidden');
    
    // Preencher informações do cliente
    displayUsername.textContent = clientInfo.username;
    displayCurrentServer.textContent = clientInfo.server_name || 'N/A';
    displayPackage.textContent = clientInfo.package_name || 'N/A';
    
    populateServerSelect();
}

// Função para migração do cliente
async function handleClientMigration(event) {
    event.preventDefault();
    
    const formData = new FormData(clientMigrationForm);
    const serverId = formData.get('server_id');
    
    if (!serverId) {
        showMessage(migrationMessage, 'Por favor, selecione um servidor.', 'error');
        return;
    }
    
    const selectedServer = availableServers.find(s => s.id === serverId);
    const serverName = selectedServer ? selectedServer.name : 'servidor selecionado';
    
    const confirmMigration = confirm(
        `Tem certeza que deseja migrar para ${serverName}?\n\n` +
        'Esta ação pode levar alguns minutos para ser concluída.'
    );
    
    if (!confirmMigration) {
        return;
    }
    
    showLoading('Migrando servidor...');
    hideMessage(migrationMessage);
    
    try {
        // Solicitar senha para confirmar migração
        const password = prompt('Digite sua senha para confirmar a migração:');
        if (!password) {
            hideLoading();
            return;
        }
        
        const response = await apiRequest(`/api/client/migrate?token=${encodeURIComponent(clientToken)}`, {
            method: 'POST',
            body: JSON.stringify({ server_id: serverId, password: password })
        });
        
        if (response.success) {
            showMessage(migrationMessage, response.message || 'Migração realizada com sucesso!', 'success');
            
            // Atualizar informações do cliente
            clientInfo.server_id = serverId;
            clientInfo.server_name = serverName;
            displayCurrentServer.textContent = serverName;
            
            // Recarregar opções de servidor
            populateServerSelect();
            
            // Resetar formulário
            clientMigrationForm.reset();
        } else {
            showMessage(migrationMessage, 'Falha na migração.', 'error');
        }
    } catch (error) {
        showMessage(migrationMessage, error.message || 'Erro ao migrar servidor.', 'error');
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

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Login form
    clientLoginForm.addEventListener('submit', handleClientLogin);
    
    // Migration form
    clientMigrationForm.addEventListener('submit', handleClientMigration);
    
    // Logout button
    btnClientLogout.addEventListener('click', handleClientLogout);
    
    // Limpar mensagens quando o usuário começar a digitar
    document.getElementById('client-username').addEventListener('input', () => {
        hideMessage(loginMessage);
    });
    
    document.getElementById('client-password').addEventListener('input', () => {
        hideMessage(loginMessage);
    });
    
    newServerSelect.addEventListener('change', () => {
        hideMessage(migrationMessage);
    });
});

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

// Inicialização quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    // Processa credenciais da URL se existirem
    processUrlCredentials();
});