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
    XRP = "XRP"
    BNB = "BNB"
    ADA = "ADA"
    SOL = "SOL"
    DOGE = "DOGE"
    DOT = "DOT"
    MATIC = "MATIC"
    LTC = "LTC"
    AVAX = "AVAX"
    SHIB = "SHIB"

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
        """Formata preço para BRL com casas decimais inteligentes"""
        if price < 0.01:
            # Para preços muito baixos, usa até 8 casas decimais
            formatted = f"{price:.8f}".rstrip('0').rstrip('.')
            # Se ainda for 0, usa formatação científica
            if float(formatted) == 0:
                return f"{price:.2e}"
        elif price < 1.0:
            # Para preços baixos, usa 4 casas decimais
            formatted = f"{price:.4f}".rstrip('0').rstrip('.')
        else:
            # Para preços normais, usa 2 casas decimais
            formatted = f"{price:,.2f}"
        
        # Aplica formatação brasileira (ponto para milhares, vírgula para decimais)
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    
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
    """Dados para notificações - suporte a múltiplas moedas"""
    crypto_prices: dict  # Dict[str, CryptoPrice]
    timestamp: datetime
    
    def to_dict(self) -> dict:
        """Converte para dicionário"""
        result = {
            "timestamp": self.timestamp.isoformat()
        }
        
        for symbol, crypto in self.crypto_prices.items():
            result[f"{symbol}_price"] = str(crypto.price or 0)
            result[f"{symbol}_status"] = crypto.alert_status.value
            
        return result
    
    def has_alerts(self) -> bool:
        """Verifica se alguma moeda está em alerta"""
        return any(
            crypto.alert_status in [AlertStatus.ALTA, AlertStatus.BAIXA] 
            for crypto in self.crypto_prices.values()
        )
    
    def get_alert_coins(self) -> list:
        """Retorna lista de moedas em alerta"""
        return [
            symbol for symbol, crypto in self.crypto_prices.items()
            if crypto.alert_status in [AlertStatus.ALTA, AlertStatus.BAIXA]
        ]
