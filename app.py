from flask import Flask, jsonify
import requests
import json
import os

app = Flask(__name__)

# Your session cookies (update these every hour from Firefox)
SESSION_COOKIES = {
    "XSRF-TOKEN": "eyJpdiI6Im00YTV0bHpGS0hlMmV4ekxVZ3graVE9PSIsInZhbHVlIjoibUxRRDY5N3dEWGdxZU4wY1F2OTlLNGpZSWpYYkpyTmJid3JzYXlrQ3F0YzF1SjlpSkdMNklldzF5UkFaK2hwTStFSUZMclEvWHVONjFtbWc5TGdXOWJBeXE4VXdXRVNTcWVUTGF3cXVpbWR3WmR0Ui9sY3EraGRTcGd6Y0xmWm8iLCJtYWMiOiIyYzQ5NGZjYWE1OWEwNDk3OGVjYWM2ZjZhYTgyN2M1M2QxZDdhYjJhZThiZjRkMWVmODEyNmY2MzU1MjJiYWFjIiwidGFnIjoiIn0%3D",
    "ivas_sms_session": "eyJpdiI6ImhORDl0c3JOTWFvWHZWMlh5Mmtjcmc9PSIsInZhbHVlIjoiWktVTmtHT0lvbi82TXNlaGh5T3NBNHZjZEUyODJDTmFUZFV3T0REcWtRQlJIV1BuSUJ2emRKWTRiTzN0MEtyUy9PUXNIRExhdmQxbXRiTXZOZTcxOUg2MWovT3VEdUxOL1BCYkkvZ0dvQlBBenBIWUxMSnEwTkVIdDdyM3E1TUUiLCJtYWMiOiJmNTViN2FiOWEyZGQwNmM3YTg3MGU1ZjVjODRkZmYwNzFjOWQ0YTdjOTIwNGUwNTIxNWI5NzBhNWE1ZDcyNDg4IiwidGFnIjoiIn0%3D",
    "_fbp": "fb.1.1781903538584.890564191345746600"
}

REPLIT_API = "https://ac2cac9c-95ba-403b-8a48-73c401db292a-00-2afievth5nt9n.kirk.replit.dev/cf-api/get-cf-clearance"

@app.route('/')
def home():
    return jsonify({'status': 'running', 'endpoint': '/sms'})

@app.route('/sms')
def get_sms():
    try:
        # Get fresh cf_clearance from Replit
        cf_resp = requests.get(REPLIT_API, timeout=120)
        cf_data = cf_resp.json()
        cf_clearance = cf_data.get('cf_clearance')
        
        if not cf_clearance:
            return jsonify({'error': 'Failed to get cf_clearance'}), 500
        
        # Add fresh cf_clearance to cookies
        cookies = SESSION_COOKIES.copy()
        cookies['cf_clearance'] = cf_clearance
        
        # Fetch SMS
        sess = requests.Session()
        for name, value in cookies.items():
            sess.cookies.set(name, value, domain='www.ivasms.com')
        
        sms_resp = sess.get(
            'https://www.ivasms.com/portal/sms/test/sms',
            params={'draw': '1', 'start': '0', 'length': '25'},
            headers={'X-Requested-With': 'XMLHttpRequest'},
            timeout=30
        )
        
        if sms_resp.status_code == 200:
            data = sms_resp.json()
            messages = []
            for row in data.get('data', []):
                msg = {
                    'sender': row.get('originator', 'N/A'),
                    'phone': row.get('termination', {}).get('test_number', 'N/A') if isinstance(row.get('termination'), dict) else 'N/A',
                    'message': row.get('messagedata', 'N/A')[:100],
                    'time': row.get('senttime', 'N/A')
                }
                messages.append(msg)
            return jsonify({'status': 'success', 'count': len(messages), 'messages': messages})
        else:
            return jsonify({'error': f'SMS fetch failed: {sms_resp.status_code}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
