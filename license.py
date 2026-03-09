"""
license.py — Moteur de licence OptiGest Pro v3
================================================
Logique :
  1. Machine ID  = SHA256(uuid + hostname + cpu_count) → 16 hex chars
  2. Clé valide  = HMAC-SHA256(secret + machine_id + expiry) → formatée XXXX-XXXX-XXXX-XXXX
  3. La clé est stockée dans la DB (settings) après activation
  4. À chaque démarrage : recalcul machine_id, re-vérification HMAC, vérif expiry
  5. Si invalide → LockScreen CTk (verrouillage total, app inutilisable)

Ton outil privé : tools/keygen.py
"""

import hashlib, hmac, platform, uuid, datetime, os, sys
import customtkinter as ctk
from config import T, APP_NAME, APP_VERSION

# ── Secret partagé (NE PAS DIVULGUER) ─────────────────────────────────────────
# Change cette chaîne avant de distribuer — elle est le cœur du système
_SECRET = b"0ptiG3st#Qu3id!2025$M@roc"


# ══════════════════════════════════════════════════════════════════════════════
# MACHINE ID
# ══════════════════════════════════════════════════════════════════════════════
def get_machine_id() -> str:
    """Retourne un identifiant unique et stable lié au matériel."""
    try:
        node   = str(uuid.getnode())
        host   = platform.node().lower()
        cpu    = str(platform.processor() or platform.machine())
        raw    = f"{node}:{host}:{cpu}"
        digest = hashlib.sha256(raw.encode()).hexdigest()
        return digest[:16].upper()
    except Exception:
        return "0000000000000000"


def format_machine_id(mid: str) -> str:
    """Affichage lisible : XXXX-XXXX-XXXX-XXXX"""
    m = mid.upper().ljust(16, "0")[:16]
    return f"{m[0:4]}-{m[4:8]}-{m[8:12]}-{m[12:16]}"


# ══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATION DE CLÉ  (utilisé dans tools/keygen.py)
# ══════════════════════════════════════════════════════════════════════════════
def generate_key(machine_id: str, expiry: str) -> str:
    """
    Génère une clé pour machine_id avec date d'expiration.
    expiry format : 'YYYY-MM-DD'  ou  'permanent'
    Retourne : 'XXXX-XXXX-XXXX-XXXX-XXXX'  (20 hex chars formatés)
    """
    mid_clean = machine_id.replace("-", "").upper()
    payload   = f"{mid_clean}:{expiry}".encode()
    digest    = hmac.new(_SECRET, payload, hashlib.sha256).hexdigest()
    # Préfixe expiry encodé (4 chars) + 16 chars HMAC
    if expiry == "permanent":
        prefix = "PERM"
    else:
        # encode YYYYMMDD → base36-like 4 chars
        try:
            d = datetime.datetime.strptime(expiry, "%Y-%m-%d")
            days = (d - datetime.datetime(2020, 1, 1)).days
            prefix = f"{days:04X}"
        except Exception:
            prefix = "FFFF"
    raw = (prefix + digest[:16]).upper()
    return f"{raw[0:5]}-{raw[5:10]}-{raw[10:15]}-{raw[15:20]}"


# ══════════════════════════════════════════════════════════════════════════════
# VÉRIFICATION
# ══════════════════════════════════════════════════════════════════════════════
def verify_key(key: str, machine_id: str) -> tuple[bool, str]:
    """
    Vérifie une clé.
    Retourne (True, "OK") ou (False, "raison")
    """
    try:
        raw = key.replace("-", "").upper()
        if len(raw) != 20:
            return False, "Format de clé invalide"

        prefix = raw[:4]
        hmac_part = raw[4:20]

        # Décode expiry
        if prefix == "PERM":
            expiry = "permanent"
        else:
            try:
                days = int(prefix, 16)
                exp_date = datetime.datetime(2020, 1, 1) + datetime.timedelta(days=days)
                expiry = exp_date.strftime("%Y-%m-%d")
                # Vérifie expiration
                if exp_date.date() < datetime.date.today():
                    return False, f"Licence expirée le {expiry}"
            except Exception:
                return False, "Format de clé invalide"

        # Recompute HMAC
        mid_clean = machine_id.replace("-", "").upper()
        payload   = f"{mid_clean}:{expiry}".encode()
        expected  = hmac.new(_SECRET, payload, hashlib.sha256).hexdigest()[:16].upper()

        if not hmac.compare_digest(hmac_part, expected):
            return False, "Clé invalide pour ce poste"

        return True, expiry

    except Exception as e:
        return False, f"Erreur vérification : {e}"


# ══════════════════════════════════════════════════════════════════════════════
# CHECK AU DÉMARRAGE
# ══════════════════════════════════════════════════════════════════════════════
def check_license() -> tuple[bool, str]:
    """
    Appelé au démarrage.
    Lit la clé depuis la DB settings, vérifie contre machine_id courant.
    Retourne (True, expiry) ou (False, raison)
    """
    try:
        from database.models import get_settings
        settings = get_settings()
        key = settings.get("license_key", "").strip()
        if not key:
            return False, "Aucune licence activée"
        mid = get_machine_id()
        return verify_key(key, mid)
    except Exception as e:
        return False, f"Erreur lecture licence : {e}"


def activate_license(key: str) -> tuple[bool, str]:
    """
    Tente d'activer une clé. Si valide, la stocke en DB.
    Retourne (True, expiry) ou (False, raison)
    """
    mid = get_machine_id()
    ok, info = verify_key(key, mid)
    if ok:
        from database.models import set_setting
        set_setting("license_key", key.strip().upper())
    return ok, info


# ══════════════════════════════════════════════════════════════════════════════
# ÉCRAN DE VERROUILLAGE
# ══════════════════════════════════════════════════════════════════════════════
class LockScreen(ctk.CTkToplevel):
    """
    Fenêtre modale de verrouillage — app totalement bloquée.
    Si activation réussie → appelle on_unlocked() et se détruit.
    """

    def __init__(self, parent, reason: str, on_unlocked=None):
        super().__init__(parent)
        self.on_unlocked = on_unlocked
        self.title(f"{APP_NAME} — Activation requise")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.grab_set()         # Modale — bloque toute interaction derrière
        self.attributes("-topmost", True)

        w, h = 520, 580
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.configure(fg_color=T["bg"])
        self._build(reason)

    def _build(self, reason: str):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=T["danger"], corner_radius=0, height=100)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🔒", font=("Segoe UI Emoji", 36),
                     text_color="#fff").pack(pady=(16, 2))
        ctk.CTkLabel(hdr, text="Licence requise",
                     font=(T["font"], 16, "bold"), text_color="#fff").pack()

        body = ctk.CTkFrame(self, fg_color=T["surface"], corner_radius=0)
        body.pack(fill="both", expand=True)
        inner = ctk.CTkFrame(body, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=40, pady=20)

        # Raison
        ctk.CTkLabel(inner, text=reason,
                     font=(T["font"], 11), text_color=T["danger"],
                     wraplength=400).pack(pady=(0, 16))

        # Machine ID
        mid = get_machine_id()
        mid_fmt = format_machine_id(mid)
        mid_card = ctk.CTkFrame(inner, fg_color=T["surface2"], corner_radius=10)
        mid_card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(mid_card, text="🖥  Identifiant de ce poste",
                     font=(T["font"], 10), text_color=T["text_muted"]).pack(pady=(10, 4))
        ctk.CTkLabel(mid_card, text=mid_fmt,
                     font=("Consolas", 18, "bold"), text_color=T["accent"]).pack()
        ctk.CTkLabel(mid_card,
                     text="Communiquez ce code à votre revendeur pour obtenir votre clé.",
                     font=(T["font"], 9), text_color=T["text_muted"],
                     wraplength=380).pack(pady=(4, 10))

        # Copier ID
        ctk.CTkButton(mid_card, text="📋  Copier l'identifiant",
                      fg_color=T["surface3"], hover_color=T["border"],
                      text_color=T["text"], font=(T["font"], 10),
                      height=30, corner_radius=6,
                      command=lambda: self._copy(mid_fmt)).pack(pady=(0, 10))

        # Saisie clé
        ctk.CTkLabel(inner, text="Clé de licence",
                     font=(T["font"], 10), text_color=T["text_muted"],
                     anchor="w").pack(anchor="w", pady=(0, 4))
        self.key_var = ctk.StringVar()
        self.key_entry = ctk.CTkEntry(inner, textvariable=self.key_var,
                                      placeholder_text="XXXXX-XXXXX-XXXXX-XXXXX",
                                      fg_color=T["input_bg"], border_color=T["border"],
                                      text_color=T["text"],
                                      font=("Consolas", 13),
                                      height=42, corner_radius=8)
        self.key_entry.pack(fill="x")
        self.key_entry.bind("<Return>", lambda e: self._activate())

        self.msg_var = ctk.StringVar()
        ctk.CTkLabel(inner, textvariable=self.msg_var,
                     font=(T["font"], 10), text_color=T["danger"]).pack(pady=(6, 0))

        ctk.CTkButton(inner, text="🔓  Activer la licence",
                      command=self._activate,
                      fg_color=T["primary"], hover_color=T["primary_dk"],
                      text_color="#fff", font=(T["font"], 13, "bold"),
                      height=44, corner_radius=10).pack(fill="x", pady=(12, 0))

        ctk.CTkButton(inner, text="✖  Quitter",
                      command=self.destroy,
                      fg_color="transparent", hover_color=T["surface3"],
                      text_color=T["text_muted"], font=(T["font"], 11),
                      height=34, corner_radius=8).pack(fill="x", pady=(6, 0))

        # Footer
        ctk.CTkLabel(self,
                     text=f"{APP_NAME} v{APP_VERSION}  —  Contactez votre revendeur",
                     font=(T["font"], 9), text_color=T["text_muted"],
                     fg_color=T["bg"]).pack(pady=8)

        self.key_entry.focus()

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.msg_var.set("✅  Identifiant copié dans le presse-papiers")
        self.after(3000, lambda: self.msg_var.set(""))

    def _activate(self):
        key = self.key_var.get().strip()
        if not key:
            self.msg_var.set("❌  Veuillez saisir une clé de licence")
            return
        ok, info = activate_license(key)
        if ok:
            self.msg_var.set("")
            self._show_success(info)
        else:
            self.msg_var.set(f"❌  {info}")

    def _show_success(self, expiry: str):
        pop = ctk.CTkToplevel(self)
        pop.title("Activation réussie")
        pop.geometry("340x200")
        pop.grab_set()
        pop.configure(fg_color=T["surface"])
        ctk.CTkLabel(pop, text="✅  Licence activée !",
                     font=(T["font"], 16, "bold"), text_color=T["success"]).pack(pady=(28, 8))
        exp_txt = "Licence permanente" if expiry == "permanent" else f"Expire le : {expiry}"
        ctk.CTkLabel(pop, text=exp_txt,
                     font=(T["font"], 11), text_color=T["text_muted"]).pack()
        ctk.CTkButton(pop, text="Démarrer l'application",
                      command=lambda: self._finish(pop),
                      fg_color=T["success"], hover_color="#16a34a",
                      text_color="#fff", font=(T["font"], 12, "bold"),
                      height=40, corner_radius=8).pack(pady=20)

    def _finish(self, popup):
        popup.destroy()
        self.grab_release()
        self.destroy()
        if self.on_unlocked:
            self.on_unlocked()

    def _on_close(self):
        self.destroy()


def show_lock_screen(parent, reason: str, on_unlocked=None):
    LockScreen(parent, reason, on_unlocked)