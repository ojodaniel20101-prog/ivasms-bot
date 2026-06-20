from flask import Flask, request, jsonify
import requests
import json
import logging
from bs4 import BeautifulSoup
import threading
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class IVASSMSClient:
    def __init__(self):
        self.base_url = "https://www.ivasms.com"
        self.logged_in = False
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def login(self, email, password):
        try:
            # Get login page for CSRF token
            login_page = self.session.get(f"{self.base_url}/login")
            soup = BeautifulSoup(login_page.text, 'html.parser')
            token = soup.find('input', {'name': '_token'})
            csrf_token = token['value'] if token else ''
            
            # Login
            login_data = {
                '_token': csrf_token,
                'email': email,
                'password': password
            }
            
            response = self.session.post(f"{self.base_url}/login", data=login_data)
            
            if response.status_code == 200 and 'portal' in response.url:
                self.logged_in = True
                logger.info("Login successful!")
                return True
            else:
                logger.error(f"Login failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def get_sms(self, limit=25):
        if not self.logged_in:
            return []
        
        try:
            params = {
                'draw': '1',
                'start': '0',
                'length': str(limit),
                'search[value]': ''
            }
            
            headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'{self.base_url}/portal/sms/test/sms'
            }
            
            response = self.session.get(
                f"{self.base_url}/portal/sms/test/sms",
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                messages = []
                for row in data.get('data', []):
                    msg = {
                        'sender': row.get('originator', 'N/A'),
                        'phone': row.get('termination', {}).get('test_number', 'N/A') if isinstance(row.get('termination'), dict) else 'N/A',
                        'message': row.get('messagedata', 'N/A'),
                        'time': row.get('senttime', 'N/A')
                    }
                    messages.append(msg)
                return messages
            return []
        except Exception as e:
            logger.error(f"Error fetching SMS: {e}")
            return []

# Initialize client
client = IVASSMSClient()

@app.route('/')
def home():
    return jsonify({'status': 'running', 'endpoint': '/sms'})

@app.route('/sms')
def get_sms():
    email = 'sandunisithara100@gmail.com'
    password = 'eA*M*EP&6URb.C9'
    
    if not client.logged_in:
        if not client.login(email, password):
            return jsonify({'error': 'Login failed'}), 401
    
    messages = client.get_sms(limit=25)
    return jsonify({'status': 'success', 'messages': messages, 'count': len(messages)})

# Keep alive function
def keep_alive():
    while True:
        try:
            time.sleep(600)
            requests.get('http://localhost:5000/', timeout=5)
        except:
            pass

threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
