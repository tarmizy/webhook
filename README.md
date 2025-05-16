# GitLab Auto-Pull Webhook

Webhook sederhana yang otomatis melakukan `git pull` pada repository lokal setiap kali ada push ke GitLab.

## Fitur

- Otomatis melakukan `git pull` saat terjadi push ke repository GitLab
- Verifikasi token untuk keamanan
- Logging untuk pemantauan dan debugging
- Dapat dikonfigurasi sebagai layanan systemd untuk ketersediaan tinggi

## Prasyarat

- Python 3.6+
- Flask
- Git sudah terinstal dan terkonfigurasi di server
- Server Ubuntu (atau distribusi Linux lainnya)
- Akses ke repository GitLab

## Instalasi

### 1. Menginstal Paket yang Dibutuhkan

```bash
# Update repository paket
sudo apt update

# Instal Python dan pip jika belum ada
sudo apt install python3 python3-pip git

# Instal Flask menggunakan pip
pip3 install flask
```

### 2. Menyiapkan Webhook (optional)

```bash
# Buat direktori untuk webhook
mkdir -p ~/webhook
cd ~/webhook

# Buat file requirements.txt
echo "flask==2.0.1" > requirements.txt

# Instalasi dari requirements.txt
pip3 install -r requirements.txt
```

### 3. Membuat Script Webhook

Buat file `webhook.py` di direktori `~/webhook`:

```bash
nano ~/webhook/webhook.py
```

Masukkan kode webhook berikut:

```python
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
REPO_PATH = '/path/to/your/repository/tms'

# Kunci rahasia webhook (atur ini sama dengan yang di GitLab)
SECRET_TOKEN = 'your_secret_token_here'

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
```

**Penting:** Ganti `REPO_PATH` dengan path sebenarnya ke repository Anda dan `SECRET_TOKEN` dengan token rahasia pilihan Anda.

### 4. Membuat Service Systemd

Buat file service systemd untuk menjalankan webhook sebagai service:

```bash
sudo nano /etc/systemd/system/gitlab-webhook.service
```

Masukkan konfigurasi berikut:

```
[Unit]
Description=GitLab Webhook Server
After=network.target

[Service]
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/webhook
ExecStart=/usr/bin/python3 /home/YOUR_USERNAME/webhook/webhook.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=gitlab-webhook

[Install]
WantedBy=multi-user.target
```

Ganti `YOUR_USERNAME` dengan nama pengguna Anda di server.

### 5. Mengaktifkan dan Memulai Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable gitlab-webhook
sudo systemctl start gitlab-webhook
```

### 6. Memeriksa Status Service

```bash
sudo systemctl status gitlab-webhook
```

### 7. Melihat Log

```bash
tail -f ~/webhook/webhook.log
```

## Konfigurasi GitLab Webhook

1. Buka repositori GitLab di browser
2. Pergi ke **Settings > Webhooks** (atau **Settings > Integrations** di versi baru)
3. Masukkan URL Webhook: `http://your_server_ip:5000/webhook`
4. Masukkan **Secret Token** yang sama dengan yang Anda tentukan di script webhook
5. Pilih peristiwa yang akan memicu webhook (biasanya "Push events")
6. Jika menggunakan HTTP (bukan HTTPS), nonaktifkan "Enable SSL verification"
7. Klik "Add webhook"

## Pengujian Webhook

### Pengujian dari GitLab

1. Di halaman Webhooks GitLab, cari webhook yang baru dibuat
2. Klik tombol "Test" dan pilih "Push events"
3. Periksa log webhook untuk memastikan berfungsi:
   ```bash
   tail -f ~/webhook/webhook.log
   ```

### Pengujian Manual dengan curl

```bash
curl -X POST http://your_server_ip:5000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Gitlab-Token: your_secret_token_here" \
  -d '{"repository": {"name": "test-repo"}}'
```

## Troubleshooting

### Webhook tidak berjalan
```bash
sudo systemctl status gitlab-webhook
sudo journalctl -u gitlab-webhook
```

### Webhook menerima request tetapi tidak melakukan pull
```bash
# Periksa izin di direktori repository
ls -la /path/to/your/repository/tms

# Pastikan kredensial Git dikonfigurasi dengan benar
cd /path/to/your/repository/tms
git config credential.helper store
git pull  # Pastikan tidak meminta password
```

### GitLab webhook test menunjukkan error
- Periksa URL webhook
- Periksa token rahasia
- Periksa firewall server (port 5000 harus terbuka)
- Periksa log webhook untuk informasi lebih lanjut

## Menggunakan Nginx sebagai Proxy (Opsional)

Untuk produksi, disarankan menggunakan Nginx sebagai proxy:

### Instalasi Nginx
```bash
sudo apt install nginx
```

### Konfigurasi Nginx
```bash
sudo nano /etc/nginx/sites-available/webhook
```

Masukkan konfigurasi berikut:
```
server {
    listen 80;
    server_name your_server_domain_or_ip;

    location /webhook {
        proxy_pass http://localhost:5000/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Aktifkan konfigurasi dan restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/webhook /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Keamanan

- Selalu gunakan token rahasia yang kuat dan unik
- Pertimbangkan untuk menggunakan HTTPS dengan Let's Encrypt
- Batasi akses ke endpoint webhook hanya dari IP GitLab jika memungkinkan
- Berikan izin minimal yang diperlukan untuk repository Git

## Lisensi

[MIT License](https://opensource.org/licenses/MIT)
