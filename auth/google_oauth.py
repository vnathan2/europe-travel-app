# auth/google_oauth.py
# Autenticación OAuth2 con Google + control de roles

import os
import time
import urllib.parse

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Rate limit del login. Mitiga OWASP A07 (Identification and Authentication Failures).
# Granularidad: por sesión de Streamlit (cookie del usuario en el navegador).
# Esto no detiene un ataque distribuido, pero sí frena rebotes de un mismo
# navegador y reduce el consumo de cuota Google OAuth ante errores repetidos.
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SEC   = 300   # 5 minutos

ROLE_ADMIN    = "ADMIN"
ROLE_FAMILIAR = "FAMILIAR"

def _get_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        try:
            from utils.gcp_client import get_secret
            val = get_secret(key)
        except Exception:
            val = ""
    return val or ""

def get_authorized_users() -> dict:
    return {
        _get_env("ADMIN_EMAIL").lower():      ROLE_ADMIN,
        _get_env("FAMILIAR_EMAIL_1").lower(): ROLE_FAMILIAR,
        _get_env("FAMILIAR_EMAIL_2").lower(): ROLE_FAMILIAR,
    }

def get_redirect_uri() -> str:
    """
    Resuelve la redirect_uri para el OAuth flow.

    Orden:
      1. Variable de entorno OAUTH_REDIRECT_URI (canonical para prod).
      2. Detección automática por host de la request (run.app, localhost).
      3. Falla explícita con instrucciones (sin URLs hardcodeadas).
    """
    uri = _get_env("OAUTH_REDIRECT_URI")
    if uri:
        return uri

    try:
        host = st.context.headers.get("host", "")
        if "run.app" in host:
            return f"https://{host}"
        if "localhost" in host or "127.0.0.1" in host:
            return f"http://{host}"
    except Exception:
        pass

    # Sin URI configurada ni host detectable: detener el flujo con un error claro
    # en vez de redirigir a una URL hardcodeada que puede no existir.
    st.error(
        "❌ No se pudo determinar la redirect_uri para OAuth.\n\n"
        "Configura la variable de entorno **`OAUTH_REDIRECT_URI`** "
        "en Cloud Run (debe coincidir con la URI registrada en Google Cloud Console)."
    )
    st.stop()

def get_oauth_config() -> dict:
    return {
        "client_id":     _get_env("GOOGLE_CLIENT_ID"),
        "client_secret": _get_env("GOOGLE_CLIENT_SECRET"),
        "redirect_uri":  get_redirect_uri(),
    }

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL  = "https://www.googleapis.com/oauth2/v3/userinfo"

def build_auth_url() -> str:
    cfg = get_oauth_config()
    params = {
        "client_id":     cfg["client_id"],
        "redirect_uri":  cfg["redirect_uri"],
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "online",
        "prompt":        "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code: str) -> dict:
    cfg = get_oauth_config()
    resp = requests.post(GOOGLE_TOKEN_URL, data={
        "code":          code,
        "client_id":     cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "redirect_uri":  cfg["redirect_uri"],
        "grant_type":    "authorization_code",
    }, timeout=10)
    return resp.json()

def get_user_info(access_token: str) -> dict:
    resp = requests.get(
        GOOGLE_USER_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10
    )
    return resp.json()

def get_user_role(email: str) -> str | None:
    users = get_authorized_users()
    return users.get(email.lower())

def is_authenticated() -> bool:
    return st.session_state.get("auth_user") is not None

def get_current_user() -> dict | None:
    return st.session_state.get("auth_user")

def get_current_role() -> str | None:
    user = get_current_user()
    return user.get("role") if user else None

def is_admin() -> bool:
    return get_current_role() == ROLE_ADMIN

def show_prices() -> bool:
    return get_current_role() == ROLE_ADMIN

def logout():
    for key in ("auth_user", "oauth_code_processed", "_show_prices", "_is_admin", "_user_name"):
        st.session_state.pop(key, None)
    st.query_params.clear()
    st.rerun()

def show_login_page():
    auth_url = build_auth_url()

    # Modo debug: muestra qué URI se está usando
    if os.getenv("DEBUG_AUTH", "").lower() == "true":
        st.info(f"🔧 Redirect URI activa: `{get_redirect_uri()}`")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            "<h1 style='text-align:center'>✈️ Europe Travel 2026</h1>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align:center;color:#666;'>"
            "Jonathan · Giovanna · Camila<br>15 – 30 Julio 2026</p>",
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style='text-align:center'>
                <a href="{auth_url}" target="_self">
                    <button style="
                        background:#4285F4;color:white;border:none;
                        padding:14px 32px;border-radius:6px;
                        font-size:16px;cursor:pointer;">
                        🔐 Iniciar sesión con Google
                    </button>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("🔒 Solo los miembros de la familia tienen acceso.")

def show_access_denied(email: str):
    st.error(f"⛔ Acceso denegado para **{email}**")
    st.warning("Esta aplicación es privada para la familia.")
    if st.button("🔄 Intentar con otra cuenta"):
        logout()


def _registrar_intento_login():
    """Suma 1 al contador de intentos de login en la ventana actual."""
    ahora = time.time()
    estado = st.session_state.get("login_throttle", {"count": 0, "ts": ahora})
    if ahora - estado["ts"] > LOGIN_WINDOW_SEC:
        estado = {"count": 0, "ts": ahora}
    estado["count"] += 1
    st.session_state.login_throttle = estado


def _login_bloqueado() -> tuple[bool, int]:
    """Retorna (bloqueado, segundos_restantes)."""
    estado = st.session_state.get("login_throttle")
    if not estado:
        return False, 0
    transcurrido = time.time() - estado["ts"]
    if transcurrido > LOGIN_WINDOW_SEC:
        return False, 0
    if estado["count"] >= MAX_LOGIN_ATTEMPTS:
        return True, int(LOGIN_WINDOW_SEC - transcurrido)
    return False, 0


def _resetear_throttle():
    """Limpia el contador tras un login exitoso."""
    st.session_state.pop("login_throttle", None)

def auth_gate() -> bool:
    params = st.query_params
    code = params.get("code")

    # IMPORTANTE: procesar el código OAuth ANTES de verificar sesión activa.
    # Si hay un código nuevo, siempre procesarlo - permite cambio de usuario
    # sin necesidad de cerrar sesión explícitamente primero.
    if code and not st.session_state.get("oauth_code_processed"):
        # Rate limit: verificar antes de tocar Google
        bloqueado, segundos = _login_bloqueado()
        if bloqueado:
            st.error(f"🔒 Demasiados intentos de login. Espera {segundos} segundos.")
            st.stop()

        _registrar_intento_login()
        st.session_state.oauth_code_processed = True

        with st.spinner("🔐 Verificando tu cuenta..."):
            try:
                token_data = exchange_code_for_token(code)
                access_token = token_data.get("access_token")

                if not access_token:
                    error = token_data.get(
                        "error_description",
                        token_data.get("error", "desconocido")
                    )
                    st.error(f"❌ Error al obtener token: **{error}**")
                    st.info(
                        "💡 Posible causa: la Redirect URI en Google Cloud Console "
                        "no coincide exactamente con la de tu `.env`.\n\n"
                        f"URI que se usó: `{get_redirect_uri()}`"
                    )
                    if st.button("🔄 Volver al login"):
                        st.session_state.pop("oauth_code_processed", None)
                        st.query_params.clear()
                        st.rerun()
                    st.stop()

                user_info = get_user_info(access_token)
                email = user_info.get("email", "").lower()
                name  = user_info.get("name", email)
                pic   = user_info.get("picture", "")
                role  = get_user_role(email)

                st.query_params.clear()

                if role is None:
                    show_access_denied(email)
                    st.stop()

                _resetear_throttle()
                st.session_state.auth_user = {
                    "email": email,
                    "name":  name,
                    "pic":   pic,
                    "role":  role,
                }
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error de autenticación: {e}")
                if st.button("🔄 Volver al login"):
                    st.session_state.pop("oauth_code_processed", None)
                    st.query_params.clear()
                    st.rerun()
                st.stop()

    elif code and st.session_state.get("oauth_code_processed"):
        # FIX 2026-05-11 — CAUSA RAÍZ DEL BUG EN DEPLOY 00054:
        # Streamlit 1.32 en Cloud Run puede tardar un ciclo de rerun en
        # reflejar st.query_params.clear() en la URL del browser. Durante
        # ese ciclo extra, code != None pero oauth_code_processed = True.
        # El st.stop() anterior bloqueaba toda la UI permanentemente:
        # apply_theme() ya había inyectado el CSS (pantalla con fondo de color)
        # pero ningún módulo cargaba porque la ejecución se detenía aquí.
        # En local (APP_MODE=DEVELOPMENT) nunca hay ?code= → nunca entraba aquí.
        # Fix: limpiar params y continuar en vez de detener la ejecución.
        st.query_params.clear()
        # Continúa hacia is_authenticated() en el siguiente bloque

    if is_authenticated():
        return True

    show_login_page()
    st.stop()
