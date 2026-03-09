import os

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DB_PATH     = os.path.join(BASE_DIR, "optigest.db")
APP_NAME    = "OptiGest Pro"
APP_VERSION = "3.0"
COMPANY     = "Wholesale Optique"

# ── Palette dark premium ──────────────────────────────────────────────────────
DARK = {
    "bg":           "#0f1117",
    "surface":      "#1a1d27",
    "surface2":     "#22263a",
    "surface3":     "#2a2f45",
    "primary":      "#6c63ff",
    "primary_dk":   "#5a52e0",
    "primary_glow": "#3d3a8a",
    "accent":       "#00d4aa",
    "accent_dk":    "#00b890",
    "success":      "#22c55e",
    "danger":       "#ef4444",
    "warning":      "#f59e0b",
    "info":         "#38bdf8",
    "text":         "#e8eaf6",
    "text_muted":   "#6b7280",
    "text_dim":     "#9ca3af",
    "border":       "#2d3149",
    "border_light": "#3d4263",
    "input_bg":     "#13161f",
    "sidebar_w":    220,
    "font":         "Segoe UI",
    # matplotlib
    "mpl_bg":       "#1a1d27",
    "mpl_fg":       "#e8eaf6",
    "mpl_grid":     "#2d3149",
    "mpl_bar1":     "#6c63ff",
    "mpl_bar2":     "#00d4aa",
    "mpl_line":     "#6c63ff",
    "mpl_pie":      ["#6c63ff","#00d4aa","#f59e0b","#ef4444","#38bdf8","#a78bfa","#34d399"],
}

LIGHT = {
    "bg":           "#f0f2f8",
    "surface":      "#ffffff",
    "surface2":     "#e8ecf7",
    "surface3":     "#dde3f5",
    "primary":      "#4f6ef7",
    "primary_dk":   "#3b56d4",
    "primary_glow": "#dde3f5",
    "accent":       "#0284c7",
    "accent_dk":    "#0369a1",
    "success":      "#16a34a",
    "danger":       "#dc2626",
    "warning":      "#d97706",
    "info":         "#0284c7",
    "text":         "#1e2235",
    "text_muted":   "#64748b",
    "text_dim":     "#94a3b8",
    "border":       "#d1d5e8",
    "border_light": "#e2e8f0",
    "input_bg":     "#f8f9fd",
    "sidebar_w":    220,
    "font":         "Segoe UI",
    "mpl_bg":       "#ffffff",
    "mpl_fg":       "#1e2235",
    "mpl_grid":     "#e2e8f0",
    "mpl_bar1":     "#4f6ef7",
    "mpl_bar2":     "#0284c7",
    "mpl_line":     "#4f6ef7",
    "mpl_pie":      ["#4f6ef7","#0284c7","#d97706","#dc2626","#16a34a","#7c3aed","#0891b2"],
}

# Active theme (mutable)
T = dict(DARK)

def set_theme(mode: str):
    """mode = 'dark' | 'light'"""
    T.clear()
    T.update(DARK if mode == "dark" else LIGHT)

ROLES = {
    "Administrateur": ["dashboard","pos","purchases","inventory","customers","suppliers","reports","users","settings"],
    "Manager":        ["dashboard","pos","purchases","inventory","customers","reports"],
    "Vendeur":        ["dashboard","pos","customers"],
}

NAV = [
    ("dashboard",  "󰕮  Dashboard",      "dashboard"),
    ("pos",        "󰦨  Caisse POS",     "pos"),
    ("purchases",  "󰋑  Achats",         "purchases"),
    ("inventory",  "󰜱  Inventaire",     "inventory"),
    ("customers",  "󰉌  Clients",        "customers"),
    ("suppliers",  "󰏗  Fournisseurs",   "suppliers"),
    ("reports",    "󰈸  Rapports",       "reports"),
    ("users",      "󰀄  Utilisateurs",   "users"),
    ("settings",   "󰒓  Paramètres",     "settings"),
]

# Fallback nav labels (ASCII-safe)
NAV_LABELS = {
    "dashboard":  "📊  Dashboard",
    "pos":        "💳  Caisse POS",
    "purchases":  "🛒  Achats",
    "inventory":  "📦  Inventaire",
    "customers":  "👥  Clients",
    "suppliers":  "🏭  Fournisseurs",
    "reports":    "📈  Rapports",
    "users":      "👤  Utilisateurs",
    "settings":   "⚙   Paramètres",
}

PAYMENT_METHODS = ["Espèces", "Carte bancaire", "Virement", "Chèque", "Crédit"]

LENS_CATEGORIES = ["Unifocal", "Progressif", "Bifocal", "Lentilles", "Solaire", "Accessoire"]
LENS_TYPES      = ["Organique", "Minéral", "Polycarbonate", "Trivex", "Hi-index"]
LENS_INDICES    = ["1.50", "1.53", "1.56", "1.60", "1.67", "1.74", "N/A"]
COATINGS        = ["Anti-reflet", "AR + UV", "Photochromique", "Polarisant",
                   "Blue Protect", "Durci", "Miroir", "Standard"]
