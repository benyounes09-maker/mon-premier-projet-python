import customtkinter as ctk
from ui.widgets import ctk_label, ctk_button, ctk_entry, ctk_combo, sep
from config import T, LENS_CATEGORIES, LENS_TYPES, LENS_INDICES, COATINGS, PAYMENT_METHODS
from database.models import get_products, get_customers, create_sale


class POS(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color=T["bg"], corner_radius=0)
        self.current_user = current_user
        self.cart = []
        self.customer_id = None
        self._all_products = get_products()
        self._found_product = None
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk_label(hdr, "💳  Caisse POS", size=18, bold=True).pack(side="left")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        self._build_form(body)
        self._build_cart(body)

    def _build_form(self, parent):
        card = ctk.CTkFrame(parent, fg_color=T["surface"], corner_radius=16,
                            border_width=1, border_color=T["border"])
        card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        ctk_label(card, "📋  Sélection produit", size=13, bold=True).pack(
            anchor="w", padx=16, pady=(14, 4))
        sep(card, pady=(0, 8))

        sf = ctk.CTkScrollableFrame(card, fg_color="transparent",
                                     scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True, padx=14, pady=4)

        self.f_cat    = ctk.StringVar(value=LENS_CATEGORIES[0])
        self.f_type   = ctk.StringVar(value=LENS_TYPES[0])
        self.f_indice = ctk.StringVar(value=LENS_INDICES[0])
        self.f_coat   = ctk.StringVar(value=COATINGS[0])
        brands = sorted(set(p["brand"] for p in self._all_products if p.get("brand")))
        self.f_brand  = ctk.StringVar(value=brands[0] if brands else "")
        self.f_qty    = ctk.StringVar(value="1")
        self.f_disc_type = ctk.StringVar(value="%")
        self.f_disc_val  = ctk.StringVar(value="0")

        def lbl(text):
            ctk_label(sf, text, size=10, color=T["text_muted"]).pack(anchor="w", pady=(8, 2))

        def make_cb(label, values, var):
            lbl(label)
            cb = ctk_combo(sf, values, variable=var, width=320)
            cb.pack(anchor="w")
            cb.configure(command=lambda _: self._update_product_label())

        make_cb("Catégorie",   LENS_CATEGORIES, self.f_cat)
        make_cb("Type verre",  LENS_TYPES,       self.f_type)
        make_cb("Indice",      LENS_INDICES,      self.f_indice)
        make_cb("Traitement",  COATINGS,          self.f_coat)
        make_cb("Marque",      brands,            self.f_brand)

        sep(sf, pady=(12, 8))
        self.found_label = ctk.CTkLabel(sf, text="— Aucun produit sélectionné —",
                                         font=(T["font"], 11, "bold"),
                                         text_color=T["text_muted"])
        self.found_label.pack(anchor="w")
        self.price_label = ctk.CTkLabel(sf, text="", font=(T["font"], 13, "bold"),
                                         text_color=T["accent"])
        self.price_label.pack(anchor="w")
        self.stock_label = ctk.CTkLabel(sf, text="", font=(T["font"], 10),
                                         text_color=T["text_muted"])
        self.stock_label.pack(anchor="w")

        sep(sf, pady=(10, 8))
        lbl("Quantité")
        qty_row = ctk.CTkFrame(sf, fg_color="transparent")
        qty_row.pack(anchor="w")
        ctk.CTkButton(qty_row, text="−", width=32, height=32,
                      fg_color=T["surface3"], text_color=T["text"],
                      command=lambda: self.f_qty.set(str(max(1, int(self.f_qty.get() or 1) - 1))),
                      corner_radius=8, font=(T["font"], 14, "bold")).pack(side="left")
        ctk_entry(qty_row, textvariable=self.f_qty, width=60).pack(side="left", padx=6)
        ctk.CTkButton(qty_row, text="+", width=32, height=32,
                      fg_color=T["primary"], text_color="#fff",
                      command=lambda: self.f_qty.set(str(int(self.f_qty.get() or 1) + 1)),
                      corner_radius=8, font=(T["font"], 14, "bold")).pack(side="left")

        sep(sf, pady=(10, 8))
        lbl("Réduction")
        disc_row = ctk.CTkFrame(sf, fg_color="transparent")
        disc_row.pack(anchor="w")
        ctk_combo(disc_row, ["%", "MAD"], variable=self.f_disc_type, width=80).pack(side="left")
        ctk_entry(disc_row, textvariable=self.f_disc_val,
                  placeholder="0", width=100).pack(side="left", padx=6)

        sep(sf, pady=(12, 8))
        ctk_button(sf, "➕  Ajouter au panier",
                   command=self._add_to_cart,
                   style="primary", width=320, height=42).pack(anchor="w")

    def _update_product_label(self):
        candidates = [p for p in self._all_products if p.get("active", 1)]
        cat = self.f_cat.get()
        brand = self.f_brand.get()
        indice = self.f_indice.get()
        ptype = self.f_type.get()
        coat = self.f_coat.get()

        if cat:   candidates = [p for p in candidates if p.get("category") == cat]
        if brand: candidates = [p for p in candidates if p.get("brand") == brand]
        if indice: candidates = [p for p in candidates if p.get("index_value") == indice]
        if ptype: candidates = [p for p in candidates if p.get("lens_type") == ptype]
        if coat:  candidates = [p for p in candidates if p.get("coating") == coat]

        if candidates:
            p = candidates[0]
            self._found_product = p
            sc = T["success"] if p["stock"] > 0 else T["danger"]
            self.found_label.configure(text=p["name"][:40], text_color=sc)
            self.price_label.configure(text=f"{p['sale_price']:,.2f} MAD")
            stk_c = T["danger"] if p["stock"] <= p["min_stock"] else T["success"]
            self.stock_label.configure(text=f"Stock : {p['stock']} u.", text_color=stk_c)
        else:
            self._found_product = None
            self.found_label.configure(text="— Aucun produit correspondant —",
                                        text_color=T["text_muted"])
            self.price_label.configure(text="")
            self.stock_label.configure(text="")

    def _add_to_cart(self):
        p = self._found_product
        if not p:
            return
        try:
            qty = max(1, int(self.f_qty.get() or 1))
        except ValueError:
            qty = 1
        try:
            disc_val = float(self.f_disc_val.get() or 0)
        except ValueError:
            disc_val = 0

        if self.f_disc_type.get() == "%":
            disc_pct = min(disc_val, 100)
        else:
            disc_pct = (disc_val / p["sale_price"] * 100) if p["sale_price"] > 0 else 0
            disc_pct = min(disc_pct, 100)

        for item in self.cart:
            if item["product"]["id"] == p["id"] and item["disc"] == disc_pct:
                item["qty"] += qty
                self._render_cart()
                self.f_qty.set("1"); self.f_disc_val.set("0")
                return

        self.cart.append({"product": p, "qty": qty, "price": p["sale_price"], "disc": disc_pct})
        self._render_cart()
        self.f_qty.set("1"); self.f_disc_val.set("0")

    def _build_cart(self, parent):
        self.cart_frame = ctk.CTkFrame(parent, fg_color=T["surface"], corner_radius=16,
                                       border_width=1, border_color=T["border"])
        self.cart_frame.grid(row=0, column=1, sticky="nsew")
        self._render_cart()

    def _render_cart(self):
        for w in self.cart_frame.winfo_children():
            w.destroy()

        ctk_label(self.cart_frame, "🛒  Panier", size=13, bold=True).pack(
            anchor="w", padx=16, pady=(14, 4))
        sep(self.cart_frame, pady=(0, 4))

        cr = ctk.CTkFrame(self.cart_frame, fg_color="transparent")
        cr.pack(fill="x", padx=12, pady=4)
        ctk_label(cr, "Client:", size=10, color=T["text_muted"]).pack(side="left")
        customers = get_customers()
        cust_names = ["— Comptant —"] + [c["full_name"] for c in customers]
        self._cust_map = {c["full_name"]: c["id"] for c in customers}
        self.cust_var = ctk.StringVar(value="— Comptant —")
        ctk_combo(cr, cust_names, variable=self.cust_var, width=170).pack(side="left", padx=6)

        items_frame = ctk.CTkScrollableFrame(self.cart_frame, fg_color="transparent",
                                              height=280, scrollbar_button_color=T["surface3"])
        items_frame.pack(fill="x", padx=8, pady=4)

        if not self.cart:
            ctk_label(items_frame, "Panier vide\nSélectionnez un produit",
                      color=T["text_muted"], size=11).pack(pady=30)
        else:
            for item in self.cart:
                self._cart_row(items_frame, item)

        sep(self.cart_frame, pady=(4, 0))

        total = sum(it["qty"] * it["price"] * (1 - it["disc"] / 100) for it in self.cart)
        ctk.CTkLabel(self.cart_frame, text=f"Total : {total:,.2f} MAD",
                     font=(T["font"], 16, "bold"), text_color=T["accent"]).pack(pady=8)

        pm = ctk.CTkFrame(self.cart_frame, fg_color="transparent")
        pm.pack(fill="x", padx=12, pady=(0, 6))
        ctk_label(pm, "Paiement:", size=10, color=T["text_muted"]).pack(side="left")
        self.pmt_var = ctk.StringVar(value="Espèces")
        ctk_combo(pm, PAYMENT_METHODS, variable=self.pmt_var, width=150).pack(side="left", padx=6)

        br = ctk.CTkFrame(self.cart_frame, fg_color="transparent")
        br.pack(fill="x", padx=12, pady=8)
        ctk_button(br, "🗑 Vider", command=self._clear_cart,
                   style="ghost", width=80, height=36).pack(side="left")
        ctk_button(br, "✅  Valider la vente", command=self._validate,
                   style="primary" if self.cart else "ghost",
                   width=170, height=40).pack(side="right")

    def _cart_row(self, parent, item):
        p = item["product"]
        row = ctk.CTkFrame(parent, fg_color=T["surface2"], corner_radius=8)
        row.pack(fill="x", pady=3)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=8, pady=6)
        ctk.CTkLabel(left, text=p["name"][:22], font=(T["font"], 10, "bold"),
                     text_color=T["text"], anchor="w").pack(anchor="w")
        disc_txt = f"  −{item['disc']:.0f}%" if item["disc"] > 0 else ""
        ctk.CTkLabel(left, text=f"{item['price']:,.0f} × {item['qty']}{disc_txt}",
                     font=(T["font"], 9), text_color=T["text_muted"], anchor="w").pack(anchor="w")

        total_line = item["qty"] * item["price"] * (1 - item["disc"] / 100)
        ctk.CTkLabel(row, text=f"{total_line:,.0f}",
                     font=(T["font"], 11, "bold"), text_color=T["primary"],
                     width=70, anchor="e").pack(side="right", padx=4)

        ctrl = ctk.CTkFrame(row, fg_color="transparent")
        ctrl.pack(side="right")
        ctk.CTkButton(ctrl, text="✕", width=24, height=24,
                      fg_color=T["danger"], text_color="#fff",
                      command=lambda i=item: self._remove_item(i),
                      corner_radius=6, font=(T["font"], 10)).pack(side="left", padx=(0, 4))
        ctk.CTkButton(ctrl, text="−", width=26, height=26,
                      fg_color=T["surface3"], text_color=T["text"],
                      command=lambda i=item: self._qty(i, -1),
                      corner_radius=6, font=(T["font"], 12, "bold")).pack(side="left")
        ctk.CTkLabel(ctrl, text=str(item["qty"]), width=28,
                     font=(T["font"], 11, "bold"), text_color=T["text"]).pack(side="left")
        ctk.CTkButton(ctrl, text="+", width=26, height=26,
                      fg_color=T["primary"], text_color="#fff",
                      command=lambda i=item: self._qty(i, +1),
                      corner_radius=6, font=(T["font"], 12, "bold")).pack(side="left")

    def _qty(self, item, delta):
        item["qty"] = max(1, item["qty"] + delta)
        self._render_cart()

    def _remove_item(self, item):
        self.cart.remove(item)
        self._render_cart()

    def _clear_cart(self):
        self.cart.clear()
        self._render_cart()

    def _validate(self):
        if not self.cart:
            return
        cust_name = self.cust_var.get()
        cust_id = self._cust_map.get(cust_name)
        items = [{"product_id": it["product"]["id"],
                  "qty": it["qty"], "price": it["price"],
                  "disc": it["disc"]} for it in self.cart]
        inv = create_sale(cust_id, items, self.pmt_var.get(), self.current_user["id"])
        self.cart.clear()
        self._render_cart()
        pop = ctk.CTkToplevel(self)
        pop.title("Vente validée")
        pop.geometry("320x180")
        pop.grab_set()
        ctk.CTkLabel(pop, text="✅  Vente enregistrée",
                     font=(T["font"], 15, "bold"), text_color=T["success"]).pack(pady=(24, 8))
        ctk.CTkLabel(pop, text=f"Facture : {inv}",
                     font=(T["font"], 12), text_color=T["text"]).pack()
        ctk_button(pop, "Fermer", command=pop.destroy,
                   style="primary", width=120, height=36).pack(pady=16)
