"""
Serviço de notificações
Regras de negócio para envio de notificações
"""
from typing import Optional
from datetime import datetime
from ..models.crypto_data import NotificationData


class NotificationFormatter:
    """Formatador de notificações"""
    
    @staticmethod
    def create_mobile_notification(data: NotificationData) -> str:
        """Cria notificação compacta para mobile"""
        btc_icon = data.btc_price.get_icon()
        eth_icon = data.eth_price.get_icon()
        
        notification = f"""{btc_icon} BTC: R$ {data.btc_price.formatted_price} - {data.btc_price.alert_status.value}
{eth_icon} ETH: R$ {data.eth_price.formatted_price} - {data.eth_price.alert_status.value}"""
        
        return notification
    
    @staticmethod
    def create_fcm_notification(data: NotificationData) -> tuple[str, str]:
        """Cria notificação para FCM (título e corpo)"""
        title = "CRYPTO ANALYSER"
        body = f"BTC: R$ {data.btc_price.formatted_price} ({data.btc_price.alert_status.value}) | ETH: R$ {data.eth_price.formatted_price} ({data.eth_price.alert_status.value})"
        return title, body


class NotificationService:
    """Serviço de notificações com regras de negócio"""
    
    def __init__(self):
        self.formatter = NotificationFormatter()
        self._last_notification_time: Optional[datetime] = None
    
    def should_send_notification(self, interval_seconds: int = 30) -> bool:
        """Verifica se deve enviar notificação baseado no intervalo"""
        if self._last_notification_time is None:
            return True
        
        time_diff = (datetime.now() - self._last_notification_time).total_seconds()
        return time_diff >= interval_seconds
    
    def mark_notification_sent(self):
        """Marca que uma notificação foi enviada"""
        self._last_notification_time = datetime.now()
    
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
