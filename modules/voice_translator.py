# modules/voice_translator.py
# Módulo: Traductor de Voz Optimizado
import requests
import streamlit as st

FRASES_UTILES = {
    "🇪🇸 Español → Inglés": {
        "idioma_destino": "en",
        "flag": "🇬🇧",
        "tts_lang": "en-GB",
        "frases": [
            ("¿Cuánto cuesta?", "How much does it cost?"),
            ("¿Dónde está el baño?", "Where is the bathroom?"),
            ("Una mesa para tres personas", "A table for three people"),
            ("La cuenta, por favor", "The bill, please"),
            ("¿Habla español?", "Do you speak Spanish?"),
            ("No entiendo", "I don't understand"),
            ("¿Puede repetir más despacio?", "Can you repeat more slowly?"),
            ("Estoy perdido/a", "I'm lost"),
            ("Llame a la policía", "Call the police"),
            ("Necesito un médico", "I need a doctor"),
            ("¿Dónde está la estación?", "Where is the train station?"),
        ]
    },
    "🇪🇸 Español → Francés": {
        "idioma_destino": "fr",
        "flag": "🇫🇷",
        "tts_lang": "fr-FR",
        "frases": [
            ("¿Cuánto cuesta?", "Combien ça coûte?"),
            ("¿Dónde está el baño?", "Où sont les toilettes?"),
            ("Una mesa para tres personas", "Une table pour trois personnes"),
            ("La cuenta, por favor", "L'addition, s'il vous plaît"),
            ("¿Habla español?", "Parlez-vous espagnol?"),
            ("No entiendo", "Je ne comprends pas"),
            ("¿Puede repetir más despacio?", "Pouvez-vous répéter plus lentement?"),
            ("Estoy perdido/a", "Je suis perdu(e)"),
            ("Llame a la policía", "Appelez la police"),
            ("Necesito un médico", "J'ai besoin d'un médecin"),
            ("¿Dónde está la estación?", "Où est la gare?"),
            ("¡Feliz cumpleaños!", "Joyeux anniversaire!"),
        ]
    },
    "🇪🇸 Español → Neerlandés": {
        "idioma_destino": "nl",
        "flag": "🇳🇱",
        "tts_lang": "nl-NL",
        "frases": [
            ("¿Cuánto cuesta?", "Hoeveel kost het?"),
            ("¿Dónde está el baño?", "Waar is het toilet?"),
            ("Una mesa para tres personas", "Een tafel voor drie personen"),
            ("La cuenta, por favor", "De rekening, alstublieft"),
            ("¿Habla español?", "Spreekt u Spaans?"),
            ("No entiendo", "Ik begrijp het niet"),
            ("Estoy perdido/a", "Ik ben verdwaald"),
            ("Llame a la policía", "Bel de politie"),
            ("Necesito un médico", "Ik heb een dokter nodig"),
            ("¿Dónde está la estación?", "Waar is het station?"),
            ("Gracias", "Dank u wel"),
        ]
    },
}

def traducir_texto(texto: str, idioma_destino: str) -> str:
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": texto, "langpair": f"es|{idioma_destino}"}
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        if data.get("responseStatus") == 200:
            return data["responseData"]["translatedText"]
        return "Error en la traducción (Límite de API alcanzado)"
    except Exception as e:
        return f"Error: {e}"

def componente_voz_completo(idioma_destino: str, tts_lang: str, idioma_nombre: str):
    html_code = f"""
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        .voz-wrapper {{
            font-family: 'Inter', -apple-system, sans-serif;
            max-width: 640px; margin: 0 auto; padding: 8px 0 16px 0;
            display: flex; flex-direction: column; gap: 14px;
        }}
        #btnGrabar {{
            width: 100%; padding: 18px 24px;
            background: linear-gradient(135deg, #FF4B4B 0%, #cc0000 100%);
            color: white; border: none; border-radius: 14px;
            font-size: 18px; font-weight: 700; cursor: pointer;
            box-shadow: 0 4px 20px rgba(255, 75, 75, 0.35);
            transition: all 0.25s ease; letter-spacing: 0.3px;
        }}
        #btnGrabar:hover {{ transform: translateY(-1px); box-shadow: 0 6px 24px rgba(255, 75, 75, 0.5); }}
        #btnGrabar.grabando {{
            background: linear-gradient(135deg, #991111 0%, #660000 100%);
            animation: pulse-red 1.2s ease-in-out infinite;
        }}
        @keyframes pulse-red {{
            0%, 100% {{ box-shadow: 0 4px 20px rgba(255,75,75,0.35); }}
            50% {{ box-shadow: 0 4px 32px rgba(255,75,75,0.7); }}
        }}
        #statusBox {{ text-align: center; font-size: 13px; color: #888; min-height: 20px; }}
        .texto-panel {{ background: #161b27; border: 1px solid #2a2f3e; border-radius: 14px; padding: 16px 18px; }}
        .texto-panel.activo {{ border-color: #3a7bd5; }}
        .texto-panel.traducido {{ border-color: #22c55e44; background: #0f1f14; }}
        .texto-panel.traducido.activo {{ border-color: #22c55e; }}
        .panel-label {{ font-size: 11px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: #555; margin-bottom: 8px; }}
        .panel-label.traducido-label {{ color: #22c55e99; }}
        .panel-texto {{ font-size: 17px; color: #ccc; min-height: 28px; line-height: 1.5; }}
        .panel-texto.placeholder {{ color: #3a3f50; font-style: italic; }}
        .panel-texto.traducido-texto {{ color: #e2fde8; font-weight: 600; font-size: 19px; }}
        .panel-texto.provisional {{ color: #555; font-style: italic; }}
        #btnAudio {{
            width: 100%; padding: 14px 24px;
            background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
            color: white; border: none; border-radius: 14px;
            font-size: 16px; font-weight: 600; cursor: pointer;
            box-shadow: 0 4px 16px rgba(34, 197, 94, 0.25);
            transition: all 0.25s ease; opacity: 0.4; pointer-events: none;
        }}
        #btnAudio.enabled {{ opacity: 1; pointer-events: all; }}
        #btnAudio.reproduciendo {{
            background: linear-gradient(135deg, #0f6b2e 0%, #0a4d20 100%);
            animation: pulse-green 1s ease-in-out infinite;
        }}
        @keyframes pulse-green {{
            0%, 100% {{ box-shadow: 0 4px 16px rgba(34,197,94,0.25); }}
            50% {{ box-shadow: 0 4px 28px rgba(34,197,94,0.6); }}
        }}
    </style>

    <div class="voz-wrapper">
        <button id="btnGrabar" onclick="toggleGrabacion()">🎙️ Toca para hablar en español</button>
        <div id="statusBox">Listo — toca el botón y habla</div>
        <div class="texto-panel" id="panelEspanol">
            <div class="panel-label">🇵🇪 Lo que dijiste</div>
            <div id="textoEspanol" class="panel-texto placeholder">Habla para ver el texto aquí...</div>
        </div>
        <div class="texto-panel traducido" id="panelTraducido">
            <div class="panel-label traducido-label">{idioma_nombre} Traducción</div>
            <div id="textoTraducido" class="panel-texto traducido-texto placeholder">La traducción aparecerá aquí...</div>
        </div>
        <button id="btnAudio" onclick="reproducirAudio()">🔊 Escuchar pronunciación</button>
    </div>

    <script>
    let recognition = null;
    let grabando = false;
    let ultimaTraduccion = '';

    function setPanel(id, text, isPlaceholder, isTraducido) {{
        const el = document.getElementById(id);
        if(!el) return;
        el.className = 'panel-texto' + (isTraducido ? ' traducido-texto' : '') + (isPlaceholder ? ' placeholder' : '');
        el.textContent = text;
    }}

    async function traducirTexto(texto) {{
        try {{
            document.getElementById('statusBox').textContent = '⏳ Traduciendo...';
            const url = `https://api.mymemory.translated.net/get?q=${{encodeURIComponent(texto)}}&langpair=es|{idioma_destino}`;
            const response = await fetch(url);
            const data = await response.json();
            return data.responseStatus === 200 ? data.responseData.translatedText : 'Error de cuota API';
        }} catch(e) {{ return 'Error de conexión'; }}
    }}

    function reproducirAudio(texto) {{
        const textoFinal = texto || ultimaTraduccion;
        if (!textoFinal) return;
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(textoFinal);
        u.lang = '{tts_lang}';
        u.rate = 0.9;
        const btn = document.getElementById('btnAudio');
        u.onstart = () => {{ btn.textContent = '🔊 Reproduciendo...'; btn.classList.add('reproduciendo'); }};
        u.onend = () => {{ btn.textContent = '🔊 Escuchar pronunciación'; btn.classList.remove('reproduciendo'); }};
        window.speechSynthesis.speak(u);
    }}

    function toggleGrabacion() {{ grabando ? detenerGrabacion() : iniciarGrabacion(); }}

    function iniciarGrabacion() {{
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {{
            document.getElementById('statusBox').textContent = '❌ Navegador no compatible';
            return;
        }}
        recognition = new SR();
        recognition.lang = 'es-PE';
        recognition.interimResults = true;

        recognition.onstart = () => {{
            grabando = true;
            const btn = document.getElementById('btnGrabar');
            btn.textContent = '⏹️ Toca para detener';
            btn.classList.add('grabando');
            document.getElementById('statusBox').textContent = '🔴 Escuchando...';
            setPanel('textoEspanol', 'Escuchando...', true, false);
            setPanel('textoTraducido', 'Esperando...', true, true);
        }};

        recognition.onresult = async (event) => {{
            let final_ = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {{
                if (event.results[i].isFinal) final_ += event.results[i][0].transcript;
            }}
            if (final_) {{
                setPanel('textoEspanol', final_, false, false);
                const trad = await traducirTexto(final_);
                ultimaTraduccion = trad;
                setPanel('textoTraducido', trad, false, true);
                document.getElementById('panelTraducido').classList.add('activo');
                document.getElementById('btnAudio').classList.add('enabled');
                document.getElementById('statusBox').textContent = '✅ Traducción lista';
                reproducirAudio(trad);
            }}
        }};

        recognition.onerror = () => detenerGrabacion();
        recognition.onend = () => detenerGrabacion();
        recognition.start();
    }}

    function detenerGrabacion() {{
        grabando = false;
        if (recognition) recognition.stop();
        const btn = document.getElementById('btnGrabar');
        btn.textContent = '🎙️ Toca para hablar en español';
        btn.classList.remove('grabando');
    }}
    </script>
    """
    st.components.v1.html(html_code, height=480)

def mostrar():
    st.title("🎙️ Traductor de Voz")
    st.caption("Habla en español → traducción automática → audio")

    tab_voz, tab_texto, tab_frases = st.tabs(["🎙️ Voz", "⌨️ Texto", "📖 Frases"])

    with tab_voz:
        idioma_sel = st.selectbox("Traducir a:", list(FRASES_UTILES.keys()), key="v_auto")
        grupo = FRASES_UTILES[idioma_sel]
        st.info("💡 Toca el botón, habla y espera la magia.")
        componente_voz_completo(grupo["idioma_destino"], grupo["tts_lang"], grupo["flag"])

    with tab_texto:
        mapa = {"Inglés 🇬🇧": ("en", "en-GB"), "Francés 🇫🇷": ("fr", "fr-FR"), "Neerlandés 🇳🇱": ("nl", "nl-NL")}
        idioma_t = st.selectbox("Traducir a:", list(mapa.keys()))
        cod, tts = mapa[idioma_t]
        t_in = st.text_area("Escribe en español:", height=100)
        if st.button("🌍 Traducir", use_container_width=True):
            if t_in.strip():
                res = traducir_texto(t_in, cod)
                st.markdown(f"### {res}")
                st.components.v1.html(f"<button onclick='h()' style='padding:10px; background:#16a34a; color:white; border:none; border-radius:8px; cursor:pointer;'>🔊 Escuchar</button><script>function h(){{window.speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(`{res}`);u.lang='{tts}';window.speechSynthesis.speak(u);}}</script>", height=60)

    with tab_frases:
        g_sel = st.selectbox("Idioma:", list(FRASES_UTILES.keys()), key="v_frases")
        grupo = FRASES_UTILES[g_sel]
        for i, (esp, trad) in enumerate(grupo["frases"]):
            with st.container(border=True):
                c1, c2 = st.columns([1, 1])
                c1.write(f"🇪🇸 {esp}")
                c2.write(f"{grupo['flag']} {trad}")
                st.components.v1.html(f"<button onclick='h{i}()' style='padding:5px 15px; background:#16a34a; color:white; border:none; border-radius:5px; cursor:pointer;'>🔊 Escuchar</button><script>function h{i}(){{window.speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(`{trad}`);u.lang='{grupo['tts_lang']}';window.speechSynthesis.speak(u);}}</script>", height=45)
