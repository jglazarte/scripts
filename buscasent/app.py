import os
import re
import html
from flask import Flask, render_template_string, request, jsonify, abort

app = Flask(__name__)

# Usa siempre la carpeta donde está ubicado este archivo app.py
CARPETA_SENTENCIAS = os.path.dirname(os.path.abspath(__file__))

CSS_COMUN = """
    :root {
        --bg-dark: #0f172a;
        --panel-bg: rgba(30, 41, 59, 0.7);
        --panel-border: rgba(255, 255, 255, 0.1);
        --accent: #38bdf8;
        --accent-hover: #0ea5e9;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
        --chat-user: #0284c7;
        --chat-system: rgba(255, 255, 255, 0.05);
        --highlight: #fef08a;
        --highlight-text: #854d0e;
    }
    
    body { 
        background: radial-gradient(circle at top right, #1e293b, var(--bg-dark)); 
        color: var(--text-main);
        font-family: 'Inter', sans-serif;
        margin: 0;
        height: 100vh;
        overflow: hidden;
    }

    * { box-sizing: border-box; }
    
    .term-highlight { 
        background-color: var(--highlight); 
        color: var(--highlight-text); 
        font-weight: 600; 
        padding: 0 4px; 
        border-radius: 4px;
    }
"""

HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Buscador de Sentencias Local</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        {CSS_COMUN}
        
        .layout {{
            display: flex;
            height: 100vh;
            width: 100vw;
        }}
        
        /* Main Chat Area (Left) */
        .main-chat {{
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }}
        
        /* Header */
        .header {{
            padding: 24px;
            border-bottom: 1px solid var(--panel-border);
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(12px);
            z-index: 10;
        }}
        .header h1 {{ margin: 0; font-size: 20px; font-weight: 600; letter-spacing: 0.5px; display:flex; align-items:center; gap: 10px; }}
        .header h1 span {{ color: var(--accent); }}
        
        /* Messages Container */
        .messages-container {{
            flex: 1;
            overflow-y: auto;
            padding: 30px;
            display: flex;
            flex-direction: column;
            gap: 24px;
            scroll-behavior: smooth;
        }}
        
        /* Chat Bubbles */
        .message {{
            max-width: 85%;
            padding: 20px 24px;
            border-radius: 20px;
            font-size: 15px;
            line-height: 1.6;
            animation: fadeIn 0.3s ease;
        }}
        
        .msg-user {{
            align-self: flex-end;
            background: var(--chat-user);
            color: white;
            border-bottom-right-radius: 4px;
            box-shadow: 0 4px 15px rgba(2, 132, 199, 0.3);
        }}
        
        .msg-system {{
            align-self: flex-start;
            background: var(--chat-system);
            border: 1px solid var(--panel-border);
            backdrop-filter: blur(8px);
            border-bottom-left-radius: 4px;
            width: 100%;
            max-width: 90%;
        }}
        
        /* Result Items inside System Bubble */
        .result-item {{
            margin-top: 15px;
            padding: 16px;
            background: rgba(0,0,0,0.2);
            border-radius: 12px;
            border-left: 4px solid var(--accent);
        }}
        .result-item:first-child {{ margin-top: 0; }}
        
        .file-link {{
            color: var(--accent);
            text-decoration: none;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 8px;
            font-size: 16px;
            transition: color 0.2s;
        }}
        .file-link:hover {{ color: #7dd3fc; text-decoration: underline; }}
        .result-context {{ color: #cbd5e1; font-size: 14.5px; }}
        
        /* Input Area fixed at bottom */
        .input-area {{
            padding: 24px 30px;
            background: rgba(15, 23, 42, 0.8);
            border-top: 1px solid var(--panel-border);
            backdrop-filter: blur(12px);
        }}
        
        .input-wrapper {{
            display: flex;
            gap: 12px;
            background: rgba(255,255,255,0.05);
            padding: 8px;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: border-color 0.3s;
        }}
        .input-wrapper:focus-within {{ border-color: var(--accent); box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.1); }}
        
        input[type="text"] {{
            flex: 1;
            background: transparent;
            border: none;
            color: white;
            font-size: 16px;
            padding: 12px 16px;
            outline: none;
            font-family: inherit;
        }}
        input[type="text"]::placeholder {{ color: var(--text-muted); }}
        
        button {{
            background: var(--accent);
            color: #0f172a;
            border: none;
            border-radius: 12px;
            padding: 0 24px;
            font-weight: 600;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.2s;
            font-family: inherit;
        }}
        button:hover {{ background: var(--accent-hover); transform: translateY(-1px); }}
        button:active {{ transform: translateY(0); }}
        
        .btn-clear {{ background: rgba(255,255,255,0.1); color: white; }}
        .btn-clear:hover {{ background: rgba(255,255,255,0.15); }}
        
        /* Sidebar (Right) */
        .sidebar {{
            width: 320px;
            background: var(--panel-bg);
            border-left: 1px solid var(--panel-border);
            display: flex;
            flex-direction: column;
            backdrop-filter: blur(20px);
        }}
        
        .sidebar-header {{
            padding: 24px;
            border-bottom: 1px solid var(--panel-border);
        }}
        .sidebar-header h2 {{ margin: 0; font-size: 16px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; }}
        
        .history-list {{
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        
        .history-item {{
            padding: 14px 16px;
            border-radius: 12px;
            background: rgba(255,255,255,0.03);
            border: 1px solid transparent;
            cursor: pointer;
            font-size: 14.5px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .history-item:before {{ content: '🕒'; font-size: 14px; opacity: 0.5; }}
        .history-item:hover {{
            background: rgba(255,255,255,0.08);
            border-color: rgba(255,255,255,0.1);
            transform: translateX(-2px);
        }}
        
        /* Custom Scrollbars */
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.2); border-radius: 10px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: rgba(255,255,255,0.3); }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        /* Loading Animation */
        .typing-indicator span {{
            display: inline-block;
            width: 6px;
            height: 6px;
            background: var(--text-muted);
            border-radius: 50%;
            margin: 0 2px;
            animation: bounce 1.4s infinite ease-in-out both;
        }}
        .typing-indicator span:nth-child(1) {{ animation-delay: -0.32s; }}
        .typing-indicator span:nth-child(2) {{ animation-delay: -0.16s; }}
        @keyframes bounce {{
            0%, 80%, 100% {{ transform: scale(0); }}
            40% {{ transform: scale(1); }}
        }}
        
    </style>
</head>
<body>
    <div class="layout">
        <!-- Main Chat Area left -->
        <main class="main-chat">
            <header class="header">
                <h1><span>⚖️</span> Buscador Analítico de Sentencias</h1>
            </header>
            
            <div class="messages-container" id="chat">
                <div class="message msg-system">
                    👋 ¡Hola Guille! Escribe un término abajo para buscar en todas las sentencias locales.<br>
                    <span style="color:var(--text-muted); font-size: 13px; display:block; margin-top:8px;">Te mostraré 50 palabras antes y 100 palabras después de la coincidencia para garantizar buen contexto.</span>
                </div>
            </div>
            
            <div class="input-area">
                <div class="input-wrapper">
                    <input type="text" id="busqueda" placeholder="Ej. recurso de amparo..." autocomplete="off">
                    <button id="btnBuscar" onclick="buscar()">Buscar</button>
                    <button class="btn-clear" onclick="limpiar()" title="Limpiar Chat">Limpiar</button>
                </div>
            </div>
        </main>
        
        <!-- Sidebar Right -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <h2>Historial</h2>
            </div>
            <div class="history-list" id="historial">
                <!-- Items de historial -->
                <div style="color:var(--text-muted); font-style:italic; font-size:13px; padding:10px;">Vacío</div>
            </div>
        </aside>
    </div>

    <script>
        let historial = [];
        const inputBusqueda = document.getElementById('busqueda');
        const chat = document.getElementById('chat');
        const hDiv = document.getElementById('historial');
        const btnBuscar = document.getElementById('btnBuscar');

        inputBusqueda.addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') buscar();
        }});

        function appendUserMessage(text) {{
            const div = document.createElement('div');
            div.className = 'message msg-user';
            div.textContent = text;
            chat.appendChild(div);
            // Hacer scroll hasta abajo
            chat.scrollTop = chat.scrollHeight;
        }}

        function appendSystemMessage(htmlContent) {{
            const div = document.createElement('div');
            div.className = 'message msg-system';
            div.innerHTML = htmlContent;
            chat.appendChild(div);
            // Hacer scroll suave hasta el nuevo mensaje para ser visible
            setTimeout(() => {{
                chat.scrollTop = chat.scrollHeight;
            }}, 20);
        }}
        
        function appendTypingIndicator() {{
            const id = 'typing-' + Date.now();
            const div = document.createElement('div');
            div.className = 'message msg-system';
            div.id = id;
            div.innerHTML = `<div class="typing-indicator">Buscando documentos locales <span></span><span></span><span></span></div>`;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
            return id;
        }}

        function buscar() {{
            const query = inputBusqueda.value.trim();
            if(!query) return;

            // Actualizar historial
            if(!historial.includes(query)) {{
                historial.unshift(query);
                if(historial.length > 20) historial.pop(); // límite preventivo
                actualizarHistorial();
            }}

            // Instancia render de interfaz de chat: mensaje de usuario
            appendUserMessage(query);
            inputBusqueda.value = '';
            
            // Indicador de carga
            const typingId = appendTypingIndicator();
            btnBuscar.disabled = true;

            fetch('/search', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{query: query}})
            }})
            .then(res => res.json())
            .then(data => {{
                // Remover carga indicador de que el server responde
                document.getElementById(typingId).remove();
                btnBuscar.disabled = false;
                
                let htmlStr = `<div style="margin-bottom:12px; font-weight:600;">Resultados para "${{query}}": ${{data.results.length}} coincidencias encontradas.</div>`;
                
                if(data.results.length === 0) {{
                    htmlStr += `<div style="color:var(--text-muted); font-style:italic;">No se encontraron resultados en los archivos de texto.</div>`;
                }} else {{
                    data.results.forEach(r => {{
                        const queryParam = encodeURIComponent(query);
                        htmlStr += `
                            <div class="result-item">
                                <a href="/ver/${{r.archivo}}?q=${{queryParam}}" target="_blank" class="file-link">📄 ${{r.archivo}}</a>
                                <div class="result-context">...${{r.contexto}}...</div>
                            </div>`;
                    }});
                }}
                
                appendSystemMessage(htmlStr);
                
            }})
            .catch(err => {{
                document.getElementById(typingId).remove();
                btnBuscar.disabled = false;
                appendSystemMessage(`<span style="color:#ef4444;">Ocurrió un error en la búsqueda. Asegúrate de que el servidor Flask esté corriendo.</span>`);
            }});
        }}

        function actualizarHistorial() {{
            if(historial.length === 0) {{
                hDiv.innerHTML = `<div style="color:var(--text-muted); font-style:italic; font-size:13px; padding:10px;">Vacío</div>`;
                return;
            }}
            hDiv.innerHTML = historial.map(h => `
                <div class="history-item" onclick="document.getElementById('busqueda').value='${{h}}'; buscar();">
                    ${{h}}
                </div>
            `).join('');
        }}

        function limpiar() {{
            chat.innerHTML = `
                <div class="message msg-system">
                    👋 Historial de chat limpiado.<br>
                    <span style="opacity:0.8;">¿Qué quieres buscar ahora?</span>
                </div>
            `;
        }}
    </script>
</body>
</html>
"""

@app.route('/ver/<filename>')
def ver_archivo(filename):
    ruta = os.path.join(CARPETA_SENTENCIAS, filename)
    if not os.path.exists(ruta) or not filename.endswith('.txt'):
        abort(404)
    
    query = request.args.get('q', '')
    
    try:
        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
            contenido_seguro = html.escape(contenido)
            
        return render_template_string(f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <title>Leyendo: {{filename}}</title>
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
                <style>
                    {CSS_COMUN}
                    body {{ 
                        background: var(--bg-dark); 
                        padding: 0; 
                        margin: 0; 
                        overflow-y: scroll;
                    }}
                    .doc-container {{
                        max-width: 900px;
                        margin: 40px auto;
                        background: rgba(30, 41, 59, 0.4);
                        border: 1px solid var(--panel-border);
                        border-radius: 16px;
                        padding: 50px 60px;
                        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
                        backdrop-filter: blur(10px);
                    }}
                    .header-doc {{ 
                        border-bottom: 1px solid var(--panel-border); 
                        margin-bottom: 40px; 
                        padding-bottom: 20px; 
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }}
                    .header-doc h2 {{ margin: 0; font-size: 24px; font-weight: 600; color: #f1f5f9; }}
                    .header-doc .badge {{ background: var(--chat-user); color: white; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; }}
                    .documento {{ 
                        font-size: 17px; 
                        line-height: 1.8; 
                        color: #cbd5e1; 
                        white-space: pre-wrap; 
                        font-family: 'Inter', sans-serif;
                    }}
                    
                    /* Custom Scrollbar */
                    ::-webkit-scrollbar {{ width: 10px; }}
                    ::-webkit-scrollbar-track {{ background: var(--bg-dark); }}
                    ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 5px; }}
                    ::-webkit-scrollbar-thumb:hover {{ background: rgba(255,255,255,0.2); }}
                </style>
            </head>
            <body>
                <div class="doc-container">
                    <div class="header-doc">
                        <h2>📄 {{filename}}</h2>
                        <span class="badge">Visor Seguro</span>
                    </div>
                    <!-- El div ID permite a Javascript localizar y modificar -->
                    <div class="documento" id="cuerpoSentencia">{{{{contenido_seguro}}}}</div>
                </div>
                
                <script>
                    const query = "{{{{query}}}}".trim();
                    if(query) {{
                        const docDiv = document.getElementById('cuerpoSentencia');
                        let content = docDiv.innerHTML;
                        
                        // Escapar la query para RegExp
                        const safeQuery = query.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
                        const regex = new RegExp(safeQuery, 'gi');
                        
                        docDiv.innerHTML = content.replace(regex, (match) => `<span class="term-highlight">${{match}}</span>`);
                        
                        setTimeout(() => {{
                            const firstMatch = document.querySelector('.term-highlight');
                            if(firstMatch) {{
                                firstMatch.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            }}
                        }}, 500);
                    }}
                </script>
            </body>
            </html>
        """, filename=filename, query=query, contenido_seguro=contenido_seguro)
    except Exception as e:
        return f"Error al leer el archivo: {e}"

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search', methods=['POST'])
def search():
    termino = request.json.get('query', '').lower()
    resultados = []
    
    if not termino:
        return jsonify(results=resultados)

    archivos = sorted([f for f in os.listdir(CARPETA_SENTENCIAS) if f.endswith('.txt')])

    for nombre in archivos:
        ruta = os.path.join(CARPETA_SENTENCIAS, nombre)
        try:
            with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
                contenido = f.read()
                
                for coincidencia in re.finditer(re.escape(termino), contenido.lower()):
                    inicio, fin = coincidencia.start(), coincidencia.end()
                    
                    texto_previo = contenido[:inicio]
                    texto_posterior = contenido[fin:]
                    
                    prev_words = texto_previo.split()[-50:]
                    post_words = texto_posterior.split()[:100]
                    
                    prev_str = " ".join(prev_words)
                    post_str = " ".join(post_words)
                    
                    prev_safe = html.escape(prev_str)
                    post_safe = html.escape(post_str)
                    match_safe = html.escape(contenido[inicio:fin])
                    
                    resaltado = f"{prev_safe} <span class='term-highlight'>{match_safe}</span> {post_safe}"
                    
                    resultados.append({
                        "archivo": nombre, 
                        "contexto": resaltado
                    })
                    
        except Exception:
            continue
            
    return jsonify(results=resultados)

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)
