"""
AppService - Gerencia threads e lógica de background da aplicação
"""
import time
import threading
from typing import Optional

from ..config.settings import settings
from .crypto_service import CryptoService
from .notification_service import NotificationService
from .fcm_service import fcm_service
from .firestore_service import get_firestore_service
from ..repositories.crypto_repository import CryptoRepository


class AppService:
    """Serviço principal da aplicação - gerencia threads e background services"""
    
    def __init__(self, crypto_service: CryptoService, notification_service: NotificationService, repository: CryptoRepository):
        self.crypto_service = crypto_service
        self.notification_service = notification_service
        self.repository = repository
        
        self._last_btc_alert = None
        self._last_eth_alert = None
        
    def start_background_services(self):
        """Inicia todos os serviços em background"""
        try:
            settings.load_from_firestore()
            print("Configurações carregadas do Firestore")
        except Exception as e:
            print(f"Aviso: Falha ao carregar Firestore: {e}")
            print("Continuando com configurações padrão...")
        
        # Thread para atualizar preços via API REST (1 minuto)
        price_thread = threading.Thread(target=self._price_updater)
        price_thread.daemon = True
        price_thread.start()
        
        # Thread para verificar alertas
        alert_thread = threading.Thread(target=self._check_alerts)
        alert_thread.daemon = True
        alert_thread.start()
        
        # Thread para enviar notificações periódicas
        notification_thread = threading.Thread(target=self._periodic_notification_sender)
        notification_thread.daemon = True
        notification_thread.start()
        
    def _price_updater(self):
        """Thread para atualizar preços de 1 em 1 minuto"""
        # Primeira consulta imediata
        try:
            print("Fazendo consulta inicial de preços...")
            self.crypto_service.update_prices_from_api()
        except Exception as e:
            print(f"Erro na consulta inicial: {e}")
        
        # Loop principal com intervalo de 1 minuto
        while True:
            try:
                time.sleep(60)  # 1 minuto
                self.crypto_service.update_prices_from_api()
            except Exception as e:
                print(f"Erro no atualizador de preços: {e}")
                time.sleep(30)
                
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
                    self.notification_service.send_formatted_notification(
                        self.crypto_service, fcm_service
                    )
                    
            except Exception as e:
                print(f"Erro no sender periódico: {e}")
                time.sleep(30)
