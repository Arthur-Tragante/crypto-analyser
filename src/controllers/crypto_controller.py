"""
Controller de criptomoedas
Apenas gatilhos - sem regras de negócio
"""
from flask import jsonify, Response
from ..services.crypto_service import CryptoService
from ..repositories.crypto_repository import CryptoRepository

class CryptoController:
    """Controller para endpoints de criptomoedas"""
    
    def __init__(self, repository=None, service=None):
        self.repository = repository or CryptoRepository()
        self.service = service or CryptoService(self.repository)
    
    def get_home(self):
        """Endpoint raiz com informações da API"""
        return jsonify({
            "message": "Crypto Analyser API - Versão Limpa",
            "version": "2.1",
            "endpoints": {
                "/display": "Visualização ASCII em tempo real",
                "/fcm/send-to-topic": "Enviar notificação FCM para tópico",
                "/fcm/send-to-token": "Enviar notificação FCM para token específico"
            }
        })

    def get_display(self):
        """Retorna a visualização formatada em ASCII como texto"""
        display_text = self.service.create_display_text()
        return Response(display_text, mimetype='text/plain')
    
    def get_display_auto_refresh(self):
        """Retorna página HTML com auto-refresh do display"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Crypto Analyser - Display</title>
            <meta charset="UTF-8">
            <style>
                body {{
                    background-color: #000;
                    color: #00ff00;
                    font-family: 'Courier New', monospace;
                    margin: 20px;
                    font-size: 14px;
                }}
                #display {{
                    white-space: pre;
                    border: 1px solid #00ff00;
                    padding: 10px;
                    background-color: #001100;
                }}
            </style>
        </head>
        <body>
            <h1>Crypto Analyser - Display em Tempo Real</h1>
            <div id="display">Carregando...</div>
            
            <script>
                function updateDisplay() {{
                    fetch('/display')
                        .then(response => response.text())
                        .then(data => {{
                            document.getElementById('display').textContent = data;
                        }})
                        .catch(error => {{
                            console.error('Erro:', error);
                            document.getElementById('display').textContent = 'Erro ao carregar dados';
                        }});
                }}
                
                // Atualizar a cada 2 segundos
                updateDisplay();
                setInterval(updateDisplay, 2000);
            </script>
        </body>
        </html>
        """
        return html_content
