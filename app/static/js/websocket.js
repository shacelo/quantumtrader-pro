// static/js/websocket.js - VERSIÓN COMPLETA Y CORREGIDA
class WebSocketManager {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        this.init();
    }

    init() {
        // ✅ CORREGIDO: Verificar si CONFIG existe
        if (typeof CONFIG === 'undefined' || !CONFIG.SOCKET_ENABLED) {
            console.log('WebSocket disabled in configuration');
            return;
        }

        try {
            this.socket = io({
                transports: ['websocket'],
                timeout: 10000
            });

            this.setupEventHandlers();
        } catch (error) {
            console.error('WebSocket initialization error:', error);
        }
    }

    setupEventHandlers() {
        this.socket.on('connect', () => {
            console.log('✅ WebSocket connected');
            this.connected = true;
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            
            if (typeof updateConnectionStatus === 'function') {
                updateConnectionStatus('connected');
            }
            
            showNotification('🔗 Conectado al servidor en tiempo real', 'success');
        });

        this.socket.on('disconnect', (reason) => {
            console.log('❌ WebSocket disconnected:', reason);
            this.connected = false;
            
            if (typeof updateConnectionStatus === 'function') {
                updateConnectionStatus('disconnected');
            }
            
            this.handleReconnection();
        });

        this.socket.on('connect_error', (error) => {
            console.error('❌ WebSocket connection error:', error);
            this.connected = false;
            
            if (typeof updateConnectionStatus === 'function') {
                updateConnectionStatus('error');
            }
            
            this.handleReconnection();
        });

        this.socket.on('log_entry', (data) => {
            this.handleLogEntry(data);
        });

        this.socket.on('trade_update', (data) => {
            this.handleTradeUpdate(data);
        });

        this.socket.on('balance_update', (data) => {
            this.handleBalanceUpdate(data);
        });

        this.socket.on('session_update', (data) => {
            this.handleSessionUpdate(data);
        });

        this.socket.on('bot_status', (data) => {
            this.handleBotStatus(data);
        });
    }

    handleReconnection() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * this.reconnectAttempts;
            
            console.log(`🔄 Attempting reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
            
            setTimeout(() => {
                this.socket.connect();
            }, delay);
        } else {
            console.error('❌ Max reconnection attempts reached');
            showNotification('❌ Error de conexión con el servidor', 'error');
        }
    }

    handleLogEntry(data) {
        if (typeof addLog === 'function') {
            addLog(data.source, data.message, data.level);
        }
        
        // Show important logs as notifications
        if (data.level === 'error') {
            showNotification(`❌ ${data.source}: ${data.message}`, 'error');
        } else if (data.level === 'warning') {
            showNotification(`⚠️ ${data.source}: ${data.message}`, 'warning');
        }
    }

    handleTradeUpdate(data) {
        console.log('📊 Trade update:', data);
        
        const message = `💰 ${data.symbol} - ${data.side} ${data.quantity} @ ${data.price}`;
        showNotification(message, 'info');
        
        // Refresh dashboard data
        if (typeof loadDashboardData === 'function') {
            setTimeout(loadDashboardData, 1000);
        }
    }

    handleBalanceUpdate(data) {
        console.log('💰 Balance update:', data);
        
        // Update balance display immediately
        const balanceElement = document.getElementById('currentBalance');
        if (balanceElement) {
            balanceElement.textContent = formatCurrency(data.balance);
        }
    }

    handleSessionUpdate(data) {
        console.log('🔄 Session update:', data);
        
        if (data.status === 'stopped' && typeof updateBotStatus === 'function') {
            updateBotStatus(false, data.status);
        }
        
        // Refresh dashboard when session changes
        if (typeof loadDashboardData === 'function') {
            setTimeout(loadDashboardData, 500);
        }
    }

    handleBotStatus(data) {
        console.log('🤖 Bot status:', data);
        
        if (typeof updateBotStatus === 'function') {
            const isRunning = data.status === 'running';
            updateBotStatus(isRunning, data.status, data.trading_mode);
        }
        
        showNotification(`🤖 ${data.message}`, 'info');
        
        // Refresh dashboard when bot status changes
        if (typeof loadDashboardData === 'function') {
            setTimeout(loadDashboardData, 500);
        }
    }

    joinSession(sessionId) {
        if (this.connected && sessionId) {
            this.socket.emit('join_session', { session_id: sessionId });
            console.log(`🔗 Joined session: ${sessionId}`);
        }
    }

    leaveSession(sessionId) {
        if (this.connected && sessionId) {
            this.socket.emit('leave_session', { session_id: sessionId });
            console.log(`🔗 Left session: ${sessionId}`);
        }
    }

    // Nuevo método para enviar comandos al bot
    sendBotCommand(command, data = {}) {
        if (this.connected) {
            this.socket.emit('bot_command', {
                command: command,
                ...data
            });
            console.log(`🤖 Sent bot command: ${command}`, data);
        }
    }

    // Método para solicitar estado actual
    requestStatusUpdate() {
        if (this.connected) {
            this.socket.emit('status_request');
            console.log('📊 Requested status update');
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.connected = false;
            console.log('🔌 WebSocket manually disconnected');
        }
    }

    // Método para verificar estado de conexión
    isConnected() {
        return this.connected;
    }

    // Método para obtener estadísticas de conexión
    getConnectionStats() {
        return {
            connected: this.connected,
            reconnectAttempts: this.reconnectAttempts,
            maxReconnectAttempts: this.maxReconnectAttempts
        };
    }
}

// Initialize WebSocket manager
const wsManager = new WebSocketManager();

// Expose socket globally for other scripts
const socket = wsManager.socket;

// Función global para controlar WebSocket desde otros archivos
function getWebSocketManager() {
    return wsManager;
}