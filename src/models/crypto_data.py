from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class AlertStatus(Enum):
    """Status dos alertas"""
    NORMAL = "NORMAL"
    BAIXA = "BAIXA"
    ALTA = "ALTA"

class CryptoSymbol(Enum):
    """Símbolos das criptomoedas"""
    BTC = "BTC"
    ETH = "ETH"

@dataclass
class CryptoPrice:
    """Modelo para preços de criptomoedas"""
    symbol: CryptoSymbol
    name: str
    price: Optional[float] = None
    formatted_price: str = "Carregando..."
    last_update: Optional[datetime] = None
    alert_status: AlertStatus = AlertStatus.NORMAL
    
    def update_price(self, new_price: float):
        """Atualiza o preço e timestamp"""
        self.price = new_price
        self.formatted_price = self._format_brl(new_price)
        self.last_update = datetime.now()
    
    def _format_brl(self, price: float) -> str:
        """Formata preço para BRL"""
        return f"{price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    def get_icon(self) -> str:
        """Retorna ícone baseado no status"""
        if self.alert_status == AlertStatus.BAIXA:
            return "🔴"
        elif self.alert_status == AlertStatus.ALTA:
            return "🟢"
        elif self.symbol == CryptoSymbol.BTC:
            return "🔶"
        else:  # ETH
            return "🔷"


@dataclass
class SystemStatus:
    """Status do sistema"""
    status: str = "connecting"
    btc_connected: bool = False
    eth_connected: bool = False
    last_update: Optional[datetime] = None
    
    def update_connection_status(self, btc_price: Optional[float], eth_price: Optional[float]):
        """Atualiza status das conexões"""
        self.btc_connected = btc_price is not None
        self.eth_connected = eth_price is not None
        self.status = "connected" if (self.btc_connected and self.eth_connected) else "connecting"
        self.last_update = datetime.now()


@dataclass
class NotificationData:
    """Dados para notificações"""
    btc_price: CryptoPrice
    eth_price: CryptoPrice
    timestamp: datetime
    
    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            "btc_price": str(self.btc_price.price or 0),
            "eth_price": str(self.eth_price.price or 0),
            "btc_status": self.btc_price.alert_status.value,
            "eth_status": self.eth_price.alert_status.value,
            "timestamp": self.timestamp.isoformat()
        }
