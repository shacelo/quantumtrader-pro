// static/js/dashboard.js
class DashboardManager {
    constructor() {
        this.charts = {};
        this.data = null;
        this.updateInterval = null;
    }

    async loadDashboardData() {
        try {
            const response = await apiCall('/dashboard/data');
            
            if (response.success) {
                this.data = response;
                this.updateDashboard();
                this.updateCharts();
                this.updateLastUpdate();
            } else {
                console.warn('No data available:', response.message);
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            showNotification('❌ Error cargando datos del dashboard', 'error');
        }
    }

    updateDashboard() {
        if (!this.data) return;

        const { balance, trading, positions, session } = this.data;

        // Update balance metrics
        this.updateBalanceMetrics(balance);
        
        // Update trading metrics
        this.updateTradingMetrics(trading);
        
        // Update positions
        this.updatePositions(positions);
        
        // Update recent trades
        this.updateRecentTrades(trading.recent_trades);
        
        // Update session info
        if (session) {
            this.updateSessionInfo(session);
        }
    }

    updateBalanceMetrics(balance) {
        // Current Balance
        document.getElementById('currentBalance').textContent = formatCurrency(balance.current_balance);
        document.getElementById('initialBalance').textContent = `Inicial: ${formatCurrency(balance.current_balance - balance.total_pnl)}`;

        // P&L
        const pnlElement = document.getElementById('totalPnL');
        const pnlPercentElement = document.getElementById('totalPnLPercent');
        
        pnlElement.textContent = formatCurrency(balance.total_pnl);
        pnlElement.className = `text-3xl font-bold mt-1 ${balance.total_pnl >= 0 ? 'positive' : 'negative'}`;
        
        pnlPercentElement.textContent = formatPercent(balance.total_pnl_percent || 0);
        pnlPercentElement.className = `text-sm ${balance.total_pnl >= 0 ? 'positive' : 'negative'}`;
    }

    updateTradingMetrics(trading) {
        // Trading Stats
        document.getElementById('tradingStats').textContent = 
            `${trading.real_trades}R/${trading.simulated_trades}S`;
        document.getElementById('totalTrades').textContent = 
            `${trading.total_trades} trades total`;

        // Win Rate
        document.getElementById('winRate').textContent = `${trading.win_rate}%`;
        document.getElementById('winLossStats').textContent = 
            `${trading.winning_trades}W / ${trading.losing_trades}L`;

        // Update counts
        document.getElementById('recentTradesCount').textContent = trading.recent_trades.length;
    }

    updatePositions(positions) {
        const container = document.getElementById('activePositions');
        const countElement = document.getElementById('activePositionsCount');

        countElement.textContent = positions.active_positions;

        if (positions.positions.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <div class="text-4xl mb-2">📭</div>
                    <p>No hay posiciones activas</p>
                </div>
            `;
            return;
        }

        container.innerHTML = positions.positions.map(position => `
            <div class="bg-gray-700 rounded-lg p-4 border-l-4 ${position.unrealized_pnl >= 0 ? 'border-green-400' : 'border-red-400'}">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <span class="font-bold text-lg">${position.symbol}</span>
                        ${position.real_trade ? '<span class="ml-2 px-2 py-1 bg-red-600 rounded text-xs">REAL</span>' : ''}
                    </div>
                    <span class="font-bold ${position.unrealized_pnl >= 0 ? 'positive' : 'negative'}">
                        ${position.unrealized_pnl >= 0 ? '+' : ''}${position.unrealized_pnl_percent}%
                    </span>
                </div>
                <div class="grid grid-cols-2 gap-2 text-sm">
                    <div>
                        <span class="text-gray-400">Entrada:</span>
                        <div class="font-medium">${position.entry_price.toFixed(4)}</div>
                    </div>
                    <div>
                        <span class="text-gray-400">Actual:</span>
                        <div class="font-medium">${position.current_price.toFixed(4)}</div>
                    </div>
                    <div>
                        <span class="text-gray-400">Cantidad:</span>
                        <div class="font-medium">${position.quantity.toFixed(6)}</div>
                    </div>
                    <div>
                        <span class="text-gray-400">P&L:</span>
                        <div class="font-medium ${position.unrealized_pnl >= 0 ? 'positive' : 'negative'}">
                            ${formatCurrency(position.unrealized_pnl)}
                        </div>
                    </div>
                </div>
                <div class="mt-3 pt-2 border-t border-gray-600 text-xs text-gray-400">
                    <div class="flex justify-between">
                        <span>🔴 SL: ${position.stop_loss.toFixed(4)}</span>
                        <span>🟢 TP: ${position.take_profit.toFixed(4)}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    updateRecentTrades(trades) {
        const container = document.getElementById('recentTrades');

        if (trades.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <div class="text-4xl mb-2">📊</div>
                    <p>No hay operaciones recientes</p>
                </div>
            `;
            return;
        }

        container.innerHTML = trades.map(trade => `
            <div class="bg-gray-700 rounded-lg p-3 border-l-4 ${trade.pnl >= 0 ? 'border-green-400' : 'border-red-400'}">
                <div class="flex justify-between items-center mb-1">
                    <div class="flex items-center space-x-2">
                        <span class="font-medium">${trade.symbol}</span>
                        ${trade.real_trade ? 
                          '<span class="px-1 py-0.5 bg-red-600 rounded text-xs">REAL</span>' : 
                          '<span class="px-1 py-0.5 bg-gray-600 rounded text-xs">SIM</span>'
                        }
                    </div>
                    <span class="text-sm font-medium ${trade.pnl >= 0 ? 'positive' : 'negative'}">
                        ${trade.pnl >= 0 ? '+' : ''}${formatCurrency(trade.pnl)}
                    </span>
                </div>
                <div class="flex justify-between text-xs text-gray-400">
                    <span>${trade.entry_price.toFixed(4)} → ${trade.exit_price.toFixed(4)}</span>
                    <span>${new Date(trade.exit_time).toLocaleTimeString()}</span>
                </div>
                <div class="flex justify-between text-xs mt-1">
                    <span class="px-2 py-1 rounded ${trade.status === 'WIN' ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200'}">
                        ${trade.status === 'WIN' ? '✓ GANADOR' : '✗ PERDEDOR'}
                    </span>
                    <span class="text-gray-400">${trade.close_reason}</span>
                </div>
            </div>
        `).join('');
    }

    updateSessionInfo(session) {
        // Update bot status based on session
        const isRunning = session.status === 'running';
        updateBotStatus(isRunning, session.status, session.trading_mode);
    }

    updateCharts() {
        if (!this.data) return;

        const { balance } = this.data;

        // Balance Chart
        this.updateBalanceChart(balance.history);
        
        // P&L Chart
        this.updatePnLChart(balance.history);
    }

    updateBalanceChart(history) {
        const ctx = document.getElementById('balanceChart').getContext('2d');
        
        if (this.charts.balance) {
            this.charts.balance.destroy();
        }

        const labels = history.map(h => h.time);
        const data = history.map(h => h.balance);

        this.charts.balance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Balance (USDT)',
                    data: data,
                    borderColor: '#60a5fa',
                    backgroundColor: 'rgba(96, 165, 250, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#94a3b8',
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#94a3b8'
                        }
                    }
                }
            }
        });
    }

    updatePnLChart(history) {
        const ctx = document.getElementById('pnlChart').getContext('2d');
        
        if (this.charts.pnl) {
            this.charts.pnl.destroy();
        }

        const labels = history.map(h => h.time);
        const data = history.map(h => h.pnl);

        this.charts.pnl = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'P&L (USDT)',
                    data: data,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 3,
                    segment: {
                        borderColor: ctx => {
                            const value = ctx.p0.parsed.y;
                            return value >= 0 ? '#10b981' : '#ef4444';
                        }
                    }
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#94a3b8',
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#94a3b8'
                        }
                    }
                }
            }
        });
    }

    updateLastUpdate() {
        const element = document.getElementById('lastUpdate');
        if (element && this.data) {
            const timestamp = new Date(this.data.timestamp).toLocaleString('es-AR');
            element.textContent = `Última actualización: ${timestamp}`;
        }
    }

    startAutoRefresh(interval = 10000) {
        this.stopAutoRefresh();
        this.updateInterval = setInterval(() => {
            this.loadDashboardData();
        }, interval);
    }

    stopAutoRefresh() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
}

// Global dashboard instance
const dashboard = new DashboardManager();

// Expose to global scope for HTML event handlers
function loadDashboardData() {
    return dashboard.loadDashboardData();
}

function startAutoRefresh() {
    dashboard.startAutoRefresh();
}

function stopAutoRefresh() {
    dashboard.stopAutoRefresh();
}