import customtkinter as ctk
from ui.widgets import ctk_label, ctk_button, ctk_entry, ctk_combo, sep
from config import T, LENS_CATEGORIES, LENS_TYPES, LENS_INDICES, COATINGS
from database.models import get_products, save_product, get_suppliers


class Inventory(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color=T["bg"], corner_radius=0)
        self.current_user = current_user
        self.selected_id = None
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk_label(hdr, "📦  Inventaire Produits", size=18, bold=True).pack(side="left")
        ctk_button(hdr, "➕  Nouveau produit", command=self._new_product,
                   style="primary", width=150, height=34).pack(side="right")

        # Search bar
        bar = ctk.CTkFrame(self, fg_color=T["surface"], corner_radius=12,
                           border_width=1, border_color=T["border"])
        bar.pack(fill="x", padx=24, pady=(0, 12))
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)
        ctk_label(inner, "🔍", size=14).pack(side="left", padx=(0, 6))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_list())
        ctk_entry(inner, placeholder="Rechercher produit, référence, marque…",
                  textvariable=self.search_var, width=300).pack(side="left")

        self.cat_filter = ctk.StringVar(value="Tous")
        cats = ["Tous"] + LENS_CATEGORIES
        cb = ctk_combo(inner, cats, variable=self.cat_filter, width=160,
                       command=lambda _: self._refresh_list())
        cb.pack(side="left", padx=10)

        ctk_button(inner, "🔄 Actualiser", command=self._refresh_list,
                   style="ghost", width=110, height=32).pack(side="right")

        # Body: list + form side by side
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        self._build_list(body)
        self._build_form(body)
        self._refresh_list()

    def _build_list(self, parent):
        card = ctk.CTkFrame(parent, fg_color=T["surface"], corner_radius=16,
                            border_width=1, border_color=T["border"])
        card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        # Column headers
        cols = [("Réf.", 70), ("Nom", 200), ("Catégorie", 100),
                ("Stock", 60), ("Prix Vente", 90), ("Statut", 70)]
        hdr = ctk.CTkFrame(card, fg_color=T["surface2"], corner_radius=0)
        hdr.pack(fill="x")
        for lbl, w in cols:
            ctk.CTkLabel(hdr, text=lbl, font=(T["font"], 10, "bold"),
                         text_color=T["text_muted"], width=w, anchor="w").pack(
                side="left", padx=8, pady=8)

        self.list_frame = ctk.CTkScrollableFrame(card, fg_color="transparent",
                                                 scrollbar_button_color=T["surface3"])
        self.list_frame.pack(fill="both", expand=True)

    def _refresh_list(self, *_):
        for w in self.list_frame.winfo_children():
            w.destroy()
        search = self.search_var.get()
        cat = self.cat_filter.get()
        products = get_products(search=search)
        if cat != "Tous":
            products = [p for p in products if p["category"] == cat]

        if not products:
            ctk_label(self.list_frame, "Aucun produit trouvé",
                      color=T["text_muted"]).pack(pady=40)
            return

        for i, p in enumerate(products):
            bg = T["surface"] if i % 2 == 0 else T["surface2"]
            row = ctk.CTkFrame(self.list_frame, fg_color=bg, corner_radius=0, height=38)
            row.pack(fill="x")
            row.pack_propagate(False)
            row.bind("<Button-1>", lambda e, p=p: self._select(p))

            stock_color = T["danger"] if p["stock"] <= p["min_stock"] else T["success"]
            vals = [
                (p.get("reference","")[:8], 70, T["text_muted"]),
                (p["name"][:28],            200, T["text"]),
                (p.get("category","")[:12], 100, T["text_dim"]),
                (str(p["stock"]),           60,  stock_color),
                (f"{p['sale_price']:,.0f}", 90,  T["accent"]),
                ("✅ Actif" if p["active"] else "❌ Off", 70, T["text_muted"]),
            ]
            for v, w, c in vals:
                lbl = ctk.CTkLabel(row, text=v, font=(T["font"], 10),
                                   text_color=c, width=w, anchor="w")
                lbl.pack(side="left", padx=8)
                lbl.bind("<Button-1>", lambda e, p=p: self._select(p))

    def _build_form(self, parent):
        self.form_card = ctk.CTkFrame(parent, fg_color=T["surface"], corner_radius=16,
                                      border_width=1, border_color=T["border"])
        self.form_card.grid(row=0, column=1, sticky="nsew")
        self._show_empty_form()

    def _show_empty_form(self):
        for w in self.form_card.winfo_children():
            w.destroy()
        ctk_label(self.form_card, "Sélectionnez un produit\nou créez-en un nouveau",
                  size=12, color=T["text_muted"]).place(relx=.5, rely=.5, anchor="center")

    def _select(self, p):
        self.selected_id = p["id"]
        self._render_form(p)

    def _new_product(self):
        self.selected_id = None
        self._render_form({})

    def _render_form(self, p):
        for w in self.form_card.winfo_children():
            w.destroy()

        title = "✏️  Modifier produit" if p.get("id") else "➕  Nouveau produit"
        ctk_label(self.form_card, title, size=13, bold=True).pack(anchor="w", padx=16, pady=(14, 4))
        sep(self.form_card, pady=(0, 8))

        sf = ctk.CTkScrollableFrame(self.form_card, fg_color="transparent",
                                    scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True, padx=12, pady=4)

        self._vars = {}

        def field(label, key, default="", combo_vals=None, width=240):
            ctk_label(sf, label, size=10, color=T["text_muted"]).pack(anchor="w", pady=(6, 1))
            var = ctk.StringVar(value=str(p.get(key, default) or ""))
            self._vars[key] = var
            if combo_vals:
                w = ctk_combo(sf, combo_vals, variable=var, width=width)
            else:
                w = ctk_entry(sf, textvariable=var, width=width)
            w.pack(anchor="w")

        field("Référence",      "reference")
        field("Nom produit *",  "name")
        field("Catégorie",      "category", combo_vals=LENS_CATEGORIES)
        field("Type verre",     "lens_type", combo_vals=LENS_TYPES)
        field("Indice",         "index_value", combo_vals=LENS_INDICES)
        field("Traitement",     "coating", combo_vals=COATINGS)
        field("Marque",         "brand")

        # Prices row
        ctk_label(sf, "Prix Achat / Vente", size=10, color=T["text_muted"]).pack(anchor="w", pady=(6, 1))
        pr = ctk.CTkFrame(sf, fg_color="transparent")
        pr.pack(anchor="w")
        for k, ph in [("purchase_price","Achat"), ("sale_price","Vente")]:
            var = ctk.StringVar(value=str(p.get(k, 0) or 0))
            self._vars[k] = var
            ctk_entry(pr, placeholder=ph, textvariable=var, width=110).pack(side="left", padx=(0, 6))

        # Stock row
        ctk_label(sf, "Stock / Stock min", size=10, color=T["text_muted"]).pack(anchor="w", pady=(6, 1))
        st = ctk.CTkFrame(sf, fg_color="transparent")
        st.pack(anchor="w")
        for k, ph in [("stock","Stock"), ("min_stock","Min")]:
            var = ctk.StringVar(value=str(p.get(k, 0) or 0))
            self._vars[k] = var
            ctk_entry(st, placeholder=ph, textvariable=var, width=110).pack(side="left", padx=(0, 6))

        sep(sf, pady=(12, 0))

        # Buttons
        btn_row = ctk.CTkFrame(self.form_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=10)
        ctk_button(btn_row, "💾  Enregistrer", command=self._save,
                   style="primary", width=140, height=36).pack(side="left")
        if p.get("id"):
            ctk_button(btn_row, "🗑 Supprimer",
                       command=lambda: self._delete(p["id"]),
                       style="danger", width=110, height=36).pack(side="right")

    def _save(self):
        data = {k: v.get() for k, v in self._vars.items()}
        for f in ["purchase_price","sale_price","stock","min_stock"]:
            try: data[f] = float(data[f])
            except: data[f] = 0
        data["active"] = 1
        save_product(data, self.selected_id)
        self._refresh_list()
        self._show_empty_form()

    def _delete(self, pid):
        save_product({"active": 0, **{k: "" for k in ["reference","name"]}}, pid)
        self._refresh_list()
        self._show_empty_form()
