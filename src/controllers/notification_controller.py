"""
Controller de notificações
Apenas gatilhos - sem regras de negócio
"""
from flask import jsonify, request
from datetime import datetime


class NotificationController:
    """Controller para endpoints de notificações"""
    
    def __init__(self, fcm_service=None):
        self.fcm_service = fcm_service
    
    def send_fcm_to_topic(self):
        """Envia push notification para tópico público"""
        try:
            if not self.fcm_service:
                return jsonify({"error": "FCM não está disponível"}), 503
            
            data = request.json or {}
            title = data.get('title', 'Crypto Alert')
            body = data.get('body', 'Nova atualização disponível')
            custom_data = data.get('data', {})
            
            success = self.fcm_service.send_to_topic("crypto_alerts", title, body, custom_data)
            
            if success:
                return jsonify({
                    "status": "success",
                    "message": f"Push enviado para tópico público: crypto_alerts",
                    "topic": "crypto_alerts"
                })
            else:
                return jsonify({"error": "Falha ao enviar push"}), 500
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    def send_fcm_to_token(self):
        """Envia push notification para token específico"""
        try:
            if not self.fcm_service:
                return jsonify({"error": "FCM não está disponível"}), 503
            
            data = request.json or {}
            token = data.get('token')
            title = data.get('title', 'Crypto Alert - Teste Direto')
            body = data.get('body', 'Teste de notificação para seu dispositivo específico')
            custom_data = data.get('data', {})
            
            if not token:
                return jsonify({"error": "Token FCM é obrigatório"}), 400
            
            success = self.fcm_service.send_to_token(token, title, body, custom_data)
            
            if success:
                return jsonify({
                    "status": "success",
                    "message": f"Push enviado para token específico",
                    "token_preview": f"{token[:20]}...{token[-10:]}"
                })
            else:
                return jsonify({"error": "Falha ao enviar push"}), 500
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500
