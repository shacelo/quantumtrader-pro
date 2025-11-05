// Evitar redeclaración
if (typeof window.WebSocketManager === 'undefined') {
    window.WebSocketManager = class WebSocketManager {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.init();
    }

    init() {
        try {
            console.log('Iniciando WebSocket...');
            this.socket = io();

            this.socket.on('connect', () => {
                console.log('✅ WebSocket conectado');
                this.connected = true;
            });

            this.socket.on('price_update', (data) => {
                console.log('Recibido price_update:', data);
                this.handlePriceUpdate(data);
            });

            this.socket.on('disconnect', () => {
                console.log('❌ WebSocket desconectado');
                this.connected = false;
            });

        } catch (error) {
            console.error('Error inicializando WebSocket:', error);
        }
    }

    handlePriceUpdate(data) {
        try {
            const { symbol, price, timestamp } = data;
            const priceElement = document.getElementById(`price-${symbol}`);
            const lastUpdateElement = document.getElementById(`last-price-${symbol}`);
            
            if (priceElement && lastUpdateElement) {
                const oldPrice = parseFloat(priceElement.textContent);
                const newPrice = parseFloat(price);
                
                priceElement.textContent = newPrice.toFixed(2);
                priceElement.classList.remove('price-up', 'price-down');
                
                if (newPrice > oldPrice) {
                    priceElement.classList.add('price-up');
                } else if (newPrice < oldPrice) {
                    priceElement.classList.add('price-down');
                }
                
                const date = new Date(timestamp);
                lastUpdateElement.textContent = date.toLocaleTimeString();
            }
        } catch (error) {
            console.error('Error procesando actualización de precio:', error);
        }
    }
    }
}