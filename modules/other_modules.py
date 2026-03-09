import customtkinter as ctk
from ui.widgets import ctk_label, ctk_button, ctk_entry, ctk_combo, sep
from config import T
from database.models import (get_customers, save_customer, get_suppliers,
                              save_supplier, get_sales_report, get_users, save_user,
                              get_audit_log, get_settings, set_setting)
from datetime import datetime, timedelta


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOMERS
# ═══════════════════════════════════════════════════════════════════════════════
class Customers(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color=T["bg"], corner_radius=0)
        self.current_user = current_user
        self.selected_id = None
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk_label(hdr, "👥  Clients", size=18, bold=True).pack(side="left")
        ctk_button(hdr, "➕  Nouveau", command=self._new, style="primary", width=120, height=34).pack(side="right")

        bar = ctk.CTkFrame(self, fg_color=T["surface"], corner_radius=10,
                           border_width=1, border_color=T["border"])
        bar.pack(fill="x", padx=24, pady=(0, 12))
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh())
        ctk_entry(inner, placeholder="🔍  Rechercher client…", textvariable=self.search_var, width=280).pack(side="left")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24)
        body.columnconfigure(0, weight=3); body.columnconfigure(1, weight=2); body.rowconfigure(0, weight=1)

        self._build_list(body)
        self._build_form(body)
        self._refresh()

    def _build_list(self, parent):
        card = ctk.CTkFrame(parent, fg_color=T["surface"], corner_radius=16,
                            border_width=1, border_color=T["border"])
        card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        cols = [("Code",80),("Nom",180),("Ville",100),("Téléphone",120),("Solde",90)]
        hdr = ctk.CTkFrame(card, fg_color=T["surface2"], corner_radius=0)
        hdr.pack(fill="x")
        for l,w in cols:
            ctk.CTkLabel(hdr, text=l, font=(T["font"],10,"bold"),
                         text_color=T["text_muted"], width=w, anchor="w").pack(side="left", padx=8, pady=8)
        self.list_sf = ctk.CTkScrollableFrame(card, fg_color="transparent",
                                              scrollbar_button_color=T["surface3"])
        self.list_sf.pack(fill="both", expand=True)

    def _refresh(self, *_):
        for w in self.list_sf.winfo_children(): w.destroy()
        customers = get_customers(search=self.search_var.get())
        for i, c in enumerate(customers):
            bg = T["surface"] if i%2==0 else T["surface2"]
            row = ctk.CTkFrame(self.list_sf, fg_color=bg, corner_radius=0, height=36)
            row.pack(fill="x"); row.pack_propagate(False)
            row.bind("<Button-1>", lambda e, c=c: self._select(c))
            for v, w, col in [
                (c.get("code",""), 80, T["text_muted"]),
                (c["full_name"][:24], 180, T["text"]),
                ((c.get("city") or "")[:12], 100, T["text_dim"]),
                (c.get("phone",""), 120, T["text_dim"]),
                (f"{c.get('balance',0):,.0f}", 90, T["accent"]),
            ]:
                lbl = ctk.CTkLabel(row, text=v, font=(T["font"],10), text_color=col, width=w, anchor="w")
                lbl.pack(side="left", padx=8)
                lbl.bind("<Button-1>", lambda e, c=c: self._select(c))

    def _build_form(self, parent):
        self.form_card = ctk.CTkFrame(parent, fg_color=T["surface"], corner_radius=16,
                                      border_width=1, border_color=T["border"])
        self.form_card.grid(row=0, column=1, sticky="nsew")
        ctk_label(self.form_card, "Sélectionnez un client",
                  color=T["text_muted"]).place(relx=.5, rely=.5, anchor="center")

    def _select(self, c): self.selected_id=c["id"]; self._render_form(c)
    def _new(self): self.selected_id=None; self._render_form({})

    def _render_form(self, c):
        for w in self.form_card.winfo_children(): w.destroy()
        title = "✏️  Modifier" if c.get("id") else "➕  Nouveau client"
        ctk_label(self.form_card, title, size=13, bold=True).pack(anchor="w", padx=16, pady=(14,4))
        sep(self.form_card, pady=(0,8))
        sf = ctk.CTkScrollableFrame(self.form_card, fg_color="transparent",
                                    scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True, padx=12, pady=4)
        self._vars = {}
        for label, key in [("Code","code"),("Nom *","full_name"),("Téléphone","phone"),
                            ("Email","email"),("Ville","city"),("Adresse","address")]:
            ctk_label(sf, label, size=10, color=T["text_muted"]).pack(anchor="w", pady=(6,1))
            var = ctk.StringVar(value=str(c.get(key,"") or ""))
            self._vars[key] = var
            ctk_entry(sf, textvariable=var, width=240).pack(anchor="w")
        sep(sf, pady=(12,0))
        br = ctk.CTkFrame(self.form_card, fg_color="transparent")
        br.pack(fill="x", padx=12, pady=10)
        ctk_button(br, "💾  Enregistrer", command=self._save,
                   style="primary", width=140, height=36).pack(side="left")

    def _save(self):
        data = {k: v.get() for k, v in self._vars.items()}
        save_customer(data, self.selected_id)
        self._refresh()
        for w in self.form_card.winfo_children(): w.destroy()
        ctk_label(self.form_card, "✅  Enregistré", color=T["success"],
                  size=13).place(relx=.5, rely=.5, anchor="center")


# ═══════════════════════════════════════════════════════════════════════════════
# SUPPLIERS
# ═══════════════════════════════════════════════════════════════════════════════
class Suppliers(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color=T["bg"], corner_radius=0)
        self.current_user = current_user
        self.selected_id = None
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20,8))
        ctk_label(hdr, "🏭  Fournisseurs", size=18, bold=True).pack(side="left")
        ctk_button(hdr, "➕  Nouveau", command=self._new, style="primary", width=120, height=34).pack(side="right")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24)
        body.columnconfigure(0, weight=2); body.columnconfigure(1, weight=2); body.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(body, fg_color=T["surface"], corner_radius=16,
                            border_width=1, border_color=T["border"])
        card.grid(row=0, column=0, padx=(0,8), sticky="nsew")
        cols = [("Nom",160),("Téléphone",120),("Email",160)]
        hdr2 = ctk.CTkFrame(card, fg_color=T["surface2"], corner_radius=0)
        hdr2.pack(fill="x")
        for l,w in cols:
            ctk.CTkLabel(hdr2, text=l, font=(T["font"],10,"bold"),
                         text_color=T["text_muted"], width=w, anchor="w").pack(side="left", padx=8, pady=8)
        self.list_sf = ctk.CTkScrollableFrame(card, fg_color="transparent",
                                              scrollbar_button_color=T["surface3"])
        self.list_sf.pack(fill="both", expand=True)

        self.form_card = ctk.CTkFrame(body, fg_color=T["surface"], corner_radius=16,
                                      border_width=1, border_color=T["border"])
        self.form_card.grid(row=0, column=1, sticky="nsew")
        ctk_label(self.form_card, "Sélectionnez un fournisseur",
                  color=T["text_muted"]).place(relx=.5, rely=.5, anchor="center")
        self._refresh()

    def _refresh(self):
        for w in self.list_sf.winfo_children(): w.destroy()
        for i, s in enumerate(get_suppliers()):
            bg = T["surface"] if i%2==0 else T["surface2"]
            row = ctk.CTkFrame(self.list_sf, fg_color=bg, corner_radius=0, height=36)
            row.pack(fill="x"); row.pack_propagate(False)
            row.bind("<Button-1>", lambda e, s=s: self._select(s))
            for v,w,c in [((s.get("name") or "")[:22],160,T["text"]),(s.get("phone") or "",120,T["text_dim"]),((s.get("email") or "")[:22],160,T["text_dim"])]:
                lbl = ctk.CTkLabel(row, text=v, font=(T["font"],10), text_color=c, width=w, anchor="w")
                lbl.pack(side="left", padx=8)
                lbl.bind("<Button-1>", lambda e, s=s: self._select(s))

    def _select(self, s): self.selected_id=s["id"]; self._render_form(s)
    def _new(self): self.selected_id=None; self._render_form({})

    def _render_form(self, s):
        for w in self.form_card.winfo_children(): w.destroy()
        ctk_label(self.form_card, "✏️  Fournisseur", size=13, bold=True).pack(anchor="w", padx=16, pady=(14,4))
        sep(self.form_card, pady=(0,8))
        sf = ctk.CTkScrollableFrame(self.form_card, fg_color="transparent",
                                    scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True, padx=12)
        self._vars = {}
        for label, key in [("Nom *","name"),("Contact","contact"),("Téléphone","phone"),("Email","email"),("Adresse","address")]:
            ctk_label(sf, label, size=10, color=T["text_muted"]).pack(anchor="w", pady=(6,1))
            var = ctk.StringVar(value=str(s.get(key,"") or ""))
            self._vars[key] = var
            ctk_entry(sf, textvariable=var, width=240).pack(anchor="w")
        br = ctk.CTkFrame(self.form_card, fg_color="transparent")
        br.pack(fill="x", padx=12, pady=10)
        ctk_button(br, "💾  Enregistrer", command=self._save, style="primary", width=140, height=36).pack(side="left")

    def _save(self):
        data = {k: v.get() for k, v in self._vars.items()}
        save_supplier(data, self.selected_id)
        self._refresh()


# ═══════════════════════════════════════════════════════════════════════════════
# REPORTS
# ═══════════════════════════════════════════════════════════════════════════════
class Reports(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color=T["bg"], corner_radius=0)
        self.current_user = current_user
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20,8))
        ctk_label(hdr, "📈  Rapports", size=18, bold=True).pack(side="left")

        bar = ctk.CTkFrame(self, fg_color=T["surface"], corner_radius=10,
                           border_width=1, border_color=T["border"])
        bar.pack(fill="x", padx=24, pady=(0,12))
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        today = datetime.now()
        ctk_label(inner, "Du:", size=10, color=T["text_muted"]).pack(side="left")
        self.start_var = ctk.StringVar(value=(today - timedelta(days=30)).strftime("%Y-%m-%d"))
        ctk_entry(inner, textvariable=self.start_var, width=120).pack(side="left", padx=6)
        ctk_label(inner, "Au:", size=10, color=T["text_muted"]).pack(side="left")
        self.end_var = ctk.StringVar(value=today.strftime("%Y-%m-%d"))
        ctk_entry(inner, textvariable=self.end_var, width=120).pack(side="left", padx=6)
        ctk_button(inner, "🔍  Générer", command=self._generate,
                   style="primary", width=110, height=34).pack(side="left", padx=10)

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=24)
        self._generate()

    def _generate(self):
        for w in self.body.winfo_children(): w.destroy()
        sales = get_sales_report(self.start_var.get(), self.end_var.get())
        total = sum(s["total"] for s in sales)

        # Summary cards
        sm = ctk.CTkFrame(self.body, fg_color="transparent")
        sm.pack(fill="x", pady=(0,12))
        for lbl, val, col in [
            ("Total Ventes", f"{total:,.0f} MAD", T["primary"]),
            ("Nb Factures",  str(len(sales)),      T["accent"]),
            ("Moy. Facture", f"{total/len(sales):,.0f} MAD" if sales else "—", T["success"]),
        ]:
            c = ctk.CTkFrame(sm, fg_color=T["surface"], corner_radius=12,
                             border_width=1, border_color=T["border"])
            c.pack(side="left", expand=True, fill="both", padx=6, ipady=10)
            ctk.CTkLabel(c, text=lbl, font=(T["font"],10), text_color=T["text_muted"]).pack(pady=(8,2))
            ctk.CTkLabel(c, text=val, font=(T["font"],18,"bold"), text_color=col).pack()

        # Table
        card = ctk.CTkFrame(self.body, fg_color=T["surface"], corner_radius=16,
                            border_width=1, border_color=T["border"])
        card.pack(fill="both", expand=True)
        cols = [("Facture",100),("Client",160),("Total",100),("Paiement",110),("Date",130),("Statut",80)]
        h = ctk.CTkFrame(card, fg_color=T["surface2"], corner_radius=0)
        h.pack(fill="x")
        for l,w in cols:
            ctk.CTkLabel(h, text=l, font=(T["font"],10,"bold"),
                         text_color=T["text_muted"], width=w, anchor="w").pack(side="left", padx=8, pady=8)
        sf = ctk.CTkScrollableFrame(card, fg_color="transparent",
                                    scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True)
        for i, s in enumerate(sales):
            bg = T["surface"] if i%2==0 else T["surface2"]
            row = ctk.CTkFrame(sf, fg_color=bg, corner_radius=0, height=36)
            row.pack(fill="x"); row.pack_propagate(False)
            for v,w,c in [
                (s["invoice_number"],100,T["text_muted"]),
                ((s.get("full_name") or "—")[:22],160,T["text"]),
                (f"{s['total']:,.0f}",100,T["accent"]),
                (s["payment_method"],110,T["text_dim"]),
                (s["created_at"][:16],130,T["text_dim"]),
                (s.get("status",""),80,T["success"]),
            ]:
                ctk.CTkLabel(row, text=v, font=(T["font"],10), text_color=c, width=w, anchor="w").pack(side="left", padx=8)


# ═══════════════════════════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════════════════════════
class Users(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color=T["bg"], corner_radius=0)
        self.current_user = current_user
        self.selected_id = None
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20,8))
        ctk_label(hdr, "👤  Utilisateurs", size=18, bold=True).pack(side="left")
        ctk_button(hdr, "➕  Nouveau", command=self._new, style="primary", width=120, height=34).pack(side="right")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24)
        body.columnconfigure(0, weight=2); body.columnconfigure(1, weight=2); body.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(body, fg_color=T["surface"], corner_radius=16,
                            border_width=1, border_color=T["border"])
        card.grid(row=0, column=0, padx=(0,8), sticky="nsew")
        cols = [("Identifiant",120),("Nom",160),("Rôle",120),("Statut",80)]
        hdr2 = ctk.CTkFrame(card, fg_color=T["surface2"], corner_radius=0)
        hdr2.pack(fill="x")
        for l,w in cols:
            ctk.CTkLabel(hdr2, text=l, font=(T["font"],10,"bold"),
                         text_color=T["text_muted"], width=w, anchor="w").pack(side="left", padx=8, pady=8)
        self.list_sf = ctk.CTkScrollableFrame(card, fg_color="transparent",
                                              scrollbar_button_color=T["surface3"])
        self.list_sf.pack(fill="both", expand=True)

        self.form_card = ctk.CTkFrame(body, fg_color=T["surface"], corner_radius=16,
                                      border_width=1, border_color=T["border"])
        self.form_card.grid(row=0, column=1, sticky="nsew")
        ctk_label(self.form_card, "Sélectionnez un utilisateur",
                  color=T["text_muted"]).place(relx=.5, rely=.5, anchor="center")
        self._refresh()

    def _refresh(self):
        for w in self.list_sf.winfo_children(): w.destroy()
        for i, u in enumerate(get_users()):
            bg = T["surface"] if i%2==0 else T["surface2"]
            row = ctk.CTkFrame(self.list_sf, fg_color=bg, corner_radius=0, height=36)
            row.pack(fill="x"); row.pack_propagate(False)
            row.bind("<Button-1>", lambda e, u=u: self._select(u))
            for v,w,c in [
                (u["username"],120,T["accent"]),
                (u["full_name"][:20],160,T["text"]),
                (u["role"],120,T["text_dim"]),
                ("✅" if u["active"] else "❌",80,T["success"] if u["active"] else T["danger"]),
            ]:
                lbl = ctk.CTkLabel(row, text=v, font=(T["font"],10), text_color=c, width=w, anchor="w")
                lbl.pack(side="left", padx=8)
                lbl.bind("<Button-1>", lambda e, u=u: self._select(u))

    def _select(self, u): self.selected_id=u["id"]; self._render_form(u)
    def _new(self): self.selected_id=None; self._render_form({})

    def _render_form(self, u):
        for w in self.form_card.winfo_children(): w.destroy()
        ctk_label(self.form_card, "✏️  Utilisateur", size=13, bold=True).pack(anchor="w", padx=16, pady=(14,4))
        sep(self.form_card, pady=(0,8))
        sf = ctk.CTkScrollableFrame(self.form_card, fg_color="transparent",
                                    scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True, padx=12)
        self._vars = {}
        for label, key in [("Nom complet *","full_name"),("Identifiant","username"),("Mot de passe","password")]:
            ctk_label(sf, label, size=10, color=T["text_muted"]).pack(anchor="w", pady=(6,1))
            var = ctk.StringVar(value=str(u.get(key,"") or ""))
            self._vars[key] = var
            show = "*" if key=="password" else None
            e = ctk_entry(sf, textvariable=var, width=240)
            if show: e.configure(show=show)
            e.pack(anchor="w")
        ctk_label(sf, "Rôle", size=10, color=T["text_muted"]).pack(anchor="w", pady=(6,1))
        role_var = ctk.StringVar(value=u.get("role","Vendeur"))
        self._vars["role"] = role_var
        ctk_combo(sf, ["Administrateur","Manager","Vendeur"], variable=role_var, width=240).pack(anchor="w")
        br = ctk.CTkFrame(self.form_card, fg_color="transparent")
        br.pack(fill="x", padx=12, pady=10)
        ctk_button(br, "💾  Enregistrer", command=self._save, style="primary", width=140, height=36).pack(side="left")

    def _save(self):
        data = {k: v.get() for k, v in self._vars.items()}
        data["active"] = 1
        save_user(data, self.selected_id)
        self._refresh()


# ═══════════════════════════════════════════════════════════════════════════════
# SETTINGS + AUDIT LOG
# ═══════════════════════════════════════════════════════════════════════════════
class Settings(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color=T["bg"], corner_radius=0)
        self.current_user = current_user
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20,8))
        ctk_label(hdr, "⚙   Paramètres & Audit", size=18, bold=True).pack(side="left")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24)
        body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2); body.rowconfigure(0, weight=1)

        # Settings panel
        card = ctk.CTkFrame(body, fg_color=T["surface"], corner_radius=16,
                            border_width=1, border_color=T["border"])
        card.grid(row=0, column=0, padx=(0,8), sticky="nsew")
        ctk_label(card, "Configuration", size=13, bold=True).pack(anchor="w", padx=16, pady=(14,4))
        sep(card, pady=(0,10))
        sf = ctk.CTkScrollableFrame(card, fg_color="transparent", scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True, padx=12)
        s = get_settings()
        self._svars = {}
        for label, key, default in [
            ("Nom Société","company_name","Wholesale Optique"),
            ("Téléphone","company_phone",""),
            ("Adresse","company_address",""),
            ("Email","company_email",""),
            ("TVA (%)","tva_rate","20"),
        ]:
            ctk_label(sf, label, size=10, color=T["text_muted"]).pack(anchor="w", pady=(6,1))
            var = ctk.StringVar(value=s.get(key, default))
            self._svars[key] = var
            ctk_entry(sf, textvariable=var, width=220).pack(anchor="w")
        ctk_button(card, "💾  Sauvegarder", command=self._save_settings,
                   style="primary", width=150, height=36).pack(pady=12)

        # Audit log
        acard = ctk.CTkFrame(body, fg_color=T["surface"], corner_radius=16,
                             border_width=1, border_color=T["border"])
        acard.grid(row=0, column=1, sticky="nsew")
        ctk_label(acard, "📋  Journal d'activité", size=13, bold=True).pack(anchor="w", padx=16, pady=(14,4))
        sep(acard, pady=(0,0))
        cols = [("Utilisateur",120),("Action",120),("Module",100),("Détail",180),("Date",130)]
        h = ctk.CTkFrame(acard, fg_color=T["surface2"], corner_radius=0)
        h.pack(fill="x")
        for l,w in cols:
            ctk.CTkLabel(h, text=l, font=(T["font"],10,"bold"),
                         text_color=T["text_muted"], width=w, anchor="w").pack(side="left", padx=8, pady=8)
        asf = ctk.CTkScrollableFrame(acard, fg_color="transparent", scrollbar_button_color=T["surface3"])
        asf.pack(fill="both", expand=True)
        for i, log in enumerate(get_audit_log()):
            bg = T["surface"] if i%2==0 else T["surface2"]
            row = ctk.CTkFrame(asf, fg_color=bg, corner_radius=0, height=34)
            row.pack(fill="x"); row.pack_propagate(False)
            for v,w,c in [
                ((log.get("full_name") or "Sys")[:16], 120, T["text"]),
                (log.get("action","")[:14],            120, T["primary"]),
                (log.get("module","")[:12],            100, T["text_dim"]),
                (log.get("detail","")[:24],            180, T["text_muted"]),
                (log.get("created_at","")[:16],        130, T["text_muted"]),
            ]:
                ctk.CTkLabel(row, text=v, font=(T["font"],9), text_color=c, width=w, anchor="w").pack(side="left", padx=6)

    def _save_settings(self):
        for k, var in self._svars.items():
            set_setting(k, var.get())


# ═══════════════════════════════════════════════════════════════════════════════
# PURCHASES (stub)
# ═══════════════════════════════════════════════════════════════════════════════
class Purchases(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color=T["bg"], corner_radius=0)
        ctk_label(self, "🛒  Module Achats", size=18, bold=True).pack(pady=30)
        ctk_label(self, "Ce module sera disponible dans la prochaine version.",
                  color=T["text_muted"]).pack()