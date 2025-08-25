"""
Aplicação principal refatorada
Seguindo melhores práticas - apenas configuração e inicialização
"""
import time
from flask import Flask
from flask_cors import CORS

from src.config.settings import settings
from src.controllers.crypto_controller import CryptoController
from src.controllers.notification_controller import NotificationController
from src.services.crypto_service import CryptoService
from src.services.notification_service import NotificationService
from src.services.app_service import AppService
from src.repositories.crypto_repository import CryptoRepository
from src.services.fcm_service import fcm_service


try:
    FCM_ENABLED = True
    print("FCM v1 habilitado!")
except ImportError:
    print("FCM v1 não disponível")
    FCM_ENABLED = False


class CryptoAnalyserApp:
    """Classe principal da aplicação - apenas configuração e rotas"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Inicialização de serviços
        self.repository = CryptoRepository()
        self.crypto_service = CryptoService(self.repository)
        self.notification_service = NotificationService()
        self.app_service = AppService(
            self.crypto_service, 
            self.notification_service, 
            self.repository
        )
        
        # Controllers
        self.crypto_controller = CryptoController(self.repository, self.crypto_service)
        self.notification_controller = NotificationController(
            fcm_service=fcm_service if FCM_ENABLED else None
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura as rotas da API"""
        # Rotas principais
        self.app.route('/', methods=['GET'])(self.crypto_controller.get_home)
        self.app.route('/display', methods=['GET'])(self.crypto_controller.get_display)
        self.app.route('/display/auto-refresh', methods=['GET'])(self.crypto_controller.get_display_auto_refresh)
        
        # Rotas de notificação
        self.app.route('/fcm/send-to-topic', methods=['POST'])(self.notification_controller.send_fcm_to_topic)
        self.app.route('/fcm/send-to-token', methods=['POST'])(self.notification_controller.send_fcm_to_token)

    def run(self):
        """Executa a aplicação"""
        # Inicia serviços em background
        self.app_service.start_background_services()
        
        time.sleep(3)
        
        print("=== CRYPTO PUSHER INICIADO ===")
        print("Endpoints disponíveis:")
        print("  GET /                        - Informações da API")
        print("  GET /display                - Visualização ASCII")
        print("  GET /display/auto-refresh   - Display com auto-refresh")
        print("  POST /fcm/send-to-topic     - Enviar FCM para tópico público")
        print("  POST /fcm/send-to-token     - Enviar FCM para token específico")
        print("  POST /prices/update         - Forçar atualização de preços")
        print("  POST /test/notification     - Testar lógica de notificação")
        print("  GET /test/display           - Testar display com todas as moedas")
        print("  GET /debug/prices           - Diagnóstico de instâncias")
        print("="*50)
        print("Usando API REST do CoinGecko (consultas a cada 1 minuto)")
        print("="*50)

        self.app.run(
            host="0.0.0.0",
            port=5000,
            debug=False
        )

def main():
    """Função principal"""
    app = CryptoAnalyserApp()
    app.run()

if __name__ == "__main__":
    main()
