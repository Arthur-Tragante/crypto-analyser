"""
Serviço de notificações
Regras de negócio para envio de notificações
"""
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from ..models.crypto_data import NotificationData, AlertStatus
from ..config.settings import settings

if TYPE_CHECKING:
    from .crypto_service import CryptoService
    from .fcm_service import FCMService


class NotificationFormatter:
    """Formatador de notificações"""
    
    @staticmethod
    def create_mobile_notification(data: NotificationData) -> str:
        """Cria notificação compacta para mobile"""
        lines = []
        for symbol, crypto in data.crypto_prices.items():
            icon = crypto.get_icon()
            lines.append(f"{icon} {symbol.upper()}: R$ {crypto.formatted_price} - {crypto.alert_status.value}")
        
        return "\n".join(lines)
    
    @staticmethod
    def create_fcm_notification(data: NotificationData) -> tuple[str, str]:
        """Cria notificação para FCM (título e corpo)"""
        title = "CRYPTO ANALYSER"
        
        # Cria corpo com todas as moedas
        parts = []
        for symbol, crypto in data.crypto_prices.items():
            parts.append(f"{symbol.upper()}: R$ {crypto.formatted_price} ({crypto.alert_status.value})")
        
        body = " | ".join(parts)
        return title, body


class NotificationService:
    """Serviço de notificações com regras de negócio"""
    
    def __init__(self):
        self.formatter = NotificationFormatter()
        self._last_notification_time: Optional[datetime] = None
    
    def should_send_notification(self, interval_seconds: Optional[int] = None) -> bool:
        """Verifica se deve enviar notificação baseado no intervalo"""
        if interval_seconds is None:
            interval_seconds = settings.notifications.notification_interval
        if self._last_notification_time is None:
            return True
        
        time_diff = (datetime.now() - self._last_notification_time).total_seconds()
        return time_diff >= interval_seconds
    
    def mark_notification_sent(self):
        """Marca que uma notificação foi enviada"""
        self._last_notification_time = datetime.now()
    
    def has_alert_condition(self, data: NotificationData) -> bool:
        """Verifica se alguma moeda está em condição de alerta (HIGH ou LOW)"""
        return data.has_alerts()
    
    def prepare_notification_data(self, data: NotificationData) -> dict:
        """Prepara dados completos para notificação"""
        mobile_content = self.formatter.create_mobile_notification(data)
        fcm_title, fcm_body = self.formatter.create_fcm_notification(data)
        
        return {
            "mobile_content": mobile_content,
            "fcm_title": fcm_title,
            "fcm_body": fcm_body,
            "data": data.to_dict(),
            "timestamp": data.timestamp.isoformat()
        }
    
    def send_formatted_notification(self, crypto_service: 'CryptoService', fcm_service: Optional['FCMService'] = None):
        """Envia notificação formatada para todos os canais"""
        try:
            # Busca moedas da coleção notify
            from .firestore_service import get_firestore_service
            firestore_service = get_firestore_service()
            notify_coins = firestore_service.get_notify_coins()
            
            if not notify_coins:
                print("Nenhuma moeda configurada na coleção notify - usando fallback BTC/ETH")
                notify_coins = ["btc", "eth"]
            
            notification_data = crypto_service.get_notification_data(notify_coins)
            if not notification_data:
                print("Sem dados de notificação (aguardando preços da API)...")
                return
            
            # Verifica se alguma moeda está em alerta antes de enviar
            if not self.has_alert_condition(notification_data):
                print("Nenhuma moeda em alerta - notificação não enviada")
                return
            
            alert_coins = notification_data.get_alert_coins()
            print(f"Moeda(s) em alerta detectada(s): {alert_coins} - enviando notificação...")
            prepared_data = self.prepare_notification_data(notification_data)

            # Usando apenas FCM (Firebase Cloud Messaging)
            if fcm_service:
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
            
            self.mark_notification_sent()
                    
        except Exception as e:
            print(f"Erro ao enviar notificação formatada: {e}")
