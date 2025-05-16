from flask import Flask, request, jsonify
import subprocess
import os
import hmac
import hashlib
import logging

# Konfigurasi logging
logging.basicConfig(
    filename='webhook.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

# Ubah ini ke direktori repository Anda
REPO_PATH = 'PATH REPO IN SERVER'

# Kunci rahasia webhook (atur ini sama dengan yang di GitLab)
SECRET_TOKEN = 'TOKENGIT'

@app.route('/webhook', methods=['POST'])
def webhook():
    # Mencatat request yang masuk
    logging.info("Menerima webhook request")
    
    # Validasi header
    if 'X-Gitlab-Token' not in request.headers:
        logging.warning("Tidak ada token GitLab dalam header")
        return jsonify({'status': 'error', 'message': 'No GitLab token in header'}), 401
        
    # Validasi token
    token = request.headers.get('X-Gitlab-Token')
    if token != SECRET_TOKEN:
        logging.warning("Token tidak valid")
        return jsonify({'status': 'error', 'message': 'Invalid token'}), 401
    
    # Dapatkan informasi dari payload
    data = request.json
    logging.info(f"Webhook untuk repository: {data.get('repository', {}).get('name')}")
    
    try:
        # Pindah ke direktori repository
        os.chdir(REPO_PATH)
        logging.info(f"Berpindah ke direktori: {REPO_PATH}")
        
        # Jalankan git pull
        result = subprocess.check_output(['git', 'pull'], stderr=subprocess.STDOUT)
        output = result.decode('utf-8')
        logging.info(f"Git pull berhasil: {output}")
        
        return jsonify({
            'status': 'success',
            'message': 'Repository updated successfully',
            'output': output
        }), 200
        
    except subprocess.CalledProcessError as e:
        error_message = e.output.decode('utf-8')
        logging.error(f"Error saat melakukan git pull: {error_message}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update repository',
            'error': error_message
        }), 500
    except Exception as e:
        logging.error(f"Error tidak terduga: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Unexpected error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Jangan lupa perbarui path repository yang benar
    if not os.path.exists(REPO_PATH):
        logging.critical(f"Repository path tidak valid: {REPO_PATH}")
        print(f"ERROR: Repository path tidak valid: {REPO_PATH}")
        exit(1)
        
    logging.info("Webhook server dimulai")
    app.run(host='0.0.0.0', port=5000)
