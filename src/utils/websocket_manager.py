"""
Gerenciador de WebSocket
Utilitário para conexões WebSocket
"""
import websocket
import json
import threading
from typing import Callable, Optional
from ..config.settings import settings


class WebSocketManager:
    """Gerenciador de conexões WebSocket"""
    
    def __init__(self, on_btc_message: Callable, on_eth_message: Callable):
        self.on_btc_message = on_btc_message
        self.on_eth_message = on_eth_message
        self.websocket_config = settings.websocket
        self.btc_ws: Optional[websocket.WebSocketApp] = None
        self.eth_ws: Optional[websocket.WebSocketApp] = None
    
    def _on_btc_message(self, ws, message):
        """Processa mensagens do Bitcoin"""
        try:
            data = json.loads(message)
            if 'c' in data:
                price = float(data['c'])
                self.on_btc_message(price)
        except Exception as e:
            print(f"Erro BTC WebSocket: {e}")
    
    def _on_eth_message(self, ws, message):
        """Processa mensagens do Ethereum"""
        try:
            data = json.loads(message)
            if 'c' in data:
                price = float(data['c'])
                self.on_eth_message(price)
        except Exception as e:
            print(f"Erro ETH WebSocket: {e}")
    
    def start_connections(self):
        """Inicia as conexões WebSocket em threads separadas"""
        
        self.btc_ws = websocket.WebSocketApp(
            self.websocket_config.btc_url,
            on_message=self._on_btc_message,
        )
        
        self.eth_ws = websocket.WebSocketApp(
            self.websocket_config.eth_url,
            on_message=self._on_eth_message,
        )
        
        btc_thread = threading.Thread(target=self.btc_ws.run_forever)
        eth_thread = threading.Thread(target=self.eth_ws.run_forever)
        
        btc_thread.daemon = True
        eth_thread.daemon = True
        
        btc_thread.start()
        eth_thread.start()
    
    def stop_connections(self):
        """Para as conexões WebSocket"""
        if self.btc_ws:
            self.btc_ws.close()
        if self.eth_ws:
            self.eth_ws.close()
        print("WebSockets desconectados")
