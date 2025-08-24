"""
Configurações centralizadas do sistema
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class AlertConfig:
    """Configurações de alertas de preços - carregadas do Firestore"""
    btc_lowest: Optional[float] = None
    btc_high: Optional[float] = None
    eth_lowest: Optional[float] = None
    eth_high: Optional[float] = None

@dataclass
class WebSocketConfig:
    """Configurações do WebSocket"""
    btc_url: str = "wss://stream.binance.com:9443/ws/btcbrl@ticker"
    eth_url: str = "wss://stream.binance.com:9443/ws/ethbrl@ticker"

@dataclass
class NotificationConfig:
    """Configurações de notificações"""
    fcm_topic: str = "crypto_alerts"
    notification_interval: int = 30  # segundos

@dataclass
class ServerConfig:
    """Configurações do servidor"""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False

@dataclass
class FirebaseConfig:
    """Configurações do Firebase"""
    service_account_path: str = "service-account.json"
    google_services_path: str = "google-services.json"
    firestore_collection: str = "coins"

class Settings:
    """Classe principal de configurações"""
    
    def __init__(self):
        self.alerts = AlertConfig()
        self.websocket = WebSocketConfig()
        self.notifications = NotificationConfig()
        self.server = ServerConfig()
        self.firebase = FirebaseConfig()
        
        self._load_from_env()
        
        self._firestore_loaded = False
    
    def _load_from_env(self):
        """Carrega configurações de variáveis de ambiente"""
        if os.getenv('BTC_LOWEST'):
            self.alerts.btc_lowest = float(os.getenv('BTC_LOWEST'))
        if os.getenv('BTC_HIGH'):
            self.alerts.btc_high = float(os.getenv('BTC_HIGH'))
        if os.getenv('ETH_LOWEST'):
            self.alerts.eth_lowest = float(os.getenv('ETH_LOWEST'))
        if os.getenv('ETH_HIGH'):
            self.alerts.eth_high = float(os.getenv('ETH_HIGH'))
        
        self.server.host = os.getenv('HOST', self.server.host)
        self.server.port = int(os.getenv('PORT', self.server.port))
        self.server.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        
        self.notifications.notification_interval = int(
            os.getenv('NOTIFICATION_INTERVAL', self.notifications.notification_interval)
        )
        
        self.firebase.firestore_collection = os.getenv('FIRESTORE_COLLECTION', self.firebase.firestore_collection)
    
    def load_from_firestore(self):
        """Carrega configurações do Firestore - OBRIGATÓRIO"""
        try:
            # Importação tardia para evitar dependência circular
            from ..services.firestore_service import get_firestore_service
            
            firestore_service = get_firestore_service()
            config = firestore_service.get_alert_config()
            if config:
                self.alerts.btc_lowest = float(config['btc_lowest'])
                self.alerts.btc_high = float(config['btc_high'])
                self.alerts.eth_lowest = float(config['eth_lowest'])
                self.alerts.eth_high = float(config['eth_high'])
                if 'notification_interval' in config:
                    self.notifications.notification_interval = int(config['notification_interval'])
                
                self._firestore_loaded = True
                return True
            else:
                print("ERRO: Configurações não encontradas no Firestore!")
                print("Aplicação não pode continuar sem configurações válidas")
                raise Exception("Configurações obrigatórias não encontradas no Firestore")
                
        except Exception as e:
            print(f"ERRO CRÍTICO ao carregar do Firestore: {e}")
            print("Aplicação não pode continuar sem Firestore")
            raise e
    
    def save_to_firestore(self):
        """Salva configurações atuais no Firestore"""
        try:
            
            config = {
                "btc_lowest": self.alerts.btc_lowest,
                "btc_high": self.alerts.btc_high,
                "eth_lowest": self.alerts.eth_lowest,
                "eth_high": self.alerts.eth_high,
                "notification_interval": self.notifications.notification_interval
            }
            
            from ..services.firestore_service import get_firestore_service
            firestore_service = get_firestore_service()
            return firestore_service.save_alert_config(config)
            
        except Exception as e:
            print(f"Erro ao salvar no Firestore: {e}")
            return False
    
    def update_alert_levels(self, btc_lowest: Optional[float] = None, btc_high: Optional[float] = None,
                           eth_lowest: Optional[float] = None, eth_high: Optional[float] = None) -> bool:
        """Atualiza níveis de alerta e salva no Firestore"""
        try:
            if btc_lowest is not None:
                self.alerts.btc_lowest = btc_lowest
            if btc_high is not None:
                self.alerts.btc_high = btc_high
            if eth_lowest is not None:
                self.alerts.eth_lowest = eth_lowest
            if eth_high is not None:
                self.alerts.eth_high = eth_high
            
            success = self.save_to_firestore()
            if success:
                print("Níveis de alerta atualizados e salvos no Firestore")
            return success
            
        except Exception as e:
            print(f"Erro ao atualizar níveis de alerta: {e}")
            return False
    
    def get_alert_summary(self) -> dict:
        """Retorna resumo das configurações de alerta"""
        return {
            "btc_lowest": self.alerts.btc_lowest,
            "btc_high": self.alerts.btc_high,
            "eth_lowest": self.alerts.eth_lowest,
            "eth_high": self.alerts.eth_high,
            "notification_interval": self.notifications.notification_interval,
            "firestore_loaded": self._firestore_loaded
        }

settings = Settings()
