
import os
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health_check():
    status = {
        'status': 'healthy',
        'database': False,
        'openai': bool(os.getenv('OPENAI_API_KEY')),
        'mistral': bool(os.getenv('MISTRAL_API_KEY'))
    }
    
    # Test database connection
    try:
        conn = psycopg2.connect(os.getenv('NEON_CONNECTION_STRING'))
        conn.close()
        status['database'] = True
    except:
        status['database'] = False
    
    return jsonify(status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
