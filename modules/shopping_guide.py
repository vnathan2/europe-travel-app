# modules/shopping_guide.py
# 🛒 Shopping Guide — Tiendas, ofertas y souvenirs por ciudad
# Categorías: Ropa, Zapatos/Carteras, Souvenirs, Tecnología/Comics/Anime,
#             Gastronomía para llevar, Perfumes/Cosméticos, Joyería, Outlets

import streamlit as st
import requests
import os
from utils.price_helper import mostrar_precio

# ══════════════════════════════════════════════════════════════════════════
# LADY FALLBACK — búsqueda inteligente vía Gemini + Tavily
# ══════════════════════════════════════════════════════════════════════════

def _buscar_con_lady(busqueda: str, ciudad: str, para: str) -> str:
    """
    Cuando la búsqueda local no encuentra resultados,
    Lady usa Tavily + Gemini para buscar en internet.
    """
    try:
        # 1. Buscar con Tavily
        from tavily import TavilyClient
        from utils.gcp_client import get_secret

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            api_key = get_secret("TAVILY_API_KEY")

        client = TavilyClient(api_key=api_key)

        # Construir query orientada a compras
        ciudad_en = {
            "Madrid": "Madrid Spain", "Bayona": "Bayonne France",
            "París": "Paris France", "Bruselas": "Brussels Belgium",
            "Ámsterdam": "Amsterdam Netherlands", "Europa": "Europe"
        }.get(ciudad, ciudad)

        query = f"tiendas donde comprar {busqueda} en {ciudad_en} turistas dirección precio"
        response = client.search(query=query, search_depth="basic", max_results=5)

        resultados_txt = ""
        if response.get("answer"):
            resultados_txt += f"Respuesta directa: {response['answer']}\n\n"
        for r in response.get("results", []):
            resultados_txt += f"- {r.get('title','')}: {r.get('content','')[:200]}\n"

    except Exception as e:
        resultados_txt = f"No se pudo buscar en internet: {e}"

    try:
        # 2. Lady procesa y formatea con Gemini
        import google.generativeai as genai
        from utils.gcp_client import get_secret as gs

        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            gemini_key = gs("GEMINI_API_KEY")
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        perfil_para = {
            "Jonathan": "Jonathan (46 años, le encantan: fútbol, tecnología, Transformers, comics, manga, anime, videojuegos, lucha libre)",
            "Camila":   "Camila (15 años, le encantan: anime, manga, kpop, One Piece, cultura japonesa, maquillaje, ropa, accesorios)",
            "Giovanna": "Giovanna (46 años, le encantan: carteras, zapatos, ropa, maquillaje, perfumes, gastronomía, ofertas)",
            "Todos":    "toda la familia (Jonathan, Giovanna y Camila)",
        }.get(para, "la familia")

        prompt = f"""Eres Lady 🐾, una schnauzer viajera experta en compras en Europa.

La familia busca: "{busqueda}" en {ciudad}
Búsqueda para: {perfil_para}

Información encontrada en internet:
{resultados_txt}

Basándote en esa información, dame una respuesta útil con:
1. 2-3 tiendas específicas donde encontrar "{busqueda}" en {ciudad}
   - Nombre de la tienda
   - Dirección aproximada o zona
   - Qué tienen exactamente
   - Rango de precio (€/€€/€€€)
2. Un tip de compra personalizado para {perfil_para}
3. Si hay algo especial o único que no conseguirían en Perú

Responde en español, con tu estilo simpático de perrita viajera, con emojis.
Máximo 300 palabras. Si no encontraste información suficiente, sé honesta y sugiere alternativas."""

        respuesta = model.generate_content(prompt).text
        return respuesta

    except Exception as e:
        return f"🐾 ¡Woof! No pude conectarme ahora mismo para buscar. Error: {e}\n\nIntenta buscar directamente en Google Maps: **{busqueda} {ciudad}**"

# ══════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════

def maps_url(nombre: str, ciudad: str) -> str:
    q = requests.utils.quote(f"{nombre} {ciudad}")
    return f"https://www.google.com/maps/search/?api=1&query={q}"

def precio_tag(nivel: int) -> str:
    return "€" * nivel + "·" * (3 - nivel)

CATEGORIA_EMOJI = {
    "Ropa y Moda":          "👗",
    "Zapatos y Carteras":   "👠",
    "Souvenirs":            "🎁",
    "Tecnología / Geek":    "🎮",
    "Gastronomía":          "🍫",
    "Perfumes y Cosméticos":"💄",
    "Joyería y Accesorios": "💎",
    "Outlets y Ofertas":    "🏷️",
}

PARA_QUIEN = {
    "Jonathan": "👑",
    "Camila":   "🎀",
    "Giovanna": "🌹",
    "Todos":    "👨‍👩‍👧",
}

# ══════════════════════════════════════════════════════════════════════════
# BASE DE DATOS DE TIENDAS
# ══════════════════════════════════════════════════════════════════════════

TIENDAS = {

# ─────────────────────────────────────────────────────────────────────────
# MADRID
# ─────────────────────────────────────────────────────────────────────────
"Madrid": [
    {
        "nombre": "El Corte Inglés Callao",
        "categoria": "Ropa y Moda",
        "direccion": "Preciados 3, Madrid Centro",
        "horario": "Lun–Sáb 10:00–22:00 · Dom 11:00–21:00",
        "precio": 2,
        "rating": 4.4,
        "para": ["Giovanna", "Camila", "Jonathan"],
        "productos": ["Zara, Mango, H&M, Nike, Adidas", "Ropa hombre/mujer/adolescente", "Sección internacional con marcas europeas"],
        "tip": "💡 Pide el **Tax Free** en caja si compras +€90 — recuperas ~13% del IVA en el aeropuerto.",
        "comentario": "El grande de Madrid. Tiene de todo bajo un mismo techo, ideal para la primera parada.",
    },
    {
        "nombre": "Gran Vía Shopping",
        "categoria": "Ropa y Moda",
        "direccion": "Gran Vía 32, Madrid",
        "horario": "Lun–Dom 10:00–22:00",
        "precio": 2,
        "rating": 4.3,
        "para": ["Giovanna", "Camila"],
        "productos": ["Zara flagship store", "Pull&Bear, Bershka, Stradivarius", "H&M 4 plantas"],
        "tip": "💡 La Zara de Gran Vía es la más grande de España — tiene colecciones exclusivas.",
        "comentario": "La calle de moda más famosa de Madrid. Perfecta para pasear y comprar.",
    },
    {
        "nombre": "Mercado de Fuencarral",
        "categoria": "Ropa y Moda",
        "direccion": "Fuencarral 45, Malasaña",
        "horario": "Lun–Sáb 11:00–21:00 · Dom 12:00–20:00",
        "precio": 2,
        "rating": 4.2,
        "para": ["Camila", "Jonathan"],
        "productos": ["Tiendas alternativas y urban", "Ropa vintage y streetwear", "Accesorios únicos y complementos"],
        "tip": "💡 Perfecto para encontrar piezas únicas que no verás en otros lados.",
        "comentario": "Centro comercial alternativo, muy popular entre jóvenes. Ambiente increíble.",
    },
    {
        "nombre": "Calle Serrano — Moda de Lujo",
        "categoria": "Zapatos y Carteras",
        "direccion": "Calle Serrano, Barrio Salamanca",
        "horario": "Lun–Sáb 10:00–20:30",
        "precio": 3,
        "rating": 4.6,
        "para": ["Giovanna"],
        "productos": ["Loewe (marca española de lujo)", "Camper — zapatos españoles únicos", "Lottusse — zapatos artesanales mallorquines", "Carteras y bolsos de diseño español"],
        "tip": "💡 **Loewe** es una marca de lujo española icónica — perfecta como souvenir premium.",
        "comentario": "El barrio más lujoso de Madrid. Las marcas españolas de lujo son especialmente interesantes.",
    },
    {
        "nombre": "Camper Store Gran Vía",
        "categoria": "Zapatos y Carteras",
        "direccion": "Gran Vía 54, Madrid",
        "horario": "Lun–Sáb 10:00–21:00 · Dom 11:00–21:00",
        "precio": 2,
        "rating": 4.5,
        "para": ["Giovanna", "Camila"],
        "productos": ["Zapatos artesanales españoles", "Colecciones exclusivas", "Precios ~30% más baratos que en Perú"],
        "tip": "💡 Comprando en origen ahorras mucho vs precio en Perú. Pide Tax Free.",
        "comentario": "Marca española icónica, muy cómodos. Imprescindible si les gustan los zapatos originales.",
    },
    {
        "nombre": "Mercado de San Miguel — Gastronomía",
        "categoria": "Gastronomía",
        "direccion": "Plaza de San Miguel s/n, Madrid",
        "horario": "Dom–Jue 10:00–00:00 · Vie–Sáb 10:00–01:00",
        "precio": 2,
        "rating": 4.4,
        "para": ["Todos"],
        "productos": ["Jamón ibérico para llevar (vacío)", "Aceite de oliva virgen extra", "Vinos españoles de La Rioja y Ribera", "Turrones y dulces típicos", "Queso manchego"],
        "tip": "💡 El jamón ibérico en envase al vacío pasa perfectamente en maleta. Lleva 2-3 paquetes.",
        "comentario": "Mercado gourmet en edificio histórico. Los productos para llevar son de altísima calidad.",
    },
    {
        "nombre": "FNAC Madrid",
        "categoria": "Tecnología / Geek",
        "direccion": "Preciados 28, Madrid",
        "horario": "Lun–Sáb 10:00–22:00 · Dom 11:00–21:00",
        "precio": 2,
        "rating": 4.3,
        "para": ["Jonathan", "Camila"],
        "productos": ["Videojuegos y consolas (PS5, Switch, Xbox)", "Figuras coleccionables Funko Pop y Hot Toys", "Figuras de Transformers, Star Wars, Marvel", "Comics en español (DC, Marvel, Dark Horse)", "Manga y libros de anime", "Tecnología y gadgets", "Merchandising de lucha libre y WWE"],
        "tip": "💡 Tiene sección de coleccionables muy completa. Revisa las ofertas de la semana.",
        "comentario": "La mejor tienda para Jonathan y Camila. Comics, manga y tecnología todo junto.",
    },
    {
        "nombre": "Casa del Libro — Comics y Manga",
        "categoria": "Tecnología / Geek",
        "direccion": "Gran Vía 29, Madrid",
        "horario": "Lun–Sáb 09:30–21:30 · Dom 11:00–21:00",
        "precio": 1,
        "rating": 4.4,
        "para": ["Jonathan", "Camila"],
        "productos": ["Manga en español — One Piece, Dragon Ball, Naruto, Demon Slayer", "Comics DC y Marvel en español", "Libros de kpop, BTS, Blackpink", "Artbooks de anime y cultura japonesa", "Libros de Transformers y figuras"],
        "tip": "💡 El manga en España es más barato que en Perú y viene en español perfecto.",
        "comentario": "Librería enorme con excelente sección de manga y comics. Camila va a amar esto.",
    },
    {
        "nombre": "Perfumería Júlia — Madrid",
        "categoria": "Perfumes y Cosméticos",
        "direccion": "Gran Vía 47, Madrid",
        "horario": "Lun–Sáb 10:00–21:00",
        "precio": 2,
        "rating": 4.4,
        "para": ["Giovanna", "Camila"],
        "productos": ["Perfumes de lujo (Chanel, Dior, YSL)", "Cosméticos MAC, NARS, Charlotte Tilbury", "Cremas y cuidado facial premium", "Sets de regalo con descuento"],
        "tip": "💡 Los perfumes en España son ~20-30% más baratos que en Perú. Lleva la lista de favoritos.",
        "comentario": "Perfumería de referencia en Madrid. Gran variedad y personal muy atento.",
    },
    {
        "nombre": "Sephora Gran Vía",
        "categoria": "Perfumes y Cosméticos",
        "direccion": "Gran Vía 30, Madrid",
        "horario": "Lun–Dom 10:00–22:00",
        "precio": 2,
        "rating": 4.5,
        "para": ["Giovanna", "Camila"],
        "productos": ["Maquillaje (Too Faced, Urban Decay, NYX)", "Skincare (The Ordinary, Paula's Choice)", "Perfumes exclusivos", "Sets de regalo Sephora Collection"],
        "tip": "💡 Hazte miembro Beauty Insider gratis — tienes descuentos y muestras en caja.",
        "comentario": "La Sephora más grande de Madrid. Para Camila especialmente, tiene todo lo que busca.",
    },
    {
        "nombre": "Souvenirs Madrid Centro",
        "categoria": "Souvenirs",
        "direccion": "Calle Mayor 30-50, Madrid",
        "horario": "Lun–Dom 09:00–22:00",
        "precio": 1,
        "rating": 3.9,
        "para": ["Todos"],
        "productos": ["Camisetas del Real Madrid y España", "Flamenco, toros y castañuelas artesanales", "Cerámica talavera pintada a mano", "Imanes, llaveros y postales", "Abanicos de calidad"],
        "tip": "💡 Evita las tiendas pegadas a la Puerta del Sol — son 30% más caras. Ve a Calle Mayor.",
        "comentario": "La zona de Calle Mayor/Ópera tiene mejores precios que la Puerta del Sol.",
    },
    {
        "nombre": "El Rastro — Mercadillo",
        "categoria": "Joyería y Accesorios",
        "direccion": "Calle Ribera de Curtidores, La Latina",
        "horario": "Dom y festivos 09:00–15:00",
        "precio": 1,
        "rating": 4.3,
        "para": ["Giovanna", "Camila", "Jonathan"],
        "productos": ["Joyería artesanal y vintage", "Accesorios únicos y complementos", "Ropa vintage a precios mínimos", "Antigüedades y coleccionables", "Arte y decoración"],
        "tip": "💡 Solo domingos. Lleva efectivo y regatéa — es parte de la experiencia.",
        "comentario": "El mercadillo más famoso de España. Si el 18 jul es domingo, ¡no se lo pierdan!",
    },
    {
        "nombre": "Las Rozas Village — Outlet",
        "categoria": "Outlets y Ofertas",
        "direccion": "Calle Puerto de la Morcuera 2, Las Rozas",
        "horario": "Lun–Vie 10:00–20:00 · Sáb 10:00–21:00 · Dom 11:00–20:00",
        "precio": 2,
        "rating": 4.5,
        "para": ["Giovanna", "Camila"],
        "productos": ["Marcas de lujo con 30-70% descuento", "Armani, Burberry, Hugo Boss, Michael Kors", "Zapatos y carteras de diseño rebajados", "Ropa de temporada anterior"],
        "tip": "💡 A 30 min en tren desde Madrid (Cercanías C-8). Vale mucho la pena para compras grandes.",
        "comentario": "Outlet premium a las afueras. Los descuentos son reales y la calidad excelente.",
    },
    {
        "nombre": "Generación X — Tienda Geek Madrid",
        "categoria": "Tecnología / Geek",
        "direccion": "Calle Fuencarral 45, Madrid (Malasaña)",
        "horario": "Lun–Sáb 10:00–21:00 · Dom 11:00–20:00",
        "precio": 2,
        "rating": 4.6,
        "para": ["Jonathan", "Camila"],
        "productos": [
            "Figuras Transformers: Masterpiece, Legacy, Studio Series",
            "Hot Toys y figuras de colección premium",
            "Comics Marvel y DC en español e inglés",
            "Figuras de lucha libre AAA y WWE",
            "Merchandise de anime: One Piece, Dragon Ball, Naruto",
            "Funko Pop — colección enorme de más de 1000 figuras",
            "Videojuegos retro y modernos",
        ],
        "tip": "💡 La tienda geek más completa de Madrid. Para Transformers, es el mejor lugar de España.",
        "comentario": "Referencia nacional para coleccionistas. Jonathan va a querer quedarse horas aquí.",
    },
    {
        "nombre": "Kpop Store Madrid — Wave",
        "categoria": "Tecnología / Geek",
        "direccion": "Calle Montera 24, Madrid Centro",
        "horario": "Lun–Sáb 11:00–21:00 · Dom 12:00–20:00",
        "precio": 2,
        "rating": 4.5,
        "para": ["Camila"],
        "productos": [
            "Albums físicos kpop: BTS, Blackpink, Stray Kids, Aespa, NewJeans",
            "Photocards y merchandise oficial de grupos kpop",
            "Posters, accesorios y ropa kpop",
            "Light sticks oficiales de los grupos",
            "Papelería y artículos kawaii coreanos",
        ],
        "tip": "💡 Los albums físicos de kpop en Europa son más baratos que importarlos a Perú.",
        "comentario": "Tienda especializada en kpop. Para Camila es una parada imprescindible en Madrid.",
    },
    {
        "nombre": "Akihabara Madrid — Anime y Manga",
        "categoria": "Tecnología / Geek",
        "direccion": "Calle Silva 4, Madrid Centro",
        "horario": "Lun–Sáb 11:00–21:00",
        "precio": 2,
        "rating": 4.4,
        "para": ["Camila", "Jonathan"],
        "productos": [
            "Figuras One Piece: Luffy, Zoro, toda la tripulación",
            "Manga One Piece tomos sueltos y colecciones",
            "Figuras Demon Slayer, Jujutsu Kaisen, Chainsaw Man",
            "Ropa y sudaderas de anime",
            "Accesorios cosplay y pelucas",
            "Figuras Transformers importadas de Japón",
        ],
        "tip": "💡 Importan directamente de Japón — hay figuras que no llegan a Perú.",
        "comentario": "La tienda de anime más completa de Madrid. One Piece tiene sección propia.",
    },
],

# ─────────────────────────────────────────────────────────────────────────
# BAYONA
# ─────────────────────────────────────────────────────────────────────────
"Bayona": [
    {
        "nombre": "Cazenave — Chocolatería",
        "categoria": "Gastronomía",
        "direccion": "19 Arceaux Port Neuf, Bayonne",
        "horario": "Mar–Sáb 09:00–12:00 y 14:00–19:00",
        "precio": 2,
        "rating": 4.8,
        "para": ["Todos"],
        "productos": ["Chocolate negro artesanal bayonés", "Tabletas con naranja, almendras y especias", "Cajas regalo de chocolates variados", "Macarons rellenos de chocolate"],
        "tip": "💡 Bayona es la cuna del chocolate en Francia. Cazenave lleva desde 1854. Lleva varias cajas.",
        "comentario": "Legendaria chocolatería histórica. El chocolate de Bayona es mundialmente reconocido.",
    },
    {
        "nombre": "Daranatz — Chocolatier",
        "categoria": "Gastronomía",
        "direccion": "15 Arceaux Port Neuf, Bayonne",
        "horario": "Lun–Sáb 09:00–12:30 y 14:30–19:00",
        "precio": 2,
        "rating": 4.7,
        "para": ["Todos"],
        "productos": ["Chocolates artesanales de la región", "Kanougas (caramelos locales de chocolate)", "Gâteau Basque (pastel tradicional)", "Piment d'Espelette chocolatado"],
        "tip": "💡 Los **Kanougas** son el dulce típico de Bayona — perfectos de regalo, no se consiguen en Perú.",
        "comentario": "Chocolatería artesanal con recetas del siglo XIX. De lo mejor de la ciudad.",
    },
    {
        "nombre": "Maison Montauzer — Jamón y Especialidades",
        "categoria": "Gastronomía",
        "direccion": "17 Rue du Pilori, Bayonne",
        "horario": "Mar–Sáb 09:00–13:00 y 15:00–19:00",
        "precio": 2,
        "rating": 4.6,
        "para": ["Todos"],
        "productos": ["Jambon de Bayonne (IGP) al vacío", "Foie gras y patés", "Vinos del País Vasco francés", "Quesos de la región"],
        "tip": "💡 El **Jambon de Bayonne** es único — puedes llevarlo al vacío en maleta.",
        "comentario": "La mejor charcutería de Bayona. El jamón bayonés es diferente al ibérico español.",
    },
    {
        "nombre": "Tiendas de Artesanía Vasca",
        "categoria": "Souvenirs",
        "direccion": "Rue du Pont Neuf y Grand Bayonne",
        "horario": "Lun–Sáb 10:00–19:00",
        "precio": 1,
        "rating": 4.3,
        "para": ["Todos"],
        "productos": ["Makhila — bastón artesanal vasco único", "Espadrilles (alpargatas) artesanales", "Linge Basque — telas rayadas tradicionales", "Bérets vascos de lana", "Cerámica y alfarería local"],
        "tip": "💡 Las **espadrilles** artesanales son el souvenir más auténtico del País Vasco. Muy baratas.",
        "comentario": "El barrio antiguo está lleno de tiendas artesanales vascas. Todo muy auténtico.",
    },
    {
        "nombre": "Marché Municipal de Bayonne",
        "categoria": "Gastronomía",
        "direccion": "Place des Gascons, Bayonne",
        "horario": "Mar–Sáb 07:00–13:30",
        "precio": 1,
        "rating": 4.5,
        "para": ["Todos"],
        "productos": ["Fromages de brebis (queso de oveja local)", "Piment d'Espelette en polvo y mermelada", "Miel del País Vasco", "Frutas y productos frescos de temporada"],
        "tip": "💡 El **Piment d'Espelette** en polvo es liviano y perfecto de regalo. Único en el mundo.",
        "comentario": "Mercado tradicional con productos de la región. Hay que ir temprano para lo mejor.",
    },
],

# ─────────────────────────────────────────────────────────────────────────
# PARIS
# ─────────────────────────────────────────────────────────────────────────
"París": [
    {
        "nombre": "Galeries Lafayette — Boulevard Haussmann",
        "categoria": "Ropa y Moda",
        "direccion": "40 Bd Haussmann, Paris 9e",
        "horario": "Lun–Sáb 09:30–20:30 · Dom 11:00–20:00",
        "precio": 3,
        "rating": 4.5,
        "para": ["Giovanna", "Camila"],
        "productos": ["200+ marcas de lujo y moda", "Chanel, Dior, Gucci, Saint Laurent", "Maquillaje y perfumería de lujo en planta baja", "Moda adolescente en planta separada"],
        "tip": "💡 Pide el **Formulaire de détaxe** (Tax Free) en el mostrador Info — recuperas hasta 12% en Roissy.",
        "comentario": "El gran magasin más famoso del mundo. La terraza tiene vista gratis a la Torre Eiffel.",
    },
    {
        "nombre": "Le Marais — Boutiques y Vintage",
        "categoria": "Ropa y Moda",
        "direccion": "Rue des Francs-Bourgeois, Paris 4e",
        "horario": "Lun–Dom 11:00–20:00 (muchas abren domingo)",
        "precio": 2,
        "rating": 4.6,
        "para": ["Giovanna", "Camila"],
        "productos": ["Boutiques independientes de diseñadores parisinos", "Ropa vintage de calidad premium", "APC, Rouje, Isabel Marant (marcas francesas)", "Tiendas de kpop y cultura pop"],
        "tip": "💡 El Marais es el único barrio de París donde casi todo abre los **domingos** — planifícalo.",
        "comentario": "El barrio más trendy de París. Mezcla de lujo, vintage y cultura. Camila va a amar.",
    },
    {
        "nombre": "Sephora Champs-Élysées",
        "categoria": "Perfumes y Cosméticos",
        "direccion": "70-72 Avenue des Champs-Élysées, Paris 8e",
        "horario": "Lun–Sáb 10:00–00:00 · Dom 11:00–00:00",
        "precio": 2,
        "rating": 4.4,
        "para": ["Giovanna", "Camila"],
        "productos": ["La Sephora más grande de Europa", "Colecciones exclusivas de París", "Perfumes de nicho que no se consiguen en Perú", "Tratamientos faciales y skincare premium"],
        "tip": "💡 Tiene productos exclusivos de París que NO están en otras Sephora del mundo.",
        "comentario": "Abre hasta medianoche. Después de la Torre Eiffel de noche, perfecta parada.",
    },
    {
        "nombre": "Fragonard — Perfumería Francesa",
        "categoria": "Perfumes y Cosméticos",
        "direccion": "3-5 Square de l'Opéra Louis Jouvet, Paris 9e",
        "horario": "Lun–Sáb 09:00–18:00",
        "precio": 2,
        "rating": 4.6,
        "para": ["Giovanna"],
        "productos": ["Perfumes artesanales de Grasse", "Jabones y cremas de lujo francesas", "Velas perfumadas exclusivas", "Sets de regalo muy elegantes"],
        "tip": "💡 Fragonard es mucho más económico que Chanel/Dior y igual de francés y lujoso.",
        "comentario": "Perfumería artesanal francesa de Grasse. Tour de la fábrica gratis y sin reserva.",
    },
    {
        "nombre": "Shakespeare and Company + Bouquinistes",
        "categoria": "Souvenirs",
        "direccion": "37 Rue de la Bûcherie, Paris 5e (frente a Notre Dame)",
        "horario": "Lun–Dom 10:00–22:00",
        "precio": 1,
        "rating": 4.7,
        "para": ["Todos"],
        "productos": ["Libros vintage en varios idiomas", "Postales artísticas de París", "Bolsas de tela icónicas de la librería", "Posters y mapas artísticos de París"],
        "tip": "💡 La bolsa de tela verde de Shakespeare & Company es el souvenir más auténtico de París literario.",
        "comentario": "Librería legendaria junto al Sena. Los bouquinistes (libreros del río) son únicos en el mundo.",
    },
    {
        "nombre": "Marché d'Aligre",
        "categoria": "Gastronomía",
        "direccion": "Place d'Aligre, Paris 12e",
        "horario": "Mar–Dom 07:30–13:30",
        "precio": 1,
        "rating": 4.5,
        "para": ["Todos"],
        "productos": ["Quesos franceses (Comté, Brie, Roquefort) al vacío", "Macarons artesanales de la zona", "Foie gras en lata (pasa en maleta)", "Vinos de Borgoña y Champagne"],
        "tip": "💡 El queso francés al vacío dura semanas y es el regalo gastronómico más valorado.",
        "comentario": "El mercado más auténtico de París. Precios muy razonables vs mercados turísticos.",
    },
    {
        "nombre": "Fnac Forum des Halles",
        "categoria": "Tecnología / Geek",
        "direccion": "1-7 Rue Pierre Lescot, Paris 1er",
        "horario": "Lun–Sáb 10:00–20:00 · Dom 11:00–19:00",
        "precio": 2,
        "rating": 4.2,
        "para": ["Jonathan", "Camila"],
        "productos": ["Manga en francés (colecciones enormes)", "Figuras de anime y One Piece", "Videojuegos y consolas", "Comics franco-belgas (Asterix, Tintín originales)"],
        "tip": "💡 Los comics franco-belgas originales (Tintín, Asterix) son únicos para coleccionistas.",
        "comentario": "Fnac grande con buena sección geek. Los comics franco-belgas son un lujo para Jonathan.",
    },
    {
        "nombre": "Japan Expo Store / Rue Sainte-Anne",
        "categoria": "Tecnología / Geek",
        "direccion": "Rue Sainte-Anne, Paris 1er",
        "horario": "Lun–Dom 11:00–20:00",
        "precio": 2,
        "rating": 4.5,
        "para": ["Camila", "Jonathan"],
        "productos": ["Manga, anime y cultura japonesa", "Merchandise de One Piece, Naruto, Demon Slayer", "Ropa y accesorios estilo japonés", "Papelería y artículos kawaii"],
        "tip": "💡 La Rue Sainte-Anne es el 'Japantown' de París. Para Camila es el paraíso total.",
        "comentario": "Zona japonesa de París. Hay tiendas de anime, restaurantes japoneses y papelería kawaii.",
    },
    {
        "nombre": "Louis Vuitton — Champs-Élysées",
        "categoria": "Zapatos y Carteras",
        "direccion": "101 Avenue des Champs-Élysées, Paris 8e",
        "horario": "Lun–Dom 10:00–20:00",
        "precio": 3,
        "rating": 4.3,
        "para": ["Giovanna"],
        "productos": ["Carteras icónicas LV (Speedy, Neverfull)", "Accesorios de cuero", "Pañuelos de seda", "Joyería LV"],
        "tip": "💡 Comprando LV en París ahorras vs Perú. Pide Tax Free — recuperas ~12%. Lista de espera para algunos modelos.",
        "comentario": "La tienda flagship más famosa del mundo. Aunque sea solo para ver, es una experiencia.",
    },
    {
        "nombre": "Avenue Montaigne — Lujo Concentrado",
        "categoria": "Zapatos y Carteras",
        "direccion": "Avenue Montaigne, Paris 8e",
        "horario": "Lun–Sáb 10:00–19:00",
        "precio": 3,
        "rating": 4.7,
        "para": ["Giovanna"],
        "productos": ["Chanel, Dior, Valentino, Givenchy", "Zapatos Christian Louboutin", "Carteras Hermès y Céline", "Joyería Cartier y Van Cleef"],
        "tip": "💡 Es la calle del lujo más importante del mundo. Aunque no compres, es un paseo único.",
        "comentario": "La avenida del lujo parisino. Ambiente espectacular aunque solo sea para pasear.",
    },
    {
        "nombre": "Marché aux Puces de Saint-Ouen",
        "categoria": "Joyería y Accesorios",
        "direccion": "Avenue Michelet, Saint-Ouen (M13 Porte de Clignancourt)",
        "horario": "Sáb–Lun 10:00–18:00",
        "precio": 1,
        "rating": 4.3,
        "para": ["Giovanna", "Jonathan"],
        "productos": ["Joyería vintage y antigüedades", "Ropa de diseñador de segunda mano", "Accesorios únicos y complementos", "Arte, posters y decoración vintage"],
        "tip": "💡 El mercado de pulgas más grande del mundo. Llega temprano y regatéa siempre.",
        "comentario": "Gigantesco mercado de antigüedades. Se pueden encontrar verdaderas joyas a precios únicos.",
    },
    {
        "nombre": "La Vallée Village — Outlet París",
        "categoria": "Outlets y Ofertas",
        "direccion": "3 Cours de la Garonne, Serris (RER A Val d'Europe)",
        "horario": "Lun–Sáb 10:00–19:00 · Dom 11:00–19:00",
        "precio": 2,
        "rating": 4.4,
        "para": ["Giovanna", "Camila"],
        "productos": ["Marcas de lujo con 30-70% descuento", "Sandro, Maje, Isabel Marant rebajados", "Zapatos y carteras de diseño", "A 5 min de Disneyland París"],
        "tip": "💡 Combinar con Disneyland el día 24 — está a 5 min. Aprovecha el Tax Free adicional.",
        "comentario": "Outlet premium con marcas francesas de diseño a precios de outlet. Vale mucho la pena.",
    },
    {
        "nombre": "Kpop Square Paris — Le Marais",
        "categoria": "Tecnología / Geek",
        "direccion": "Rue des Rosiers 12, Paris 4e (Le Marais)",
        "horario": "Lun–Dom 11:00–20:00",
        "precio": 2,
        "rating": 4.6,
        "para": ["Camila"],
        "productos": [
            "Albums y merchandise oficial kpop (BTS, Blackpink, Stray Kids, aespa)",
            "Photocards y inclusions de albums coreanos",
            "Ropa streetwear estilo coreano",
            "Papelería kawaii y coreana",
            "Accesorios y joyería estilo kpop",
        ],
        "tip": "💡 París tiene la mayor comunidad kpop de Europa — las tiendas son enormes y bien surtidas.",
        "comentario": "La mejor tienda kpop de París. Camila va a encontrar todo lo que busca aquí.",
    },
    {
        "nombre": "Manga Café & Store — Rue Sainte-Anne",
        "categoria": "Tecnología / Geek",
        "direccion": "Rue Sainte-Anne 27, Paris 1er",
        "horario": "Mar–Dom 11:00–21:00",
        "precio": 2,
        "rating": 4.7,
        "para": ["Camila", "Jonathan"],
        "productos": [
            "One Piece — colección completa en francés y japonés",
            "Figuras One Piece de alta gama importadas de Japón",
            "Transformers japoneses (Takara Tomy) difíciles de conseguir",
            "Manga en francés — precios únicos",
            "Artbooks y guías oficiales de anime",
            "Figuras de colección Bandai y Kotobukiya",
        ],
        "tip": "💡 Los Transformers Takara Tomy japoneses en París cuestan menos que en cualquier tienda de Perú.",
        "comentario": "La joya del Japantown de París. Importaciones directas de Japón con precios europeos.",
    },
],

# ─────────────────────────────────────────────────────────────────────────
# BRUSELAS
# ─────────────────────────────────────────────────────────────────────────
"Bruselas": [
    {
        "nombre": "Galerie de la Reine / Galeries Royales",
        "categoria": "Souvenirs",
        "direccion": "Galerie de la Reine, Brussels Centre",
        "horario": "Lun–Dom 09:00–22:00",
        "precio": 2,
        "rating": 4.7,
        "para": ["Todos"],
        "productos": ["Chocolate belga premium (Godiva, Neuhaus, Wittamer)", "Cómics belgas originales (Tintín, Los Pitufos, Asterix)", "Lace belga artesanal (encaje de Brujas)", "Cervezas especiales belgas en caja regalo"],
        "tip": "💡 Los cómics belgas en su idioma original son souvenirs únicos para Jonathan.",
        "comentario": "La galería más elegante de Bruselas. Perfecta para souvenirs premium bajo la lluvia.",
    },
    {
        "nombre": "Neuhaus — Chocolatería Belga",
        "categoria": "Gastronomía",
        "direccion": "25-27 Galerie de la Reine, Brussels",
        "horario": "Lun–Sáb 09:30–19:00 · Dom 10:00–18:00",
        "precio": 2,
        "rating": 4.8,
        "para": ["Todos"],
        "productos": ["Pralinés belgas artesanales (inventaron el pralinés)", "Caja regalo personalizada de chocolates", "Trufas, ganaches y caramelos de chocolate", "Ediciones limitadas de temporada"],
        "tip": "💡 Neuhaus inventó el pralinés en 1912. Las cajas regalo son espectaculares y resistentes al viaje.",
        "comentario": "La chocolatería más histórica de Bélgica. Los pralinés son el regalo perfecto.",
    },
    {
        "nombre": "Godiva Flagship — Grand Place",
        "categoria": "Gastronomía",
        "direccion": "Grand Place 22, Brussels",
        "horario": "Lun–Dom 09:00–22:00",
        "precio": 2,
        "rating": 4.5,
        "para": ["Todos"],
        "productos": ["Colecciones exclusivas de Godiva Bélgica", "Cajas de regalo icónicas doradas", "Chocolates con oro comestible", "Trufas y pralinés premium"],
        "tip": "💡 Godiva en Bélgica tiene productos exclusivos que NO se venden fuera del país.",
        "comentario": "Godiva original belga es muy diferente al Godiva exportado. Vale mucho la pena.",
    },
    {
        "nombre": "Delirium Store — Cervezas",
        "categoria": "Gastronomía",
        "direccion": "Impasse de la Fidélité 4, Brussels",
        "horario": "Lun–Dom 10:00–04:00",
        "precio": 1,
        "rating": 4.8,
        "para": ["Jonathan", "Todos"],
        "productos": ["2000+ cervezas belgas disponibles", "Cervezas de Abadía (Chimay, Orval, Rochefort)", "Cervezas Trappist únicas en el mundo", "Pack regalo de cervezas especiales"],
        "tip": "💡 Llevar cervezas especiales belgas en maleta bien embaladas es legal y muy apreciado de regalo.",
        "comentario": "Tiene el récord Guinness de mayor cantidad de cervezas. Jonathan no puede perdérselo.",
    },
    {
        "nombre": "Avenue Louise — Moda y Lujo",
        "categoria": "Ropa y Moda",
        "direccion": "Avenue Louise, Brussels",
        "horario": "Lun–Sáb 10:00–19:00",
        "precio": 3,
        "rating": 4.4,
        "para": ["Giovanna"],
        "productos": ["Marcas de lujo europeas", "Diseñadores belgas (Dries Van Noten, Raf Simons)", "Zapatos y carteras de diseño", "Boutiques independientes de alta moda"],
        "tip": "💡 Los diseñadores belgas son reconocidos mundialmente pero poco conocidos en Latinoamérica.",
        "comentario": "La calle de moda y lujo más importante de Bruselas. Ambiente muy elegante.",
    },
    {
        "nombre": "Bande Dessinée / Comic Shops",
        "categoria": "Tecnología / Geek",
        "direccion": "Rue du Midi 25-27, Brussels",
        "horario": "Mar–Sáb 10:00–18:30",
        "precio": 1,
        "rating": 4.6,
        "para": ["Jonathan", "Camila"],
        "productos": ["Cómics franco-belgas originales (Tintín en 80 idiomas)", "Los Pitufos, Lucky Luke, Asterix colecciones", "Figuras y merchandise de Tintín", "Ediciones limitadas y firmadas"],
        "tip": "💡 Un Tintín en idioma original belga/francés firmado es una pieza de colección única.",
        "comentario": "El Barrio del Cómic de Bruselas. Bélgica es la capital mundial del cómic europeo.",
    },
    {
        "nombre": "Place du Grand Sablon — Antigüedades",
        "categoria": "Joyería y Accesorios",
        "direccion": "Place du Grand Sablon, Brussels",
        "horario": "Sáb 09:00–18:00 · Dom 09:00–14:00",
        "precio": 2,
        "rating": 4.5,
        "para": ["Giovanna", "Jonathan"],
        "productos": ["Joyería vintage y antigua", "Lace belga (encaje artesanal) de colección", "Antigüedades y arte belga", "Marroquinería artesanal"],
        "tip": "💡 El encaje belga (dentelle de Bruxelles) es Patrimonio UNESCO. Pieza única como regalo.",
        "comentario": "El mercado de antigüedades más elegante de Bruselas. Solo fines de semana.",
    },
    {
        "nombre": "Dreamland — Juguetes y Coleccionables",
        "categoria": "Tecnología / Geek",
        "direccion": "Rue Neuve 105, Brussels",
        "horario": "Lun–Sáb 09:30–19:00 · Dom 10:00–18:00",
        "precio": 2,
        "rating": 4.3,
        "para": ["Jonathan", "Camila"],
        "productos": [
            "Figuras Transformers — amplia colección",
            "Lego (más barato que en Perú — mismas series)",
            "Figuras de anime y manga",
            "Juegos de mesa y coleccionables",
            "Merchandise de comics belgas y Marvel/DC",
        ],
        "tip": "💡 Lego en Bélgica es considerablemente más barato que en Perú — ideal para llevar sets grandes.",
        "comentario": "La mayor juguetería de Bélgica. Transformers y Lego son sus puntos fuertes.",
    },
],

# ─────────────────────────────────────────────────────────────────────────
# ÁMSTERDAM
# ─────────────────────────────────────────────────────────────────────────
"Ámsterdam": [
    {
        "nombre": "De 9 Straatjes (Las 9 Calles)",
        "categoria": "Ropa y Moda",
        "direccion": "Tussen de bogen, Amsterdam Centrum",
        "horario": "Lun–Sáb 10:00–18:00 · Dom 12:00–18:00",
        "precio": 2,
        "rating": 4.7,
        "para": ["Giovanna", "Camila"],
        "productos": ["Boutiques de diseñadores holandeses independientes", "Ropa vintage y de segunda mano de calidad", "Accesorios y joyería artesanal holandesa", "Tiendas únicas que no encontrarás en otro lado"],
        "tip": "💡 Las 9 Calles son el corazón del shopping auténtico de Ámsterdam. Aléjate de Kalverstraat turística.",
        "comentario": "El barrio de compras más auténtico de Ámsterdam. Pequeñas boutiques con personalidad propia.",
    },
    {
        "nombre": "P.C. Hooftstraat — Lujo",
        "categoria": "Zapatos y Carteras",
        "direccion": "P.C. Hooftstraat, Amsterdam",
        "horario": "Lun–Sáb 10:00–18:00 · Dom 12:00–18:00",
        "precio": 3,
        "rating": 4.5,
        "para": ["Giovanna"],
        "productos": ["Gucci, Louis Vuitton, Chanel en Amsterdam", "Zapatos Jimmy Choo y Manolo Blahnik", "Carteras Bottega Veneta y Mulberry", "Joyería de lujo"],
        "tip": "💡 Más tranquilo y menos turístico que París. El servicio es excelente y hay menos cola.",
        "comentario": "La calle del lujo de Ámsterdam. Ambiente más relajado que las mismas tiendas en París.",
    },
    {
        "nombre": "Albert Cuyp Market",
        "categoria": "Souvenirs",
        "direccion": "Albert Cuypstraat, Amsterdam De Pijp",
        "horario": "Lun–Sáb 09:00–17:00",
        "precio": 1,
        "rating": 4.4,
        "para": ["Todos"],
        "productos": ["Tulipanes secos y bulbos para llevar", "Queso Gouda y Edam al vacío", "Delft Blue (cerámica azul holandesa)", "Ropa y accesorios a precios de mercado", "Stroopwafels artesanales"],
        "tip": "💡 Los bulbos de tulipán son el souvenir más holandés que existe. Están permitidos en aduana peruana con certificado.",
        "comentario": "El mercado más grande y animado de Ámsterdam. De todo y a buenos precios.",
    },
    {
        "nombre": "Oude Molens — Quesos y Gastronomía",
        "categoria": "Gastronomía",
        "direccion": "Nieuwmarkt 4, Amsterdam",
        "horario": "Lun–Dom 09:00–18:00",
        "precio": 2,
        "rating": 4.6,
        "para": ["Todos"],
        "productos": ["Gouda viejo (Old Amsterdam) al vacío", "Edam y Maasdam en diferentes añadas", "Stroopwafels artesanales empaquetados", "Jenever (ginebra holandesa) en botella pequeña", "Hagelslag (chispas de chocolate para el pan)"],
        "tip": "💡 El queso **Old Amsterdam** en vacío es el regalo gastronómico holandés más valorado. Fácil de transportar.",
        "comentario": "Tienda de quesos artesanales. El Old Amsterdam viejo es completamente diferente al joven.",
    },
    {
        "nombre": "Jutka & Riska — Vintage",
        "categoria": "Ropa y Moda",
        "direccion": "Haarlemmerstraat 143, Amsterdam",
        "horario": "Mar–Sáb 11:00–18:00 · Dom 13:00–17:00",
        "precio": 1,
        "rating": 4.5,
        "para": ["Camila", "Giovanna"],
        "productos": ["Ropa vintage de los 60s-90s", "Accesorios y joyería vintage", "Bolsos y carteras de segunda mano premium", "Piezas únicas imposibles de encontrar"],
        "tip": "💡 El vintage en Ámsterdam tiene calidad y precio muy superiores al de Perú.",
        "comentario": "Tienda de vintage con curaduría excelente. Todo está en buen estado y bien seleccionado.",
    },
    {
        "nombre": "Anime & Manga Amsterdam",
        "categoria": "Tecnología / Geek",
        "direccion": "Kalverstraat 197, Amsterdam",
        "horario": "Lun–Dom 10:00–19:00",
        "precio": 2,
        "rating": 4.4,
        "para": ["Camila", "Jonathan"],
        "productos": ["Manga en inglés y holandés — One Piece, Jujutsu Kaisen, Chainsaw Man", "Figuras de anime: One Piece, Attack on Titan, Demon Slayer", "Kpop: BTS, Blackpink, Stray Kids merchandise", "Ropa y accesorios cosplay", "Merchandise Pokémon y Nintendo", "Figuras Gundam y maquetas"],
        "tip": "💡 Las figuras japonesas importadas en Europa son más baratas que en Perú por el mercado gris.",
        "comentario": "Buena tienda de anime en pleno centro. Para Camila es una parada obligatoria.",
    },
    {
        "nombre": "Delft Blue Shops — Cerámica",
        "categoria": "Joyería y Accesorios",
        "direccion": "Prinsengracht 440, Amsterdam",
        "horario": "Lun–Dom 09:00–18:00",
        "precio": 2,
        "rating": 4.5,
        "para": ["Giovanna", "Todos"],
        "productos": ["Cerámica Delft azul y blanca auténtica con sello", "Miniaturas de casas holandesas con jenever", "Azulejos decorativos pintados a mano", "Sets de tazas y platos Delft originales"],
        "tip": "💡 Las **casitas Delft rellenas de jenever** son el souvenir más icónico de Holanda — verifica el sello de autenticidad.",
        "comentario": "La cerámica Delft azul es Patrimonio Cultural holandés. Las piezas con sello son auténticas.",
    },
    {
        "nombre": "Sephora Amsterdam",
        "categoria": "Perfumes y Cosméticos",
        "direccion": "Kalverstraat 171, Amsterdam",
        "horario": "Lun–Sáb 10:00–20:00 · Dom 12:00–19:00",
        "precio": 2,
        "rating": 4.3,
        "para": ["Giovanna", "Camila"],
        "productos": ["Colecciones exclusivas europeas", "Marcas nórdicas de skincare (BYBI, Kora Organics)", "Perfumes de nicho", "Maquillaje last minute antes de volver"],
        "tip": "💡 Última oportunidad para compras de cosmética antes del vuelo de regreso.",
        "comentario": "La última parada de cosmética antes de volar a Lima. Últimos regalos pendientes.",
    },
    {
        "nombre": "Outlet en Bataviastad — Lelystad",
        "categoria": "Outlets y Ofertas",
        "direccion": "Oostvaardersdijk 01-13, Lelystad",
        "horario": "Lun–Dom 10:00–18:00",
        "precio": 2,
        "rating": 4.3,
        "para": ["Giovanna", "Camila"],
        "productos": ["Marcas europeas con 30-60% descuento", "Calvin Klein, Tommy Hilfiger, G-Star Raw", "Nike, Adidas outlet", "Zapatos y carteras de diseño rebajados"],
        "tip": "💡 A 45 min de Ámsterdam en tren. Vale la pena si van el día 29 antes del crucero.",
        "comentario": "El outlet más grande de Holanda. Para últimas compras grandes antes de volver.",
    },
    {
        "nombre": "Kokoro — Kpop & Japanese Culture",
        "categoria": "Tecnología / Geek",
        "direccion": "Nieuwendijk 178, Amsterdam Centrum",
        "horario": "Lun–Dom 10:00–20:00",
        "precio": 2,
        "rating": 4.5,
        "para": ["Camila"],
        "productos": [
            "Albums kpop físicos — BTS, Blackpink, Stray Kids, IVE, Le Sserafim",
            "Merchandise oficial de grupos kpop",
            "Cultura japonesa: papelería kawaii, accesorios, ropa",
            "Photocards y merchandise de One Piece",
            "Figuras y juguetes japoneses",
        ],
        "tip": "💡 Última oportunidad para compras de kpop antes de volar a Lima.",
        "comentario": "Tienda especializada en cultura asiática en el centro de Ámsterdam.",
    },
    {
        "nombre": "Game Mania Amsterdam — Geek & Gaming",
        "categoria": "Tecnología / Geek",
        "direccion": "Kalverstraat 29, Amsterdam",
        "horario": "Lun–Sáb 10:00–20:00 · Dom 12:00–18:00",
        "precio": 2,
        "rating": 4.3,
        "para": ["Jonathan", "Camila"],
        "productos": [
            "Videojuegos PS5, Switch, Xbox — precios europeos",
            "Figuras Transformers y Hot Toys",
            "Funko Pop — gran colección",
            "Merchandise de videojuegos y cultura pop",
            "Consolas retro y juegos de colección",
        ],
        "tip": "💡 Los videojuegos en Europa pueden ser 20-30% más baratos que en Perú.",
        "comentario": "La cadena de gaming más grande de Holanda. Buena selección de figuras coleccionables.",
    },
],

}

# ══════════════════════════════════════════════════════════════════════════
# UI PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════

def render_tienda_card(tienda: dict, ciudad: str):
    """Renderiza una card de tienda."""
    with st.container(border=True):
        # Header
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            cat_emoji = CATEGORIA_EMOJI.get(tienda["categoria"], "🛍️")
            st.markdown(f"### {cat_emoji} {tienda['nombre']}")
            st.caption(f"📍 {tienda['direccion']}")
        with col2:
            st.metric("Rating", f"{tienda['rating']}/5")
        with col3:
            niveles = {"€": "Económico", "€€": "Moderado", "€€€": "Lujo"}
            precio_str = "€" * tienda["precio"]
            st.metric("Precio", mostrar_precio(precio_str), mostrar_precio(niveles.get(precio_str, ""), ""))

        # Para quién
        para_tags = " ".join([
            f"{PARA_QUIEN.get(p, '👤')} {p}"
            for p in tienda["para"]
        ])
        st.caption(f"**Para:** {para_tags}")

        # Horario
        st.caption(f"🕐 {tienda['horario']}")

        st.divider()

        # Productos destacados
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("**🛍️ Qué comprar:**")
            for prod in tienda["productos"]:
                st.caption(f"• {prod}")

        with col2:
            # Botón Maps
            url = maps_url(tienda["nombre"], ciudad)
            st.link_button(
                "📍 Ver en Maps",
                url,
                use_container_width=True,
                type="primary"
            )
            st.write("")

        # Tip de ahorro
        if tienda.get("tip"):
            st.info(tienda["tip"])

        # Comentario
        if tienda.get("comentario"):
            st.caption(f"💬 _{tienda['comentario']}_")


def mostrar():
    st.title("🛒 Shopping Guide")
    st.caption("Tiendas, ofertas y souvenirs curados para la familia — por ciudad y categoría")

    is_admin = st.session_state.get("_is_admin", False)

    # ── Filtros en la parte superior ──────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        ciudad_sel = st.selectbox(
            "📍 Ciudad:",
            ["Todas"] + list(TIENDAS.keys()),
            key="shop_ciudad"
        )
    with col2:
        todas_cats = sorted(set(
            t["categoria"]
            for tiendas in TIENDAS.values()
            for t in tiendas
        ))
        cat_sel = st.selectbox(
            "🏷️ Categoría:",
            ["Todas"] + todas_cats,
            key="shop_cat"
        )
    with col3:
        persona_sel = st.selectbox(
            "👤 Para quién:",
            ["Todos", "Jonathan", "Camila", "Giovanna"],
            key="shop_persona"
        )

    # Búsqueda rápida
    busqueda = st.text_input(
        "🔍 Buscar tienda o producto...",
        placeholder="ej: chocolate, manga, perfume...",
        key="shop_busqueda"
    )

    st.divider()

    # ── Aplicar filtros ───────────────────────────────────────────────────
    ciudades_mostrar = (
        list(TIENDAS.keys()) if ciudad_sel == "Todas"
        else [ciudad_sel]
    )

    total_tiendas = 0

    for ciudad in ciudades_mostrar:
        tiendas_ciudad = TIENDAS.get(ciudad, [])

        # Filtrar por categoría
        if cat_sel != "Todas":
            tiendas_ciudad = [t for t in tiendas_ciudad if t["categoria"] == cat_sel]

        # Filtrar por persona
        if persona_sel != "Todos":
            tiendas_ciudad = [t for t in tiendas_ciudad if persona_sel in t["para"]]

        # Filtrar por búsqueda
        if busqueda:
            busq = busqueda.lower()
            tiendas_ciudad = [
                t for t in tiendas_ciudad
                if busq in t["nombre"].lower()
                or busq in t["comentario"].lower()
                or any(busq in p.lower() for p in t["productos"])
                or busq in t["categoria"].lower()
            ]

        if not tiendas_ciudad:
            continue

        total_tiendas += len(tiendas_ciudad)

        # Header de ciudad
        CIUDAD_EMOJIS = {
            "Madrid": "🇪🇸", "Bayona": "🇫🇷", "París": "🇫🇷",
            "Bruselas": "🇧🇪", "Ámsterdam": "🇳🇱"
        }
        emoji = CIUDAD_EMOJIS.get(ciudad, "📍")

        st.markdown(f"## {emoji} {ciudad}")
        st.caption(f"{len(tiendas_ciudad)} tienda(s) encontrada(s)")

        # Agrupar por categoría dentro de la ciudad
        categorias_ciudad = dict()
        for t in tiendas_ciudad:
            cat = t["categoria"]
            if cat not in categorias_ciudad:
                categorias_ciudad[cat] = []
            categorias_ciudad[cat].append(t)

        for cat, tiendas_cat in categorias_ciudad.items():
            cat_emoji = CATEGORIA_EMOJI.get(cat, "🛍️")
            with st.expander(f"{cat_emoji} {cat} — {len(tiendas_cat)} tienda(s)", expanded=True):
                for tienda in tiendas_cat:
                    render_tienda_card(tienda, ciudad)

        st.divider()

    if total_tiendas == 0:
        if busqueda:
            # ── Lady fallback: busca en internet ──────────────────────
            ciudad_busqueda = ciudad_sel if ciudad_sel != "Todas" else "Europa"
            st.warning(f"🔍 No encontré **'{busqueda}'** en mi base de datos para {ciudad_busqueda}.")
            st.markdown("### 🐾 Lady busca en internet por ti...")

            cache_key = f"lady_search_{busqueda}_{ciudad_busqueda}"
            if cache_key not in st.session_state:
                st.session_state[cache_key] = None

            if st.session_state[cache_key]:
                st.success("🐾 Lady encontró esto:")
                st.markdown(st.session_state[cache_key])
            else:
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.caption(
                        f"Lady buscará tiendas de **'{busqueda}'** en **{ciudad_busqueda}** "
                        f"con direcciones, horarios y tips reales."
                    )
                with col2:
                    if st.button("🐾 Buscar con Lady", type="primary", use_container_width=True):
                        with st.spinner("🐾 Lady está olfateando las mejores tiendas..."):
                            resultado = _buscar_con_lady(busqueda, ciudad_busqueda, persona_sel)
                        st.session_state[cache_key] = resultado
                        st.rerun()
        else:
            st.info("🔍 No se encontraron tiendas con los filtros seleccionados. Prueba con otros filtros.")

    # ── Resumen de tips Tax Free ──────────────────────────────────────────
    with st.expander("💡 Guía Tax Free — Recupera hasta 12% de tus compras", expanded=False):
        st.markdown("""
**¿Qué es el Tax Free?**
Como turistas fuera de la UE, pueden recuperar el IVA de sus compras al salir de Europa.

**Cómo funciona:**
1. Al comprar +€100 en una misma tienda, pide el **formulario de Tax Free**
2. La tienda sella el formulario
3. Al salir por el aeropuerto (Schiphol o Barajas), busca el mostrador **Tax Refund / Détaxe**
4. Sella el formulario con Aduana y cobra el reembolso en efectivo o tarjeta

**Cuánto recuperas:**
- España: ~13% del precio de compra
- Francia: ~12% del precio de compra  
- Bélgica: ~13% del precio de compra
- Países Bajos: ~15% del precio de compra

**Tiendas que aplican:**
- El Corte Inglés ✅ | Galeries Lafayette ✅ | Louis Vuitton ✅
- Zara ✅ | Sephora ✅ | Camper ✅ | La mayoría de tiendas grandes

**💡 Tip:** Agrupa compras en menos tiendas para superar el mínimo más fácilmente.
        """)

    with st.expander("🧳 Tips para llevar compras a Lima", expanded=False):
        st.markdown("""
**Productos que pasan sin problema:**
- ✅ Ropa y calzado (sin restricción)
- ✅ Cosméticos y perfumes sellados
- ✅ Chocolate y dulces empaquetados
- ✅ Quesos al vacío sin corteza
- ✅ Jamón al vacío etiquetado
- ✅ Vinos y licores (límite: 3 litros por persona)
- ✅ Manga, comics y libros
- ✅ Figuras y juguetes
- ✅ Cerámica (bien embalada)

**Con declaración/certificado:**
- ⚠️ Bulbos de tulipán: necesitan certificado fitosanitario del vendedor

**Límite de equipaje sugerido:**
- Reserva al menos 10kg de capacidad de regreso para compras
- Las maletas adicionales en Iberia desde Ámsterdam cuestan ~€50
        """)