"""
Utilitaires réseau
"""

import socket
import requests
from flask import request

def get_client_ip(req=None):
    """Récupère l'IP réelle du client (derrière proxy)"""
    if req is None:
        req = request
    
    # Headers proxy
    forwarded = req.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    
    real_ip = req.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    return req.remote_addr

def is_local_ip(ip):
    """Vérifie si une IP est locale"""
    local_ranges = [
        '127.',
        '192.168.',
        '10.',
        '172.16.', '172.17.', '172.18.', '172.19.',
        '172.20.', '172.21.', '172.22.', '172.23.',
        '172.24.', '172.25.', '172.26.', '172.27.',
        '172.28.', '172.29.', '172.30.', '172.31.'
    ]
    return any(ip.startswith(prefix) for prefix in local_ranges)

def check_port(host, port, timeout=2):
    """Vérifie si un port est ouvert"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def get_hostname():
    """Récupère le nom d'hôte"""
    return socket.gethostname()

def get_public_ip():
    """Récupère l'IP publique (pour monitoring)"""
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        return response.text
    except:
        return None