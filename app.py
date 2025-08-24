"""
Aplicação principal refatorada
Seguindo melhores práticas de código
"""
import time
import threading
from flask import Flask
from flask_cors import CORS

from src.config.settings import settings
from src.controllers.crypto_controller import CryptoController
from src.controllers.notification_controller import NotificationController
from src.services.crypto_service import CryptoService
from src.services.notification_service import NotificationService
from src.repositories.crypto_repository import CryptoRepository
from src.utils.websocket_manager import WebSocketManager
from src.services.fcm_service import fcm_service

try:
    FCM_ENABLED = True
    print("FCM v1 habilitado!")
except ImportError:
    print("FCM v1 não disponível")
    FCM_ENABLED = False
    fcm_service = None

class ServerSettings:
    host = "0.0.0.0"
    port = 80
    debug = False

class CryptoAnalyserApp:
    """Classe principal da aplicação"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        self.repository = CryptoRepository()
        self.crypto_service = CryptoService(self.repository)
        self.notification_service = NotificationService()
        
        self.crypto_controller = CryptoController()
        self.notification_controller = NotificationController(
            fcm_service=fcm_service if FCM_ENABLED else None
        )
        
        self.websocket_manager = WebSocketManager(
            on_btc_message=self._on_btc_price_update,
            on_eth_message=self._on_eth_price_update
        )
        
        self._setup_routes()
        
        self._last_btc_alert = None
        self._last_eth_alert = None
    
    def _setup_routes(self):
        """Configura as rotas da API"""
        self.app.route('/', methods=['GET'])(self.crypto_controller.get_home)
        self.app.route('/display', methods=['GET'])(self.crypto_controller.get_display)
        self.app.route('/display/auto-refresh', methods=['GET'])(self.crypto_controller.get_display_auto_refresh)
        
        self.app.route('/fcm/send-to-topic', methods=['POST'])(self.notification_controller.send_fcm_to_topic)
        self.app.route('/fcm/send-to-token', methods=['POST'])(self.notification_controller.send_fcm_to_token)
    
    def _on_btc_price_update(self, price: float):
        """Callback para atualização de preço do BTC"""
        self.crypto_service.update_crypto_price("btc", price)
    
    def _on_eth_price_update(self, price: float):
        """Callback para atualização de preço do ETH"""
        self.crypto_service.update_crypto_price("eth", price)
    
    def _check_alerts(self):
        """Thread para verificar alertas continuamente"""
        while True:
            try:
                btc = self.repository.get_crypto_by_symbol("btc")
                eth = self.repository.get_crypto_by_symbol("eth")
                
                if btc and btc.price is not None:
                    current_btc_alert = btc.alert_status
                    if self.crypto_service.should_send_alert("btc", current_btc_alert, self._last_btc_alert):
                        self._last_btc_alert = current_btc_alert
                    elif current_btc_alert.value == "NORMAL":
                        self._last_btc_alert = None
                
                if eth and eth.price is not None:
                    current_eth_alert = eth.alert_status
                    if self.crypto_service.should_send_alert("eth", current_eth_alert, self._last_eth_alert):
                        self._last_eth_alert = current_eth_alert
                    elif current_eth_alert.value == "NORMAL":
                        self._last_eth_alert = None
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Erro no sistema de alertas: {e}")
                time.sleep(5)

    def _periodic_notification_sender(self):
        """Thread para enviar notificações periódicas"""
        while True:
            try:
                time.sleep(settings.notifications.notification_interval)
                
                if self.notification_service.should_send_notification(
                    settings.notifications.notification_interval
                ):
                    self._send_formatted_notification()
                    
            except Exception as e:
                print(f"Erro no sender periódico: {e}")
                time.sleep(60)
    
    def _send_formatted_notification(self):
        """Envia notificação formatada para todos os canais"""
        try:
            notification_data = self.crypto_service.get_notification_data()
            if not notification_data:
                return
            
            prepared_data = self.notification_service.prepare_notification_data(notification_data)

            # Usando apenas FCM (Firebase Cloud Messaging) - sem limite de mensagens
            
            if FCM_ENABLED and fcm_service:
                try:
                    success = fcm_service.send_to_topic(
                        "crypto_alerts", 
                        prepared_data["fcm_title"], 
                        prepared_data["fcm_body"], 
                        prepared_data["data"]
                    )
                    if success:
                        print("FCM: Notificação enviada com sucesso")
                    else:
                        print("FCM: Falha ao enviar")
                except Exception as e:
                    print(f"FCM v1: {e}")
            
            self.notification_service.mark_notification_sent()
                    
        except Exception as e:
            print(f"Erro ao enviar notificação formatada: {e}")
    
    def start_background_services(self):
        """Inicia serviços em background"""
        settings.load_from_firestore()
        
        websocket_thread = threading.Thread(target=self.websocket_manager.start_connections)
        websocket_thread.daemon = True
        websocket_thread.start()
        
        alert_thread = threading.Thread(target=self._check_alerts)
        alert_thread.daemon = True
        alert_thread.start()
        
        notification_thread = threading.Thread(target=self._periodic_notification_sender)
        notification_thread.daemon = True
        notification_thread.start()
    
    def run(self):
        """Executa a aplicação"""
        self.start_background_services()
        
        time.sleep(3)
        
        print("=== CRYPTO PUSHER INICIADO ===")
        print("Endpoints disponíveis:")
        print("  GET /                        - Informações da API")
        print("  GET /display                - Visualização ASCII")
        print("  GET /display/auto-refresh   - Display com auto-refresh")
        print("  POST /fcm/send-to-topic     - Enviar FCM para tópico público")
        print("  POST /fcm/send-to-token     - Enviar FCM para token específico")
        print("="*50)

        self.app.run(
            host="0.0.0.0",  # força escutar em todas as interfaces
            port=5000,          # ou 5000 se quiser evitar sudo
            debug=False
        )

def main():
    """Função principal"""
    app = CryptoAnalyserApp()
    app.run()

if __name__ == "__main__":
    main()
