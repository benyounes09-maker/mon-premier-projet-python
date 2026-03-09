import sys, os, traceback, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from config import T, set_theme, DARK, LIGHT, ROLES, NAV_LABELS, APP_NAME, APP_VERSION
from ui.widgets import apply_ctk_theme
from database.models import init_db, authenticate


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════════
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  —  Connexion")
        self.resizable(False, False)
        w, h = 440, 560
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.configure(fg_color=T["bg"])
        self._build()

    def _build(self):
        # ── Header gradient panel ────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=T["primary"], corner_radius=0, height=160)
        hdr.pack(fill="x"); hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="👓", font=("Segoe UI Emoji", 42),
                     text_color="#ffffff").pack(pady=(24, 4))
        ctk.CTkLabel(hdr, text=APP_NAME,
                     font=(T["font"], 20, "bold"), text_color="#ffffff").pack()
        ctk.CTkLabel(hdr, text="Gestion Wholesale Optique",
                     font=(T["font"], 10), text_color="#c7d2fe").pack()

        # ── Form ─────────────────────────────────────────────────────────────
        form = ctk.CTkFrame(self, fg_color=T["surface"], corner_radius=0)
        form.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(form, fg_color="transparent")
        inner.pack(expand=True, fill="both", padx=48, pady=24)

        def field(label, show=None):
            ctk.CTkLabel(inner, text=label, font=(T["font"], 10),
                         text_color=T["text_muted"], anchor="w").pack(anchor="w", pady=(8, 2))
            var = ctk.StringVar()
            e = ctk.CTkEntry(inner, textvariable=var, show=show or "",
                             fg_color=T["input_bg"], border_color=T["border"],
                             text_color=T["text"], placeholder_text_color=T["text_muted"],
                             corner_radius=10, height=44,
                             font=(T["font"], 13))
            e.pack(fill="x")
            return var, e

        self.user_var, u_entry = field("Identifiant")
        self.pass_var, p_entry = field("Mot de passe", "•")
        self.user_var.set("admin")
        p_entry.bind("<Return>", lambda e: self._login())

        self.err_var = ctk.StringVar()
        ctk.CTkLabel(inner, textvariable=self.err_var,
                     font=(T["font"], 10), text_color=T["danger"]).pack(pady=(6, 0))

        ctk.CTkButton(inner, text="Se connecter  →",
                      command=self._login,
                      fg_color=T["primary"], hover_color=T["primary_dk"],
                      text_color="#ffffff",
                      font=(T["font"], 14, "bold"),
                      corner_radius=10, height=46).pack(fill="x", pady=(12, 0))

        # Theme toggle
        toggle_frame = ctk.CTkFrame(inner, fg_color="transparent")
        toggle_frame.pack(fill="x", pady=(16, 0))
        ctk.CTkLabel(toggle_frame, text="Mode sombre",
                     font=(T["font"], 10), text_color=T["text_muted"]).pack(side="left")
        self._dark = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(toggle_frame, text="", variable=self._dark,
                      command=self._toggle_theme,
                      button_color=T["primary"],
                      button_hover_color=T["primary_dk"],
                      progress_color=T["primary"]).pack(side="right")

        # Footer
        ctk.CTkLabel(self, text=f"v{APP_VERSION}  ·  © {APP_NAME}",
                     font=(T["font"], 9), text_color=T["text_muted"],
                     fg_color=T["bg"]).pack(pady=10)

        u_entry.focus()

    def _toggle_theme(self):
        mode = "dark" if self._dark.get() else "light"
        set_theme(mode)
        apply_ctk_theme(mode)
        ctk.set_appearance_mode(mode)

    def _login(self):
        user = authenticate(self.user_var.get().strip(), self.pass_var.get())
        if user:
            self.withdraw()
            MainApp(self, user)
        else:
            self.err_var.set("❌  Identifiants incorrects")
            self.after(3000, lambda: self.err_var.set(""))


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════
class MainApp(ctk.CTkToplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.current_user = current_user
        self.title(f"{APP_NAME}  —  {current_user['full_name']}  [{current_user['role']}]")
        self.configure(fg_color=T["bg"])
        self.state("zoomed")
        self.protocol("WM_DELETE_WINDOW", lambda: (self.destroy(), parent.destroy()))
        self._active_key = None
        self._build()

    def _build(self):
        # ── Sidebar ───────────────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=T["sidebar_w"],
                                    fg_color=T["surface"], corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo = ctk.CTkFrame(self.sidebar, fg_color=T["primary"], height=72, corner_radius=0)
        logo.pack(fill="x"); logo.pack_propagate(False)
        ctk.CTkLabel(logo, text=f"👓  {APP_NAME}",
                     font=(T["font"], 13, "bold"), text_color="#ffffff").place(relx=.5, rely=.5, anchor="center")

        # User badge
        ub = ctk.CTkFrame(self.sidebar, fg_color=T["surface2"], corner_radius=0, height=60)
        ub.pack(fill="x"); ub.pack_propagate(False)
        initials = "".join(w[0].upper() for w in self.current_user["full_name"].split()[:2])
        av = ctk.CTkFrame(ub, width=38, height=38, corner_radius=19, fg_color=T["primary"])
        av.place(x=12, rely=.5, anchor="w")
        ctk.CTkLabel(av, text=initials, font=(T["font"], 12, "bold"),
                     text_color="#fff").place(relx=.5, rely=.5, anchor="center")
        ctk.CTkLabel(ub, text=self.current_user["full_name"].split()[0],
                     font=(T["font"], 11, "bold"), text_color=T["text"]).place(x=58, y=10)
        ctk.CTkLabel(ub, text=self.current_user["role"],
                     font=(T["font"], 9), text_color=T["text_muted"]).place(x=58, y=30)

        # Separator
        ctk.CTkFrame(self.sidebar, fg_color=T["border"], height=1, corner_radius=0).pack(fill="x")

        # Nav buttons
        allowed = ROLES.get(self.current_user["role"], [])
        self._nav_btns = {}
        nav_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent",
                                           scrollbar_button_color=T["surface3"])
        nav_frame.pack(fill="both", expand=True, pady=8)

        for key, label, _ in [
            ("dashboard",  "📊  Dashboard",      ""),
            ("pos",        "💳  Caisse POS",     ""),
            ("purchases",  "🛒  Achats",         ""),
            ("inventory",  "📦  Inventaire",     ""),
            ("customers",  "👥  Clients",        ""),
            ("suppliers",  "🏭  Fournisseurs",   ""),
            ("reports",    "📈  Rapports",       ""),
            ("users",      "👤  Utilisateurs",   ""),
            ("settings",   "⚙   Paramètres",     ""),
        ]:
            if key not in allowed:
                continue
            btn = ctk.CTkButton(nav_frame, text=f"  {label}",
                                fg_color="transparent",
                                hover_color=T["primary_glow"],
                                text_color=T["text_muted"],
                                font=(T["font"], 11),
                                anchor="w", height=40, corner_radius=8,
                                command=lambda k=key: self._navigate(k))
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_btns[key] = btn

        # Bottom: alerts badge + logout
        ctk.CTkFrame(self.sidebar, fg_color=T["border"], height=1, corner_radius=0).pack(fill="x", side="bottom")

        logout_btn = ctk.CTkButton(self.sidebar, text="🚪  Déconnexion",
                                   fg_color="transparent", hover_color="#5c1a1a",
                                   text_color=T["danger"], font=(T["font"], 10),
                                   anchor="w", height=40, corner_radius=0,
                                   command=self._logout)
        logout_btn.pack(side="bottom", fill="x", padx=8, pady=4)

        # ── Content area ──────────────────────────────────────────────────────
        self.content = ctk.CTkFrame(self, fg_color=T["bg"], corner_radius=0)
        self.content.pack(side="right", fill="both", expand=True)

        # Navigate to first allowed module — after() pour laisser CTk finir le layout
        first = next((k for k, _, __ in [
            ("dashboard","",""), ("pos","",""), ("purchases","",""),
            ("inventory","",""), ("customers","",""), ("suppliers","",""),
            ("reports","",""), ("users","",""), ("settings","",""),
        ] if k in allowed), None)
        if first:
            self.after(150, lambda: self._navigate(first))

    def _navigate(self, key):
        # Update nav styles
        for k, btn in self._nav_btns.items():
            if k == key:
                btn.configure(fg_color=T["primary_glow"], text_color=T["primary"])
            else:
                btn.configure(fg_color="transparent", text_color=T["text_muted"])

        if self._active_key == key:
            return
        self._active_key = key

        for w in self.content.winfo_children():
            w.destroy()

        Module = self._get_module(key)
        if Module:
            try:
                Module(self.content, self.current_user).pack(fill="both", expand=True)
            except Exception as e:
                import traceback as _tb, customtkinter as _ctk
                _msg = "Erreur module [" + key + "] : " + str(e)
                _ctk.CTkLabel(self.content, text=_msg, font=(T["font"], 11),
                    text_color=T["danger"], wraplength=800).pack(padx=24, pady=24, anchor="nw")

    def _get_module(self, key):
        if key == "dashboard":
            from modules.dashboard import Dashboard; return Dashboard
        if key == "pos":
            from modules.pos import POS; return POS
        if key == "inventory":
            from modules.inventory import Inventory; return Inventory
        if key == "customers":
            from modules.other_modules import Customers; return Customers
        if key == "suppliers":
            from modules.other_modules import Suppliers; return Suppliers
        if key == "reports":
            from modules.other_modules import Reports; return Reports
        if key == "users":
            from modules.other_modules import Users; return Users
        if key == "settings":
            from modules.settings import Settings; return Settings
        if key == "purchases":
            from modules.purchases import Purchases; return Purchases
        return None

    def _logout(self):
        if ctk.messagebox if hasattr(ctk, "messagebox") else True:
            self.destroy()
            self.master.deiconify()


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    _log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "optigest_v3.log")

    def _log(msg):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(_log_path, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {msg}\n")
        except Exception:
            pass

    try:
        _log("=== Démarrage OptiGest Pro v3 ===")

        from database.models import get_settings as _gs
        init_db()
        _log("DB initialisée")
        _saved_theme = _gs().get("theme", "dark")
        apply_ctk_theme(_saved_theme)
        set_theme(_saved_theme)

        app = LoginWindow()
        _log("LoginWindow créée")

        # Vérification licence
        from license import check_license, show_lock_screen
        lic_ok, reason = check_license()
        _log(f"Licence : ok={lic_ok}  reason={reason}")

        if not lic_ok:
            app.withdraw()
            app.update()
            def _on_unlocked():
                app.deiconify()
            show_lock_screen(app, reason, on_unlocked=_on_unlocked)

        app.mainloop()
        _log("mainloop terminé")

    except Exception:
        tb = traceback.format_exc()
        _log("ERREUR FATALE:\n" + tb)
        try:
            import tkinter.messagebox as mb
            mb.showerror("Erreur", f"OptiGest Pro v3 n'a pas pu démarrer.\n\n{tb[:600]}")
        except Exception:
            pass
        raise