"""HTML templates for web UI."""

def dashboard_html() -> str:
    """Main dashboard HTML."""
    return """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>mini-Atlas Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        .header h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        .new-session {
            background: white;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        .new-session h2 {
            margin-bottom: 20px;
            color: #333;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #555;
        }
        .form-group input, .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        .form-group input:focus, .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        .form-group textarea {
            min-height: 80px;
            resize: vertical;
        }
        .goals-input {
            font-family: monospace;
            font-size: 13px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        button:active {
            transform: translateY(0);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .sessions-list {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        .sessions-list h2 {
            margin-bottom: 20px;
            color: #333;
        }
        .session-card {
            background: #f8f9fa;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s;
            cursor: pointer;
        }
        .session-card:hover {
            border-color: #667eea;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
        }
        .session-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .session-id {
            font-family: monospace;
            font-size: 14px;
            color: #667eea;
            font-weight: 600;
        }
        .status-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-running { background: #e3f2fd; color: #1976d2; }
        .status-completed { background: #e8f5e9; color: #388e3c; }
        .status-failed { background: #ffebee; color: #d32f2f; }
        .status-stopped { background: #fafafa; color: #616161; }
        .status-waiting_human { background: #fff3e0; color: #f57c00; }
        .session-info {
            color: #666;
            font-size: 14px;
            margin: 5px 0;
        }
        .session-goals {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e0e0e0;
        }
        .session-goals ul {
            list-style: none;
            padding-left: 0;
        }
        .session-goals li {
            padding: 5px 0;
            color: #555;
        }
        .session-goals li:before {
            content: "✓ ";
            color: #667eea;
            font-weight: bold;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .error {
            background: #ffebee;
            color: #d32f2f;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        .success {
            background: #e8f5e9;
            color: #388e3c;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .pulse {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 mini-Atlas</h1>
            <p>LLM-Powered Browser Automation Agent</p>
        </div>

        <div class="new-session" style="margin-bottom: 20px;">
            <h2>💻 Komut Satırı Kullanımı (CLI)</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 15px;">
                <p style="margin-bottom: 15px; color: #555;">
                    Terminal/komut satırından da kullanabilirsiniz. İki yöntem mevcut:
                </p>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="margin-bottom: 10px; color: #333; font-size: 1.1em;">1. İnteraktif Mod (Soru-Cevap)</h3>
                    <pre style="background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 8px; overflow-x: auto; font-size: 13px;"><code>python cli.py</code></pre>
                    <p style="margin-top: 10px; color: #666; font-size: 14px;">
                        CLI size URL ve hedeflerinizi adım adım soracak.
                    </p>
                </div>

                <div>
                    <h3 style="margin-bottom: 10px; color: #333; font-size: 1.1em;">2. Direkt Mod (Komut Satırından)</h3>
                    <pre style="background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 8px; overflow-x: auto; font-size: 13px;"><code>python cli.py --url "https://example.com" \\
  --goal "Login ol" \\
  --goal "Dashboard'a git" \\
  --max-steps 20</code></pre>
                    <p style="margin-top: 10px; color: #666; font-size: 14px;">
                        Tüm parametreleri komut satırından direkt belirtebilirsiniz.
                    </p>
                </div>

                <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
                    <strong style="color: #333;">Ek Parametreler:</strong>
                    <ul style="margin-top: 10px; padding-left: 20px; color: #666; line-height: 1.8;">
                        <li><code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">--email</code> - Profil email adresi</li>
                        <li><code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">--password</code> - Profil şifresi</li>
                        <li><code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">--base-url</code> - API base URL (varsayılan: http://localhost:8000)</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="new-session">
            <h2>Yeni Oturum Başlat</h2>
            <form id="newSessionForm">
                <div class="form-group">
                    <label for="url">Başlangıç URL:</label>
                    <input type="text" id="url" name="url" placeholder="https://example.com" required>
                </div>
                <div class="form-group">
                    <label for="goals">Hedefler (her satıra bir hedef):</label>
                    <textarea id="goals" name="goals" class="goals-input" placeholder="Örnek:&#10;Login ol&#10;Dashboard'a git&#10;Ayarları aç" required></textarea>
                </div>
                <div class="form-group">
                    <label for="max_steps">Maksimum Adım (opsiyonel):</label>
                    <input type="number" id="max_steps" name="max_steps" value="20" min="1" max="100">
                </div>
                <button type="submit">Oturum Başlat</button>
            </form>
            <div id="formMessage"></div>
        </div>

        <div class="sessions-list">
            <h2>Oturumlar</h2>
            <div id="sessionsContainer">
                <div class="loading">Yükleniyor...</div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin;

        // Load sessions on page load
        document.addEventListener('DOMContentLoaded', () => {
            loadSessions();
            setInterval(loadSessions, 3000); // Refresh every 3 seconds
        });

        // Form submission
        document.getElementById('newSessionForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const goals = formData.get('goals').split('\\n').filter(g => g.trim());
            
            const data = {
                url: formData.get('url'),
                goals: goals,
                max_steps: parseInt(formData.get('max_steps')) || 20,
                session_mode: 'ephemeral'
            };

            const messageDiv = document.getElementById('formMessage');
            messageDiv.innerHTML = '<div class="loading">Başlatılıyor...</div>';

            try {
                const response = await fetch(`${API_BASE}/run`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    const result = await response.json();
                    messageDiv.innerHTML = `<div class="success">Oturum başlatıldı: ${result.session_id}</div>`;
                    e.target.reset();
                    loadSessions();
                    setTimeout(() => {
                        window.location.href = `/session/${result.session_id}`;
                    }, 1000);
                } else {
                    const error = await response.json();
                    messageDiv.innerHTML = `<div class="error">Hata: ${error.detail || 'Bilinmeyen hata'}</div>`;
                }
            } catch (error) {
                messageDiv.innerHTML = `<div class="error">Hata: ${error.message}</div>`;
            }
        });

        async function loadSessions() {
            try {
                const response = await fetch(`${API_BASE}/sessions`);
                const data = await response.json();
                displaySessions(data.sessions);
            } catch (error) {
                document.getElementById('sessionsContainer').innerHTML = 
                    `<div class="error">Oturumlar yüklenemedi: ${error.message}</div>`;
            }
        }

        function displaySessions(sessions) {
            const container = document.getElementById('sessionsContainer');
            
            if (sessions.length === 0) {
                container.innerHTML = '<div class="loading">Henüz oturum yok</div>';
                return;
            }

            container.innerHTML = sessions.map(session => `
                <div class="session-card" onclick="window.location.href='/session/${session.session_id}'">
                    <div class="session-header">
                        <span class="session-id">${session.session_id}</span>
                        <span class="status-badge status-${session.status}">${getStatusText(session.status)}</span>
                    </div>
                    <div class="session-info">
                        <strong>Adımlar:</strong> ${session.steps} |
                        <strong>Oluşturulma:</strong> ${new Date(session.created_at).toLocaleString('tr-TR')}
                    </div>
                    <div class="session-goals">
                        <strong>Hedefler:</strong>
                        <ul>
                            ${session.goals.map(g => `<li>${g}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `).join('');
        }

        function getStatusText(status) {
            const statusMap = {
                'running': 'Çalışıyor',
                'completed': 'Tamamlandı',
                'failed': 'Başarısız',
                'stopped': 'Durduruldu',
                'waiting_human': 'İnsan Bekliyor'
            };
            return statusMap[status] || status;
        }
    </script>
</body>
</html>"""


def session_detail_html() -> str:
    """Session detail page HTML."""
    return """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oturum Detayı - mini-Atlas</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            color: #333;
            font-size: 1.8em;
        }
        .back-link {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            padding: 10px 20px;
            border: 2px solid #667eea;
            border-radius: 8px;
            transition: all 0.3s;
        }
        .back-link:hover {
            background: #667eea;
            color: white;
        }
        .status-panel {
            background: white;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        .status-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }
        .info-item {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .info-item label {
            display: block;
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
            text-transform: uppercase;
        }
        .info-item value {
            display: block;
            font-size: 18px;
            font-weight: 600;
            color: #333;
        }
        .steps-panel {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        .step-item {
            border-left: 4px solid #e0e0e0;
            padding: 20px;
            margin-bottom: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            transition: all 0.3s;
        }
        .step-item:hover {
            border-left-color: #667eea;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
        }
        .step-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .step-number {
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
        }
        .step-time {
            font-size: 12px;
            color: #999;
        }
        .step-action {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 13px;
        }
        .step-result {
            padding: 10px;
            margin-top: 10px;
            border-radius: 5px;
        }
        .result-success {
            background: #e8f5e9;
            color: #2e7d32;
        }
        .result-error {
            background: #ffebee;
            color: #c62828;
        }
        .screenshot {
            margin-top: 15px;
            max-width: 100%;
            border-radius: 8px;
            border: 2px solid #e0e0e0;
        }
        .status-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            display: inline-block;
        }
        .status-running { background: #e3f2fd; color: #1976d2; }
        .status-completed { background: #e8f5e9; color: #388e3c; }
        .status-failed { background: #ffebee; color: #d32f2f; }
        .status-stopped { background: #fafafa; color: #616161; }
        .status-waiting_human { background: #fff3e0; color: #f57c00; }
        .captcha-warning {
            background: #fff3e0;
            border: 2px solid #f57c00;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .captcha-warning h3 {
            color: #f57c00;
            margin-bottom: 10px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            opacity: 0.9;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Oturum Detayı</h1>
            <a href="/" class="back-link">← Ana Sayfa</a>
        </div>

        <div id="statusPanel" class="status-panel">
            <div class="loading">Yükleniyor...</div>
        </div>

        <div id="stepsPanel" class="steps-panel">
            <h2>Adım Geçmişi</h2>
            <div id="stepsContainer" class="loading">Yükleniyor...</div>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        const sessionId = window.location.pathname.split('/').pop();

        // Load session details
        async function loadSessionDetails() {
            try {
                // Get full session data
                const response = await fetch(`${API_BASE}/api/session/${sessionId}/full`);
                if (!response.ok) {
                    throw new Error('Oturum bulunamadı');
                }
                const session = await response.json();

                // Display status
                displayStatus(session);
                
                // Display steps
                displaySteps(session.steps);
                
                // Auto-refresh if session is still active
                if (session.status === 'running' || session.status === 'waiting_human') {
                    setTimeout(loadSessionDetails, 2000);
                }
            } catch (error) {
                document.getElementById('statusPanel').innerHTML = 
                    `<div style="color: #d32f2f;">Hata: ${error.message}</div>`;
            }
        }

        function displayStatus(session) {
            const panel = document.getElementById('statusPanel');
            
            const captchaWarning = session.status === 'waiting_human' ? `
                <div class="captcha-warning">
                    <h3>⚠️ CAPTCHA Tespit Edildi</h3>
                    <p>Agent bir CAPTCHA ile karşılaştı ve insan müdahalesi bekliyor.</p>
                    <p>Tarayıcıda CAPTCHA'yı çözün ve devam edin:</p>
                    <button onclick="continueSession()">Devam Et</button>
                </div>
            ` : '';

            panel.innerHTML = `
                <h2>Oturum Durumu</h2>
                <div class="status-info">
                    <div class="info-item">
                        <label>Durum</label>
                        <value><span class="status-badge status-${session.status}">${getStatusText(session.status)}</span></value>
                    </div>
                    <div class="info-item">
                        <label>Adımlar</label>
                        <value>${session.steps_count} / ${session.steps.length}</value>
                    </div>
                    <div class="info-item">
                        <label>Mevcut URL</label>
                        <value style="font-size: 14px; word-break: break-all;">${session.current_url}</value>
                    </div>
                    <div class="info-item">
                        <label>Hedefler</label>
                        <value style="font-size: 14px;">${session.goals.length} hedef</value>
                    </div>
                </div>
                <div style="margin-top: 15px;">
                    <strong>Hedefler:</strong>
                    <ul style="list-style: none; padding-left: 0; margin-top: 5px;">
                        ${session.goals.map(g => `<li style="padding: 3px 0;">✓ ${g}</li>`).join('')}
                    </ul>
                </div>
                ${captchaWarning}
            `;
        }

        function displaySteps(steps) {
            const container = document.getElementById('stepsContainer');
            
            if (steps.length === 0) {
                container.innerHTML = '<div class="loading">Henüz adım yok</div>';
                return;
            }

            container.innerHTML = steps.map(step => {
                const actionHtml = step.action ? `
                    <div class="step-action">
                        <strong>İşlem:</strong> ${step.action.action}<br>
                        ${step.action.selector ? `<strong>Selector:</strong> ${step.action.selector}<br>` : ''}
                        ${step.action.value ? `<strong>Değer:</strong> ${step.action.value}` : ''}
                    </div>
                ` : '';

                const resultHtml = step.result ? `
                    <div class="step-result result-${step.error ? 'error' : 'success'}">
                        ${step.result}
                    </div>
                ` : '';

                const errorHtml = step.error ? `
                    <div class="step-result result-error">
                        <strong>Hata:</strong> ${step.error}
                    </div>
                ` : '';

                const screenshotHtml = step.screenshot ? `
                    <img src="data:image/png;base64,${step.screenshot}" 
                         alt="Screenshot" 
                         class="screenshot"
                         onclick="this.style.maxWidth = this.style.maxWidth === '100%' ? 'none' : '100%'">
                ` : '';

                return `
                    <div class="step-item">
                        <div class="step-header">
                            <span class="step-number">#${step.step_number}</span>
                            <span class="step-time">${new Date(step.timestamp).toLocaleString('tr-TR')}</span>
                        </div>
                        <div style="margin: 10px 0; color: #666; font-size: 14px;">
                            <strong>URL:</strong> ${step.observation.url}<br>
                            <strong>Başlık:</strong> ${step.observation.title}<br>
                            <strong>Elementler:</strong> ${step.observation.element_count} (Formlar: ${step.observation.has_forms ? 'Var' : 'Yok'}, Butonlar: ${step.observation.has_buttons ? 'Var' : 'Yok'})
                        </div>
                        ${step.reasoning ? `<div style="margin: 10px 0; padding: 10px; background: #f0f0f0; border-radius: 5px; font-style: italic;">${step.reasoning}</div>` : ''}
                        ${actionHtml}
                        ${resultHtml}
                        ${errorHtml}
                        ${screenshotHtml}
                        ${step.duration_ms ? `<div style="margin-top: 10px; font-size: 12px; color: #999;">Süre: ${step.duration_ms}ms</div>` : ''}
                    </div>
                `;
            }).join('');
        }

        function getStatusText(status) {
            const statusMap = {
                'running': 'Çalışıyor',
                'completed': 'Tamamlandı',
                'failed': 'Başarısız',
                'stopped': 'Durduruldu',
                'waiting_human': 'İnsan Bekliyor'
            };
            return statusMap[status] || status;
        }

        async function continueSession() {
            try {
                const response = await fetch(`${API_BASE}/agent/continue/${sessionId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ note: 'CAPTCHA solved manually' })
                });
                
                if (response.ok) {
                    alert('Oturum devam ediyor...');
                    loadSessionDetails();
                } else {
                    alert('Hata: Oturum devam ettirilemedi');
                }
            } catch (error) {
                alert(`Hata: ${error.message}`);
            }
        }

        // Start loading
        loadSessionDetails();
    </script>
</body>
</html>"""
