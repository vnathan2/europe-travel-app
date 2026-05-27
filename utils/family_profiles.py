# utils/family_profiles.py
# Perfiles de gustos de la familia para recomendaciones personalizadas
# Usado por Travel Concierge Bot para personalizar sugerencias

PERFILES_FAMILIA = {
    "jonathan": {
        "nombre": "Jonathan",
        "rol": "admin",
        "emoji": "👑",
        "gustos": [
            "fútbol", "deportes", "comics", "videojuegos", "música",
            "comida", "lugares turísticos", "souvenirs", "Transformers",
            "manga", "anime", "películas", "series", "lucha libre",
            "tecnología",
        ],
        "descripcion": (
            "Le apasionan los deportes especialmente el fútbol, "
            "la cultura geek (comics, manga, anime, Transformers, videojuegos), "
            "la tecnología y la lucha libre. Disfruta la buena comida, "
            "los lugares turísticos y coleccionar souvenirs únicos."
        ),
        "recomendaciones_tipo": [
            "estadios de fútbol y tours deportivos",
            "tiendas de comics, manga y anime",
            "tiendas de tecnología y gadgets",
            "merchandise de Transformers y figuras coleccionables",
            "restaurantes con buena comida local auténtica",
            "souvenirs únicos y originales",
            "lugares con historia y cultura",
            "tiendas de videojuegos y gaming",
        ],
    },
    "camila": {
        "nombre": "Camila",
        "rol": "familiar",
        "emoji": "🎀",
        "gustos": [
            "comics", "anime", "manga", "kpop", "cultura japonesa",
            "películas", "series", "música", "comida china", "comida japonesa",
            "makis", "rolls", "tacos", "burritos", "pasta", "videojuegos",
            "One Piece", "maquillaje", "ropa", "accesorios", "perfumes",
            "animales domésticos", "perros", "gatos",
        ],
        "descripcion": (
            "Adolescente de 15 años apasionada por la cultura asiática "
            "(anime, manga, kpop, cultura japonesa, One Piece), "
            "la moda y el maquillaje. Le encanta la comida asiática y fusión "
            "(makis, rolls, comida japonesa y china), también tacos y pasta. "
            "Fan de los videojuegos, comics y los animales domésticos."
        ),
        "recomendaciones_tipo": [
            "tiendas de anime, manga y cultura japonesa",
            "tiendas de kpop y merchandise de One Piece",
            "restaurantes de comida japonesa, sushi, makis y rolls",
            "tiendas de maquillaje y cosméticos (Sephora, MAC, NYX)",
            "tiendas de ropa y accesorios para adolescentes",
            "perfumes y accesorios de moda",
            "tiendas de videojuegos y gaming",
            "cafeterías temáticas de anime o cultura pop",
        ],
    },
    "giovanna": {
        "nombre": "Giovanna",
        "rol": "familiar",
        "emoji": "🌹",
        "gustos": [
            "carteras", "zapatos", "ropa", "maquillaje", "accesorios",
            "perfumes", "música", "gastronomía", "entretenimiento",
            "cultura", "cine", "películas", "ofertas", "souvenirs",
        ],
        "descripcion": (
            "Le encanta la moda en todas sus formas: carteras, zapatos, "
            "ropa, accesorios y perfumes de calidad. Disfruta la gastronomía "
            "local, la cultura, el cine y las películas. Siempre atenta "
            "a las mejores ofertas y souvenirs especiales."
        ),
        "recomendaciones_tipo": [
            "tiendas de carteras y bolsos de marca o artesanales",
            "zapaterías locales y marcas europeas",
            "tiendas de ropa y moda europea",
            "perfumerías y tiendas de cosméticos",
            "accesorios de moda y joyería artesanal",
            "restaurantes gastronómicos y experiencias culinarias",
            "mercados y tiendas de ofertas y outlets",
            "museos, teatros y actividades culturales",
            "souvenirs de calidad y productos locales únicos",
        ],
    },
}


def get_contexto_perfiles() -> str:
    """
    Genera el contexto de perfiles para inyectar en el prompt de Gemini.
    Personaliza las recomendaciones según los gustos de cada miembro.
    """
    contexto = """
═══════════════════════════════════════════════════
PERFILES DE GUSTOS DE LA FAMILIA — USA ESTO PARA
PERSONALIZAR TODAS TUS RECOMENDACIONES
═══════════════════════════════════════════════════

"""
    for perfil in PERFILES_FAMILIA.values():
        contexto += f"{perfil['emoji']} {perfil['nombre'].upper()}:\n"
        contexto += f"{perfil['descripcion']}\n"
        contexto += "Tipos de lugares que le gustan:\n"
        for rec in perfil["recomendaciones_tipo"]:
            contexto += f"  • {rec}\n"
        contexto += "\n"

    contexto += """
═══════════════════════════════════════════════════
INSTRUCCIONES DE PERSONALIZACIÓN:
- Cuando alguien pregunte "qué puedo comprar", adapta según quién pregunta
- Si la pregunta no especifica para quién, sugiere opciones para los 3
- Para Jonathan: prioriza fútbol, tecnología, geek culture, comida
- Para Camila: prioriza anime/manga, moda, comida asiática, kpop
- Para Giovanna: prioriza moda, gastronomía, carteras/zapatos, cultura
- Siempre menciona precios aproximados en euros y soles peruanos
═══════════════════════════════════════════════════
"""
    return contexto


def get_perfil_por_nombre(nombre: str) -> dict:
    """Retorna el perfil de un miembro de la familia por nombre."""
    nombre_lower = nombre.lower()
    for key, perfil in PERFILES_FAMILIA.items():
        if key in nombre_lower or perfil["nombre"].lower() in nombre_lower:
            return perfil
    return {}


def get_recomendacion_ciudad(ciudad: str) -> dict:
    """
    Retorna recomendaciones específicas por ciudad y persona.
    Usado para enriquecer el contexto del bot.
    """
    RECOMENDACIONES_CIUDAD = {
        "Madrid": {
            "jonathan": [
                "Tour Estadio Santiago Bernabéu — museo y campo del Real Madrid",
                "FNAC Gran Vía — tecnología, videojuegos y comics",
                "Tiendas de manga en Calle Montera y alrededores",
                "Mercado de Fuencarral — tiendas alternativas y geek",
            ],
            "camila": [
                "Tiendas de anime y manga en el barrio Malasaña",
                "Kpop stores en Gran Vía y Centro Comercial Plaza Norte 2",
                "Sephora Gran Vía — maquillaje y cosméticos",
                "Barrio de Malasaña — ropa vintage y accesorios para adolescentes",
                "Restaurantes de sushi y comida japonesa en Lavapiés",
            ],
            "giovanna": [
                "El Corte Inglés Callao — moda, carteras y zapatos de marca",
                "Calle Serrano — tiendas de lujo y marcas europeas",
                "Mercado de San Miguel — gastronomía y productos locales",
                "Zara, Mango, Massimo Dutti en Gran Vía",
                "Casa Ciriaco — gastronomía madrileña tradicional",
            ],
        },
        "París": {
            "jonathan": [
                "Parc des Princes o Stade de France — fútbol parisino",
                "Fnac Champs-Élysées — tecnología y videojuegos",
                "Japan Expo si hay — cultura manga y anime",
                "Tiendas de comics en el barrio Saint-Michel",
            ],
            "camila": [
                "Japantown París (Rue Sainte-Anne) — manga, anime y comida japonesa",
                "Sephora Champs-Élysées — maquillaje y cosméticos premium",
                "Galeries Lafayette — ropa y accesorios de moda",
                "Restaurantes japoneses en Rue Sainte-Anne",
                "Kpop stores en el barrio Le Marais",
            ],
            "giovanna": [
                "Le Marais — boutiques de moda, carteras y accesorios artesanales",
                "Galeries Lafayette Boulevard Haussmann — moda de lujo",
                "Chanel, Dior, Louis Vuitton en Avenue Montaigne",
                "Ladurée — macarons y pasteles de lujo",
                "Le Bon Marché — grand magasin exclusivo",
            ],
        },
        "Bruselas": {
            "jonathan": [
                "Atomium — arquitectura icónica y tecnología",
                "Comic Strip Center — museo del cómic belga (Tintín, Asterix)",
                "Tiendas de comics en Rue du Midi",
            ],
            "camila": [
                "Animexx stores en el centro de Bruselas",
                "ICI Paris XL — perfumes y cosméticos con buenos precios",
                "City 2 Shopping Center — moda y accesorios",
            ],
            "giovanna": [
                "Galerie de la Reine — boutiques elegantes y souvenirs de lujo",
                "Godiva, Neuhaus, Leonidas — chocolate belga premium",
                "Avenue Louise — tiendas de lujo y moda",
                "Grand Place — artesanías y souvenirs únicos belgas",
            ],
        },
        "Ámsterdam": {
            "jonathan": [
                "Johan Cruyff Arena — estadio del Ajax Amsterdam",
                "Game Mania — tienda de videojuegos",
                "Tiendas de comics en Spuistraat",
                "NEMO Science Museum — tecnología e innovación",
            ],
            "camila": [
                "Manga/anime stores en el centro (Kalverstraat)",
                "Sephora Amsterdam — cosméticos y maquillaje",
                "De 9 Straatjes (Las 9 Calles) — ropa vintage y accesorios únicos",
                "Restaurantes japoneses en Leidseplein",
            ],
            "giovanna": [
                "P.C. Hooftstraat — calle de lujo con Gucci, Louis Vuitton, Chanel",
                "De 9 Straatjes — boutiques artesanales, carteras y accesorios",
                "Albert Cuyp Market — el mercado más grande con todo tipo de productos",
                "Mendo — librería y tienda de diseño de lujo",
                "Restaurantes con estrella Michelin en el canal Herengracht",
            ],
        },
    }
    return RECOMENDACIONES_CIUDAD.get(ciudad, {})
