"""
Serviço Firebase Cloud Messaging refatorado
Seguindo melhores práticas
"""
import jwt
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from ..config.settings import settings


class FCMService:
    """Serviço FCM com Service Account JWT"""
    
    def __init__(self, service_account_path: str = "service-account.json"):
        self.service_account_path = service_account_path
        self._load_service_account()
        self._setup_urls()
        self._reset_token_cache()
    
    def _load_service_account(self):
        """Carrega credenciais do service account"""
        with open(self.service_account_path, 'r') as f:
            self.service_account = json.load(f)
        
        self.project_id = self.service_account["project_id"]
        self.private_key = self.service_account["private_key"]
        self.client_email = self.service_account["client_email"]
    
    def _setup_urls(self):
        """Configura URLs da API"""
        self.token_url = "https://oauth2.googleapis.com/token"
        self.fcm_url = f"https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send"
    
    def _reset_token_cache(self):
        """Reseta cache do token"""
        self.access_token: Optional[str] = None
        self.token_expires: Optional[datetime] = None
    
    def _create_jwt(self) -> str:
        """Cria JWT para autenticação"""
        now = int(time.time())
        
        payload = {
            "iss": self.client_email,
            "scope": "https://www.googleapis.com/auth/firebase.messaging",
            "aud": self.token_url,
            "iat": now,
            "exp": now + 3600  # 1 hora
        }
        
        return jwt.encode(payload, self.private_key, algorithm="RS256")
    
    def _get_access_token(self) -> Optional[str]:
        """Obtém access token usando JWT"""
        try:
            if (self.access_token and self.token_expires and 
                datetime.now() < self.token_expires):
                return self.access_token
            
            jwt_token = self._create_jwt()
            
            data = {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt_token
            }
            
            response = requests.post(self.token_url, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires = datetime.now() + timedelta(seconds=expires_in - 300)

                return self.access_token
            else:
                print(f"Erro ao obter access token: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Erro JWT: {e}")
            return None
    
    def _build_payload(self, topic: str, title: str, body: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Constrói payload da mensagem FCM"""
        return {
            "message": {
                "topic": topic,
                "notification": {
                    "title": title,
                    "body": body
                },
                "data": data,
                "android": {
                    "priority": "high",
                    "notification": {
                        "sound": "default",
                        "icon": "ic_notification",
                        "color": "#FF6600",
                        "channel_id": "crypto_alerts"
                    }
                }
            }
        }
    
    def _send_request(self, payload: Dict[str, Any], access_token: str) -> requests.Response:
        """Envia requisição para FCM"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        return requests.post(
            self.fcm_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
    
    def _handle_response(self, response: requests.Response, topic: str, title: str) -> bool:
        """Processa resposta da API FCM"""
        
        if response.status_code == 200:
            result = response.json()
            return True
        else:
            print(f"Erro FCM: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def send_to_topic(self, topic: str, title: str, body: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Envia push notification para tópico"""
        try:
            access_token = self._get_access_token()
            if not access_token:
                return False
            
            payload = self._build_payload(topic, title, body, data or {})
            response = self._send_request(payload, access_token)
            
            return self._handle_response(response, topic, title)
            
        except Exception as e:
            print(f"Erro ao enviar FCM: {e}")
            return False
    
    def send_to_token(self, token: str, title: str, body: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Envia push notification para token específico"""
        try:
            access_token = self._get_access_token()
            if not access_token:
                return False
            
            payload = self._build_token_payload(token, title, body, data or {})
            response = self._send_request(payload, access_token)
            
            return self._handle_token_response(response, token, title)
            
        except Exception as e:
            print(f"Erro ao enviar FCM para token: {e}")
            return False
    
    def _build_token_payload(self, token: str, title: str, body: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Constrói payload da mensagem FCM para token específico"""
        return {
            "message": {
                "token": token,
                "notification": {
                    "title": title,
                    "body": body
                },
                "data": data,
                "android": {
                    "priority": "high",
                    "notification": {
                        "sound": "default",
                        "click_action": "FLUTTER_NOTIFICATION_CLICK"
                    }
                }
            }
        }
    
    def _handle_token_response(self, response: requests.Response, token: str, title: str) -> bool:
        """Processa resposta do FCM para token específico"""
        if response.status_code == 200:
            print(f"✅ FCM enviado para token: {title}")
            return True
        else:
            print(f"❌ Erro FCM (token): {response.status_code}")
            print(f"Response: {response.text}")
            return False


fcm_service = FCMService()
