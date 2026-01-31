#!/usr/bin/env python3
"""
StacksOrbit Wallet Connect - QR Code Authentication
Generates a QR code for wallet connection and retrieves the address for deployment
"""

import http.server
import socketserver
import webbrowser
import json
import threading
import time
from pathlib import Path

# HTML template for wallet connection
WALLET_CONNECT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StacksOrbit - Connect Wallet</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
        }
        .container {
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            max-width: 500px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        h1 { margin-bottom: 10px; font-size: 28px; }
        .subtitle { color: #888; margin-bottom: 30px; }
        .logo { font-size: 60px; margin-bottom: 20px; }
        .btn {
            background: linear-gradient(135deg, #5546ff 0%, #7c3aed 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 18px;
            border-radius: 12px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            margin: 10px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(85,70,255,0.3);
        }
        .btn:disabled {
            background: #444;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            background: rgba(255,255,255,0.05);
        }
        .status.success { background: rgba(34,197,94,0.2); border: 1px solid #22c55e; }
        .status.error { background: rgba(239,68,68,0.2); border: 1px solid #ef4444; }
        .address {
            font-family: monospace;
            font-size: 14px;
            word-break: break-all;
            background: rgba(0,0,0,0.3);
            padding: 10px;
            border-radius: 8px;
            margin-top: 10px;
        }
        .info { margin-top: 20px; font-size: 14px; color: #888; }
        .qr-section { margin: 20px 0; }
        #qrcode { 
            display: inline-block; 
            padding: 15px; 
            background: white; 
            border-radius: 10px;
            margin: 10px 0;
        }
        .hidden { display: none; }
        .balance { font-size: 24px; color: #22c55e; margin: 10px 0; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/qrcode@1.5.3/build/qrcode.min.js"></script>
</head>
<body>
    <div class="container">
        <div class="logo">🚀</div>
        <h1>StacksOrbit</h1>
        <p class="subtitle">Connect your Stacks wallet for testnet deployment</p>
        
        <div id="connect-section">
            <button class="btn" id="connectBtn" onclick="connectWallet()">
                Connect Leather/Xverse Wallet
            </button>
            
            <div class="qr-section hidden" id="qr-section">
                <p>Or scan with mobile wallet:</p>
                <div id="qrcode"></div>
            </div>
        </div>
        
        <div id="status" class="status hidden"></div>
        
        <div class="info">
            <p>Network: <strong>Testnet</strong></p>
            <p>This will connect your wallet for contract deployment</p>
        </div>
    </div>

    <script>
        let connectedAddress = null;
        
        async function connectWallet() {
            const btn = document.getElementById('connectBtn');
            const status = document.getElementById('status');
            
            btn.disabled = true;
            btn.textContent = 'Connecting...';
            
            // Check for Stacks wallet
            if (typeof window.StacksProvider !== 'undefined' || 
                typeof window.LeatherProvider !== 'undefined' ||
                typeof window.XverseProviders !== 'undefined') {
                
                try {
                    // Try Leather/Hiro Wallet first
                    const provider = window.StacksProvider || window.LeatherProvider;
                    
                    if (provider) {
                        const response = await provider.request({
                            method: 'stx_requestAccounts'
                        });
                        
                        if (response && response.addresses) {
                            const testnetAddr = response.addresses.find(a => 
                                a.address.startsWith('ST')
                            );
                            if (testnetAddr) {
                                connectedAddress = testnetAddr.address;
                                showSuccess(connectedAddress);
                                sendToServer(connectedAddress);
                                return;
                            }
                        }
                    }
                    
                    // Try Xverse
                    if (window.XverseProviders) {
                        const xverse = window.XverseProviders.StacksProvider;
                        const response = await xverse.request('getAddresses', {});
                        if (response.result && response.result.addresses) {
                            const testnetAddr = response.result.addresses.find(a => 
                                a.address.startsWith('ST')
                            );
                            if (testnetAddr) {
                                connectedAddress = testnetAddr.address;
                                showSuccess(connectedAddress);
                                sendToServer(connectedAddress);
                                return;
                            }
                        }
                    }
                    
                    showError('Could not get testnet address. Make sure wallet is on testnet.');
                } catch (err) {
                    showError('Connection failed: ' + err.message);
                }
            } else {
                showError('No Stacks wallet detected. Please install Leather or Xverse wallet.');
                showQRCode();
            }
            
            btn.disabled = false;
            btn.textContent = 'Connect Leather/Xverse Wallet';
        }
        
        function showSuccess(address) {
            const status = document.getElementById('status');
            status.className = 'status success';
            status.innerHTML = `
                <p>✅ Wallet Connected!</p>
                <div class="address">${address}</div>
                <p style="margin-top: 15px; color: #22c55e;">
                    Address saved. You can close this window and return to StacksOrbit CLI.
                </p>
            `;
            status.classList.remove('hidden');
            
            // Fetch balance
            fetchBalance(address);
        }
        
        function showError(message) {
            const status = document.getElementById('status');
            status.className = 'status error';
            status.innerHTML = `<p>❌ ${message}</p>`;
            status.classList.remove('hidden');
        }
        
        function showQRCode() {
            const qrSection = document.getElementById('qr-section');
            qrSection.classList.remove('hidden');
            
            // Generate QR code with wallet connect URL
            const connectUrl = window.location.href;
            QRCode.toCanvas(document.createElement('canvas'), connectUrl, {
                width: 200,
                margin: 2,
                color: { dark: '#000', light: '#fff' }
            }, function(error, canvas) {
                if (!error) {
                    document.getElementById('qrcode').appendChild(canvas);
                }
            });
        }
        
        async function fetchBalance(address) {
            try {
                const response = await fetch(
                    `https://api.testnet.hiro.so/extended/v1/address/${address}/balances`
                );
                const data = await response.json();
                const stxBalance = parseInt(data.stx?.balance || 0) / 1000000;
                
                const status = document.getElementById('status');
                status.innerHTML += `<p class="balance">Balance: ${stxBalance.toFixed(6)} STX</p>`;
            } catch (err) {
                console.error('Failed to fetch balance:', err);
            }
        }
        
        function sendToServer(address) {
            fetch('/wallet-connected', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ address: address })
            }).catch(err => console.error('Failed to notify server:', err));
        }
    </script>
</body>
</html>
"""

class WalletConnectHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for wallet connection"""
    
    connected_address = None
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(WALLET_CONNECT_HTML.encode())
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/wallet-connected':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            WalletConnectHandler.connected_address = data.get('address')
            print(f"\n✅ Wallet connected: {WalletConnectHandler.connected_address}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        pass  # Suppress logging


def start_wallet_connect_server(port=8765):
    """Start the wallet connect server and open browser"""
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           🚀 StacksOrbit Wallet Connect                      ║
╠══════════════════════════════════════════════════════════════╣
║  Opening browser for wallet connection...                    ║
║                                                              ║
║  If browser doesn't open, visit:                             ║
║  http://localhost:{port}                                        ║
║                                                              ║
║  Scan the QR code with your mobile Stacks wallet             ║
║  or click "Connect" if using browser extension               ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    with socketserver.TCPServer(("", port), WalletConnectHandler) as httpd:
        # Open browser
        webbrowser.open(f'http://localhost:{port}')
        
        print("Waiting for wallet connection... (Press Ctrl+C to cancel)")
        
        # Wait for connection
        timeout = 300  # 5 minutes
        start_time = time.time()
        
        while WalletConnectHandler.connected_address is None:
            httpd.handle_request()
            if time.time() - start_time > timeout:
                print("\n⏰ Timeout waiting for wallet connection")
                return None
        
        address = WalletConnectHandler.connected_address
        
        # Save to config
        save_wallet_address(address)
        
        return address


def save_wallet_address(address):
    """Save the connected wallet address to .env"""
    env_path = Path('.env')
    
    if env_path.exists():
        content = env_path.read_text()
        if 'SYSTEM_ADDRESS=' in content:
            # Update existing
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith('SYSTEM_ADDRESS='):
                    new_lines.append(f'SYSTEM_ADDRESS={address}')
                else:
                    new_lines.append(line)
            env_path.write_text('\n'.join(new_lines))
        else:
            # Append
            with open(env_path, 'a') as f:
                f.write(f'\nSYSTEM_ADDRESS={address}\n')
    else:
        # Create new
        env_path.write_text(f'SYSTEM_ADDRESS={address}\nNETWORK=testnet\n')
    
    print(f"\n✅ Saved wallet address to .env: {address}")


if __name__ == '__main__':
    import sys
    
    port = 8765
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    
    address = start_wallet_connect_server(port)
    
    if address:
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║  ✅ Wallet Connected Successfully!                           ║
╠══════════════════════════════════════════════════════════════╣
║  Address: {address[:20]}...{address[-10:]}
║                                                              ║
║  Next steps:                                                 ║
║  1. Set DEPLOYER_PRIVKEY as environment variable             ║
║  2. Run: python stacksorbit_cli.py deploy --network testnet  ║
╚══════════════════════════════════════════════════════════════╝
""")
