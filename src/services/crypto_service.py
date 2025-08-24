"""
Serviço de criptomoedas
Contém as regras de negócio
"""
from typing import Optional, Tuple
from datetime import datetime
from ..models.crypto_data import CryptoPrice, AlertStatus, NotificationData
from ..repositories.crypto_repository import CryptoRepository
from ..config.settings import settings


class CryptoService:
    """Serviço para regras de negócio de criptomoedas"""
    
    def __init__(self, repository: CryptoRepository):
        self.repository = repository
        self.alert_config = settings.alerts
    
    def update_crypto_price(self, symbol: str, price: float) -> bool:
        """Atualiza preço e verifica alertas"""
        success = self.repository.update_crypto_price(symbol, price)
        if success:
            self._check_and_update_alert_status(symbol, price)
        return success
    
    def _check_and_update_alert_status(self, symbol: str, price: float):
        """Verifica e atualiza status de alerta"""
        crypto = self.repository.get_crypto_by_symbol(symbol)
        if not crypto:
            return
        
        if symbol.lower() == "btc":
            crypto.alert_status = self._get_btc_alert_status(price)
        elif symbol.lower() == "eth":
            crypto.alert_status = self._get_eth_alert_status(price)
    
    def _get_btc_alert_status(self, price: float) -> AlertStatus:
        """Determina status de alerta para BTC"""
        if price <= self.alert_config.btc_lowest:
            return AlertStatus.BAIXA
        elif price >= self.alert_config.btc_high:
            return AlertStatus.ALTA
        return AlertStatus.NORMAL
    
    def _get_eth_alert_status(self, price: float) -> AlertStatus:
        """Determina status de alerta para ETH"""
        if price <= self.alert_config.eth_lowest:
            return AlertStatus.BAIXA
        elif price >= self.alert_config.eth_high:
            return AlertStatus.ALTA
        return AlertStatus.NORMAL
    
    def should_send_alert(self, symbol: str, current_status: AlertStatus, last_status: Optional[AlertStatus]) -> bool:
        """Determina se deve enviar alerta (evita spam)"""
        if current_status == AlertStatus.NORMAL:
            return False
        return current_status != last_status
    
    def get_notification_data(self) -> Optional[NotificationData]:
        """Prepara dados para notificação"""
        btc = self.repository.get_crypto_by_symbol("btc")
        eth = self.repository.get_crypto_by_symbol("eth")
        
        if not btc or not eth or btc.price is None or eth.price is None:
            return None
        
        return NotificationData(
            btc_price=btc,
            eth_price=eth,
            timestamp=datetime.now()
        )
    
    def get_alert_levels_info(self) -> dict:
        """Retorna informações dos níveis de alerta"""
        btc = self.repository.get_crypto_by_symbol("btc")
        eth = self.repository.get_crypto_by_symbol("eth")
        
        return {
            "alert_levels": {
                "btc": {
                    "lowest": self.alert_config.btc_lowest,
                    "high": self.alert_config.btc_high,
                    "current": btc.price if btc else None,
                    "formatted_lowest": self._format_brl(self.alert_config.btc_lowest),
                    "formatted_high": self._format_brl(self.alert_config.btc_high),
                    "formatted_current": btc.formatted_price if btc else "N/A",
                    "status": btc.alert_status.value if btc else "N/A"
                },
                "eth": {
                    "lowest": self.alert_config.eth_lowest,
                    "high": self.alert_config.eth_high,
                    "current": eth.price if eth else None,
                    "formatted_lowest": self._format_brl(self.alert_config.eth_lowest),
                    "formatted_high": self._format_brl(self.alert_config.eth_high),
                    "formatted_current": eth.formatted_price if eth else "N/A",
                    "status": eth.alert_status.value if eth else "N/A"
                }
            },
            "alert_status": "Sistema ativo - notificações a cada 30s",
            "timestamp": datetime.now().isoformat()
        }
    
    def _format_brl(self, price: float) -> str:
        """Formata preço para BRL"""
        return f"{price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    def create_display_text(self) -> str:
        """Cria texto formatado para display ASCII"""
        btc = self.repository.get_crypto_by_symbol("btc")
        eth = self.repository.get_crypto_by_symbol("eth")
        
        if not btc or not eth:
            return "Dados não disponíveis"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        width = 62
        
        display_text = ""
        display_text += "╔" + "═" * width + "╗\n"
        display_text += "║" + " CRYPTO ANALYSER - PREÇOS EM TEMPO REAL".center(width) + "║\n"
        display_text += "╠" + "═" * width + "╣\n"
        display_text += f"║ Última atualização: {timestamp}{' ' * (width - len(f' Última atualização: {timestamp}'))}║\n"
        display_text += "╠" + "═" * width + "╣\n"
        
        alerts_active = []
        if btc.alert_status == AlertStatus.BAIXA:
            alerts_active.append("BTC ALERTA DE BAIXA")
        elif btc.alert_status == AlertStatus.ALTA:
            alerts_active.append("BTC ALERTA DE ALTA")
        
        if eth.alert_status == AlertStatus.BAIXA:
            alerts_active.append("ETH ALERTA DE BAIXA")
        elif eth.alert_status == AlertStatus.ALTA:
            alerts_active.append("ETH ALERTA DE ALTA")
        
        if alerts_active:
            for alert in alerts_active:
                display_text += f"║ {alert}{' ' * (width - len(f' {alert}'))}║\n"
            display_text += "╠" + "═" * width + "╣\n"
        
        display_text += f"║Bitcoin (BTC):   R$ {btc.formatted_price}{' ' * (width - len(f'Bitcoin (BTC):   R$ {btc.formatted_price}'))}║\n"
        display_text += f"║Ethereum (ETH):  R$ {eth.formatted_price}{' ' * (width - len(f'Ethereum (ETH):  R$ {eth.formatted_price}'))}║\n"
        
        display_text += "╠" + "═" * width + "╣\n"
        display_text += f"║Níveis: BTC L={self._format_brl(self.alert_config.btc_lowest)[:7]} H={self._format_brl(self.alert_config.btc_high)[:7]}{' ' * (width - len(f'Níveis: BTC L={self._format_brl(self.alert_config.btc_lowest)[:7]} H={self._format_brl(self.alert_config.btc_high)[:7]}'))}║\n"
        display_text += f"║        ETH L={self._format_brl(self.alert_config.eth_lowest)[:7]} H={self._format_brl(self.alert_config.eth_high)[:7]}{' ' * (width - len(f'        ETH L={self._format_brl(self.alert_config.eth_lowest)[:7]} H={self._format_brl(self.alert_config.eth_high)[:7]}'))}║\n"
        
        display_text += "╚" + "═" * width + "╝\n"
        
        return display_text
