"""
Smoke tests para invariantes críticos del europe-travel-app.

No dependen de Firestore, Gemini ni Tavily. Cubren:
  - Similitud coseno del motor RAG
  - Conversor de monedas
  - Detección del patrón [BUSCAR_WEB:] del Travel Concierge
  - Lógica de roles (mostrar_precio, is_admin)
"""
from unittest.mock import patch

import pytest

# ── 1. RAG cosine_similarity ──────────────────────────────────────────────

def test_cosine_similarity_identical_vectors():
    from utils.knowledge_base import cosine_similarity
    v = [1.0, 2.0, 3.0]
    assert cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    from utils.knowledge_base import cosine_similarity
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert cosine_similarity(a, b) == pytest.approx(0.0)


def test_cosine_similarity_zero_vector_returns_zero():
    from utils.knowledge_base import cosine_similarity
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


# ── 2. Conversor de monedas (phrase_pocket) ───────────────────────────────

@pytest.fixture
def rates_eur():
    return {
        "rates": {"EUR": 1.0, "PEN": 4.0, "USD": 1.08},
        "base":  "EUR",
        "fecha": "2026-05-10",
        "fuente": "test",
    }


def test_convertir_misma_moneda(rates_eur):
    from modules.phrase_pocket import convertir
    assert convertir(100.0, "EUR", "EUR", rates_eur) == 100.0


def test_convertir_eur_a_pen(rates_eur):
    from modules.phrase_pocket import convertir
    assert convertir(100.0, "EUR", "PEN", rates_eur) == pytest.approx(400.0)


def test_convertir_pen_a_eur(rates_eur):
    from modules.phrase_pocket import convertir
    # 400 PEN / 4 (tasa EUR->PEN) = 100 EUR
    assert convertir(400.0, "PEN", "EUR", rates_eur) == pytest.approx(100.0)


# ── 3. Travel Concierge: detectar_busqueda ────────────────────────────────

def test_detectar_busqueda_extrae_query():
    from modules.travel_concierge import detectar_busqueda
    necesita, query = detectar_busqueda("[BUSCAR_WEB: restaurantes París 2026]")
    assert necesita is True
    assert query == "restaurantes París 2026"


def test_detectar_busqueda_falso_si_no_hay_patron():
    from modules.travel_concierge import detectar_busqueda
    necesita, query = detectar_busqueda("La torre Eiffel está en París.")
    assert necesita is False
    assert query == ""


# ── 4. Roles: mostrar_precio respeta el flag _show_prices ─────────────────

def test_mostrar_precio_admin_devuelve_valor():
    with patch("utils.price_helper.st") as mock_st:
        mock_st.session_state.get.return_value = True
        from utils.price_helper import mostrar_precio
        assert mostrar_precio("€42") == "€42"


def test_mostrar_precio_familiar_oculta():
    with patch("utils.price_helper.st") as mock_st:
        mock_st.session_state.get.return_value = False
        from utils.price_helper import mostrar_precio
        assert mostrar_precio("€42") == "🔒"


def test_mostrar_precio_familiar_con_fallback_custom():
    with patch("utils.price_helper.st") as mock_st:
        mock_st.session_state.get.return_value = False
        from utils.price_helper import mostrar_precio
        assert mostrar_precio("€42", fallback="—") == "—"


# ── 5. Roles: is_admin ─────────────────────────────────────────────────────

def test_is_admin_true_para_role_admin():
    with patch("auth.google_oauth.st") as mock_st:
        mock_st.session_state.get.return_value = {"role": "ADMIN"}
        from auth.google_oauth import is_admin
        assert is_admin() is True


def test_is_admin_false_para_role_familiar():
    with patch("auth.google_oauth.st") as mock_st:
        mock_st.session_state.get.return_value = {"role": "FAMILIAR"}
        from auth.google_oauth import is_admin
        assert is_admin() is False


def test_is_admin_false_sin_usuario():
    with patch("auth.google_oauth.st") as mock_st:
        mock_st.session_state.get.return_value = None
        from auth.google_oauth import is_admin
        assert is_admin() is False


# ── 6. Throttle de login ───────────────────────────────────────────────────

def test_login_no_bloqueado_sin_intentos():
    with patch("auth.google_oauth.st") as mock_st:
        mock_st.session_state.get.return_value = None
        from auth.google_oauth import _login_bloqueado
        bloqueado, restante = _login_bloqueado()
        assert bloqueado is False
        assert restante == 0


def test_login_bloqueado_al_superar_limite():
    import time as time_mod
    with patch("auth.google_oauth.st") as mock_st:
        mock_st.session_state.get.return_value = {
            "count": 5,
            "ts": time_mod.time(),
        }
        from auth.google_oauth import MAX_LOGIN_ATTEMPTS, _login_bloqueado
        bloqueado, restante = _login_bloqueado()
        assert bloqueado is True
        assert restante > 0
        assert MAX_LOGIN_ATTEMPTS == 5


def test_login_se_libera_al_expirar_ventana():
    import time as time_mod
    with patch("auth.google_oauth.st") as mock_st:
        # 10 intentos pero la ventana ya expiró (más vieja que LOGIN_WINDOW_SEC)
        mock_st.session_state.get.return_value = {
            "count": 10,
            "ts": time_mod.time() - 9999,
        }
        from auth.google_oauth import _login_bloqueado
        bloqueado, restante = _login_bloqueado()
        assert bloqueado is False
        assert restante == 0


# ── 7. Packing checker: persistencia compartida ────────────────────────────

def test_cargar_packing_devuelve_items_marcados_de_firestore():
    from modules import packing_checker
    fake_doc = type("Doc", (), {
        "exists":   True,
        "to_dict":  lambda self: {"items_marcados": {"Documentos_Pasaporte": True}},
    })()
    mock_db = type("DB", (), {})()
    mock_db.collection = lambda *a, **kw: type("C", (), {
        "document": lambda self, *a, **kw: type("D", (), {
            "get": lambda self: fake_doc,
        })(),
    })()
    with patch("modules.packing_checker.get_firestore_client", return_value=mock_db):
        packing_checker.cargar_packing.clear()
        resultado = packing_checker.cargar_packing()
    assert resultado == {"Documentos_Pasaporte": True}


# ── 8. Offline FAQs: fallback cuando Gemini falla ──────────────────────────

def test_buscar_faq_offline_matchea_robo_pasaporte():
    from utils.offline_faqs import buscar_faq_offline
    faq = buscar_faq_offline("Me robaron el pasaporte ayer en el metro")
    assert faq is not None
    assert faq["id"] == "robo_pasaporte"
    assert "consulado" in faq["respuesta"].lower()


def test_buscar_faq_offline_matchea_telefonos_emergencia():
    from utils.offline_faqs import buscar_faq_offline
    faq = buscar_faq_offline("¿Cuál es el número de emergencia en Europa?")
    assert faq is not None
    assert faq["id"] == "telefonos_emergencia"
    assert "112" in faq["respuesta"]


def test_buscar_faq_offline_sin_match_retorna_none():
    from utils.offline_faqs import buscar_faq_offline
    faq = buscar_faq_offline("¿Cuál es la mejor pizza de Madrid?")
    assert faq is None


def test_respuesta_fallback_generica_lista_modulos_offline():
    from utils.offline_faqs import respuesta_fallback_generica
    msg = respuesta_fallback_generica()
    assert "Emergency Card" in msg
    assert "Phrase Pocket" in msg
    assert "Voice Translator" in msg


def test_guardar_packing_escribe_dict_completo():
    from modules import packing_checker
    escrito = {}
    class _Doc:
        def set(self, payload):
            escrito.update(payload)
    class _Col:
        def document(self, *a, **kw):
            return _Doc()
    class _DB:
        def collection(self, *a, **kw):
            return _Col()
    with patch("modules.packing_checker.get_firestore_client", return_value=_DB()), \
         patch("modules.packing_checker.st") as mock_st:
        mock_st.session_state.get.return_value = {"email": "victor.ramirez@entel.pe"}
        ok = packing_checker.guardar_packing({"Salud_Ibuprofeno": True})
    assert ok is True
    assert escrito["items_marcados"] == {"Salud_Ibuprofeno": True}
    assert escrito["actualizado_por"] == "victor.ramirez@entel.pe"
