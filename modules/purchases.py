"""
modules/purchases.py — Module Achats OptiGest Pro v3
=====================================================
Flux :
  Brouillon → Commandé → Reçu (stock mis à jour)

Onglets :
  1. Bons de commande  — liste + création
  2. Réception         — valider réception + mise à jour stock
  3. Statistiques      — KPIs achats + top fournisseurs
"""

import customtkinter as ctk
from ui.widgets import ctk_label, ctk_button, ctk_entry, ctk_combo, sep
from config import T
from database.models import (get_purchases, get_purchase, create_purchase,
                              receive_purchase, update_purchase_status,
                              get_purchase_stats, get_suppliers, get_products)
from datetime import datetime
import os, tempfile


# ── Couleurs statut ──────────────────────────────────────────────────────────
STATUS_COLOR = {
    "draft":    "#6b7280",
    "ordered":  "#f59e0b",
    "received": "#22c55e",
}
STATUS_LABEL = {
    "draft":    "Brouillon",
    "ordered":  "Commandé",
    "received": "Reçu",
}


class Purchases(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color=T["bg"], corner_radius=0)
        self.current_user = current_user
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk_label(hdr, "🛒  Module Achats", size=18, bold=True).pack(side="left")

        self.tabs = ctk.CTkTabview(self,
                                   fg_color=T["surface"],
                                   segmented_button_fg_color=T["surface2"],
                                   segmented_button_selected_color=T["primary"],
                                   segmented_button_selected_hover_color=T["primary_dk"],
                                   segmented_button_unselected_color=T["surface2"],
                                   segmented_button_unselected_hover_color=T["surface3"],
                                   text_color=T["text"],
                                   border_color=T["border"], border_width=1,
                                   corner_radius=16)
        self.tabs.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        for t in ["📋  Bons de commande", "📦  Réception", "📊  Statistiques"]:
            self.tabs.add(t)

        self._build_bons()
        self._build_reception()
        self._build_stats()

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 1 — BONS DE COMMANDE
    # ══════════════════════════════════════════════════════════════════════════
    def _build_bons(self):
        tab = self.tabs.tab("📋  Bons de commande")
        tab.columnconfigure(0, weight=2)
        tab.columnconfigure(1, weight=3)
        tab.rowconfigure(0, weight=1)

        # ── Liste gauche ──────────────────────────────────────────────────────
        left = ctk.CTkFrame(tab, fg_color=T["surface2"], corner_radius=14,
                            border_width=1, border_color=T["border"])
        left.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        # Toolbar
        tb = ctk.CTkFrame(left, fg_color="transparent")
        tb.pack(fill="x", padx=10, pady=8)
        ctk_button(tb, "➕  Nouveau BC", command=self._new_bc,
                   style="primary", width=130, height=32).pack(side="left")
        self.bc_filter_var = ctk.StringVar(value="Tous")
        ctk_combo(tb, ["Tous", "Brouillon", "Commandé", "Reçu"],
                  variable=self.bc_filter_var, width=120,
                  command=lambda _: self._refresh_bons()).pack(side="right")

        # Headers
        hdr = ctk.CTkFrame(left, fg_color=T["surface3"], corner_radius=0)
        hdr.pack(fill="x")
        for lbl, w in [("Référence", 90), ("Fournisseur", 140), ("Total", 90), ("Statut", 80)]:
            ctk.CTkLabel(hdr, text=lbl, font=(T["font"], 10, "bold"),
                         text_color=T["text_muted"], width=w, anchor="w").pack(
                side="left", padx=8, pady=6)

        self.bons_sf = ctk.CTkScrollableFrame(left, fg_color="transparent",
                                               scrollbar_button_color=T["surface3"])
        self.bons_sf.pack(fill="both", expand=True)

        # ── Détail droit ──────────────────────────────────────────────────────
        self.bc_detail = ctk.CTkFrame(tab, fg_color=T["surface2"], corner_radius=14,
                                       border_width=1, border_color=T["border"])
        self.bc_detail.grid(row=0, column=1, sticky="nsew")
        self._show_bc_form_empty()
        self._refresh_bons()

    def _refresh_bons(self, *_):
        for w in self.bons_sf.winfo_children():
            w.destroy()
        f = self.bc_filter_var.get()
        status_map = {"Brouillon": "draft", "Commandé": "ordered", "Reçu": "received"}
        purchases = get_purchases(status=status_map.get(f))
        if not purchases:
            ctk_label(self.bons_sf, "Aucun bon de commande",
                      color=T["text_muted"]).pack(pady=30)
            return
        for i, p in enumerate(purchases):
            bg = T["surface"] if i % 2 == 0 else T["surface3"]
            row = ctk.CTkFrame(self.bons_sf, fg_color=bg, corner_radius=0, height=38)
            row.pack(fill="x"); row.pack_propagate(False)
            row.bind("<Button-1>", lambda e, p=p: self._show_bc_detail(p))
            sc = STATUS_COLOR.get(p["status"], T["text_muted"])
            for v, w, c in [
                (p["ref"],                          90,  T["accent"]),
                ((p.get("supplier_name") or "")[:18], 140, T["text"]),
                (f"{p['total']:,.0f} MAD",          90,  T["text"]),
                (STATUS_LABEL.get(p["status"], p["status"]), 80, sc),
            ]:
                lbl = ctk.CTkLabel(row, text=v, font=(T["font"], 10),
                                   text_color=c, width=w, anchor="w")
                lbl.pack(side="left", padx=8)
                lbl.bind("<Button-1>", lambda e, p=p: self._show_bc_detail(p))

    def _show_bc_form_empty(self):
        for w in self.bc_detail.winfo_children():
            w.destroy()
        ctk_label(self.bc_detail,
                  "Sélectionnez un BC\nou créez-en un nouveau",
                  size=12, color=T["text_muted"]).place(relx=.5, rely=.5, anchor="center")

    def _new_bc(self):
        for w in self.bc_detail.winfo_children():
            w.destroy()
        self._render_bc_form({})

    def _show_bc_detail(self, p):
        for w in self.bc_detail.winfo_children():
            w.destroy()
        purchase, items = get_purchase(p["id"])
        if not purchase:
            return
        self._render_bc_view(purchase, items)

    def _render_bc_form(self, p):
        """Formulaire création nouveau BC."""
        inner = ctk.CTkScrollableFrame(self.bc_detail, fg_color="transparent",
                                        scrollbar_button_color=T["surface3"])
        inner.pack(fill="both", expand=True, padx=12, pady=8)

        ctk_label(inner, "➕  Nouveau Bon de Commande", size=13, bold=True).pack(anchor="w", pady=(4, 8))
        sep(inner, pady=(0, 8))

        # Fournisseur
        ctk_label(inner, "Fournisseur *", size=10, color=T["text_muted"]).pack(anchor="w", pady=(0, 2))
        suppliers = get_suppliers()
        sup_names = [s["name"] for s in suppliers]
        self._sup_map = {s["name"]: s["id"] for s in suppliers}
        self._sup_var = ctk.StringVar(value=sup_names[0] if sup_names else "")
        ctk_combo(inner, sup_names, variable=self._sup_var, width=280).pack(anchor="w")

        # Notes
        ctk_label(inner, "Notes / référence interne", size=10, color=T["text_muted"]).pack(anchor="w", pady=(8, 2))
        self._notes_var = ctk.StringVar()
        ctk_entry(inner, textvariable=self._notes_var,
                  placeholder="Optionnel", width=280).pack(anchor="w")

        # Lignes produits
        sep(inner, pady=(12, 8))
        ctk_label(inner, "Produits à commander", size=11, bold=True).pack(anchor="w", pady=(0, 8))

        self._bc_lines = []  # [{"product_id", "qty_var", "price_var", "frame"}]
        self._lines_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self._lines_frame.pack(fill="x")

        ctk_button(inner, "➕  Ajouter un produit",
                   command=self._add_bc_line,
                   style="ghost", width=160, height=32).pack(anchor="w", pady=(8, 0))

        # Ajouter une ligne par défaut
        self._add_bc_line()

        sep(inner, pady=(12, 8))
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x")
        ctk_button(btn_row, "💾  Enregistrer brouillon",
                   command=lambda: self._save_bc("draft"),
                   style="ghost", width=170, height=36).pack(side="left")
        ctk_button(btn_row, "📤  Commander",
                   command=lambda: self._save_bc("ordered"),
                   style="primary", width=130, height=36).pack(side="right")

    def _add_bc_line(self):
        all_products = get_products()
        # Groupe par marque
        by_brand = {}
        for p in all_products:
            brand = p.get("brand") or "Autre"
            by_brand.setdefault(brand, []).append(p)
        brands = sorted(by_brand.keys())

        f = ctk.CTkFrame(self._lines_frame, fg_color=T["surface3"],
                         corner_radius=8, border_width=1, border_color=T["border"])
        f.pack(fill="x", pady=3)

        brand_var = ctk.StringVar(value=brands[0] if brands else "")
        prod_var  = ctk.StringVar(value="")
        qty_var   = ctk.StringVar(value="1")
        price_var = ctk.StringVar(value="0")

        row1 = ctk.CTkFrame(f, fg_color="transparent")
        row1.pack(fill="x", padx=8, pady=(6, 2))

        # Combo marque
        brand_cb = ctk_combo(row1, brands, variable=brand_var, width=110)
        brand_cb.pack(side="left", padx=(0, 6))

        # Combo produit filtré par marque
        first_prods = [p["name"][:28] for p in by_brand.get(brands[0], [])]
        prod_cb = ctk_combo(row1, first_prods or ["—"], variable=prod_var, width=190)
        prod_cb.pack(side="left")

        # Supprimer
        ctk_button(row1, "✕", command=lambda fr=f: self._remove_bc_line(fr),
                   style="danger", width=28, height=28).pack(side="right")

        prod_name_to_p = {p["name"][:28]: p for p in all_products}

        def _on_brand(v):
            prods = [p["name"][:28] for p in by_brand.get(v, [])]
            prod_cb.configure(values=prods or ["—"])
            prod_var.set(prods[0] if prods else "")
            _on_prod(prod_var.get())

        def _on_prod(v):
            p = prod_name_to_p.get(v)
            if p:
                price_var.set(str(int(p.get("purchase_price", 0) or 0)))

        brand_cb.configure(command=lambda v: _on_brand(v))
        prod_cb.configure(command=lambda v: _on_prod(v))

        # Init
        if first_prods:
            prod_var.set(first_prods[0])
            _on_prod(first_prods[0])

        row2 = ctk.CTkFrame(f, fg_color="transparent")
        row2.pack(fill="x", padx=8, pady=(0, 6))
        for label, var, w in [("Qté", qty_var, 60), ("Prix unit. (MAD)", price_var, 110)]:
            ctk_label(row2, label, size=9, color=T["text_muted"]).pack(side="left", padx=(0, 2))
            ctk_entry(row2, textvariable=var, width=w).pack(side="left", padx=(0, 10))

        self._bc_lines.append({"frame": f, "prod_var": prod_var,
                                "qty_var": qty_var, "price_var": price_var,
                                "prod_map": prod_name_to_p})

    def _remove_bc_line(self, frame):
        self._bc_lines = [l for l in self._bc_lines if l["frame"] is not frame]
        frame.destroy()

    def _save_bc(self, status):
        sup_name = self._sup_var.get()
        sup_id = self._sup_map.get(sup_name)
        if not sup_id:
            return
        items = []
        for line in self._bc_lines:
            prod = line["prod_map"].get(line["prod_var"].get())
            if not prod:
                continue
            try:
                qty   = int(line["qty_var"].get() or 0)
                price = float(line["price_var"].get() or 0)
            except ValueError:
                continue
            if qty > 0:
                items.append({"product_id": prod["id"], "quantity": qty, "unit_price": price})
        if not items:
            return
        notes = self._notes_var.get()
        ref, pid = create_purchase(sup_id, items, notes, self.current_user["id"], status)
        self._refresh_bons()
        # Affiche le BC créé
        purchase, items_db = get_purchase(pid)
        self._render_bc_view(purchase, items_db)

    def _render_bc_view(self, p, items):
        """Vue d'un BC existant."""
        for w in self.bc_detail.winfo_children():
            w.destroy()

        sf = ctk.CTkScrollableFrame(self.bc_detail, fg_color="transparent",
                                     scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True, padx=12, pady=8)

        # Header BC
        sc = STATUS_COLOR.get(p["status"], T["text_muted"])
        sl = STATUS_LABEL.get(p["status"], p["status"])
        hrow = ctk.CTkFrame(sf, fg_color="transparent")
        hrow.pack(fill="x", pady=(0, 8))
        ctk_label(hrow, p["ref"], size=15, bold=True, color=T["accent"]).pack(side="left")
        ctk.CTkLabel(hrow, text=f"  {sl}", font=(T["font"], 11, "bold"),
                     text_color=sc).pack(side="left", padx=8)

        # Infos
        info_card = ctk.CTkFrame(sf, fg_color=T["surface3"], corner_radius=10)
        info_card.pack(fill="x", pady=(0, 10))
        for label, val in [
            ("Fournisseur", p.get("supplier_name") or "—"),
            ("Date",        p["created_at"][:16]),
            ("Notes",       p.get("notes") or "—"),
            ("Total",       f"{p['total']:,.2f} MAD"),
        ]:
            r = ctk.CTkFrame(info_card, fg_color="transparent")
            r.pack(fill="x", padx=12, pady=2)
            ctk_label(r, label + " :", size=10, color=T["text_muted"]).pack(side="left", padx=(0, 6))
            ctk_label(r, val, size=10).pack(side="left")

        # Lignes
        sep(sf, pady=(8, 8))
        ctk_label(sf, "Lignes commande", size=11, bold=True).pack(anchor="w", pady=(0, 6))

        col_hdr = ctk.CTkFrame(sf, fg_color=T["surface3"], corner_radius=0)
        col_hdr.pack(fill="x")
        for lbl, w in [("Produit", 180), ("Qté", 50), ("P.U.", 90), ("Total", 90)]:
            ctk.CTkLabel(col_hdr, text=lbl, font=(T["font"], 10, "bold"),
                         text_color=T["text_muted"], width=w, anchor="w").pack(
                side="left", padx=6, pady=5)

        for i, it in enumerate(items):
            bg = T["surface"] if i % 2 == 0 else T["surface2"]
            r = ctk.CTkFrame(sf, fg_color=bg, corner_radius=0, height=32)
            r.pack(fill="x"); r.pack_propagate(False)
            for v, w, c in [
                ((it.get("product_name") or "")[:24], 180, T["text"]),
                (str(it["quantity"]),                  50,  T["text_muted"]),
                (f"{it['unit_price']:,.0f}",           90,  T["text_dim"]),
                (f"{it['total']:,.0f}",                90,  T["accent"]),
            ]:
                ctk.CTkLabel(r, text=v, font=(T["font"], 10),
                             text_color=c, width=w, anchor="w").pack(side="left", padx=6)

        # Actions
        sep(sf, pady=(12, 8))
        btn_row = ctk.CTkFrame(sf, fg_color="transparent")
        btn_row.pack(fill="x")

        if p["status"] == "draft":
            ctk_button(btn_row, "📤  Marquer commandé",
                       command=lambda: self._change_status(p["id"], "ordered"),
                       style="accent", width=160, height=34).pack(side="left")

        if p["status"] == "ordered":
            ctk_button(btn_row, "✅  Confirmer réception",
                       command=lambda: self._receive(p["id"]),
                       style="success", width=170, height=34).pack(side="left")

        ctk_button(btn_row, "🖨  Export PDF",
                   command=lambda: self._export_pdf(p, items),
                   style="ghost", width=120, height=34).pack(side="right")

    def _change_status(self, pid, status):
        update_purchase_status(pid, status, self.current_user["id"])
        self._refresh_bons()
        purchase, items = get_purchase(pid)
        self._render_bc_view(purchase, items)

    def _receive(self, pid):
        receive_purchase(pid, self.current_user["id"])
        self._refresh_bons()
        self._refresh_reception()
        purchase, items = get_purchase(pid)
        self._render_bc_view(purchase, items)

    # ══════════════════════════════════════════════════════════════════════════
    # EXPORT PDF
    # ══════════════════════════════════════════════════════════════════════════
    def _export_pdf(self, p, items):
        try:
            path = self._generate_pdf(p, items)
            # Ouvre le PDF avec le viewer par défaut
            import subprocess, sys
            if sys.platform == "win32":
                os.startfile(path)
            else:
                subprocess.Popen(["xdg-open", path])
            self._toast(f"✅  PDF généré : {os.path.basename(path)}")
        except Exception as e:
            self._toast(f"❌  Erreur PDF : {e}")

    def _generate_pdf(self, p, items):
        """Génère un PDF simple via HTML + webbrowser fallback."""
        from database.models import get_settings
        settings = get_settings()
        company  = settings.get("company_name", "OptiGest Pro")
        phone    = settings.get("company_phone", "")
        address  = settings.get("company_address", "")

        rows_html = ""
        for it in items:
            rows_html += f"""
            <tr>
                <td>{it.get('reference','')}</td>
                <td>{it.get('product_name','')}</td>
                <td style="text-align:center">{it['quantity']}</td>
                <td style="text-align:right">{it['unit_price']:,.2f}</td>
                <td style="text-align:right">{it['total']:,.2f}</td>
            </tr>"""

        status_fr = STATUS_LABEL.get(p["status"], p["status"])
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Bon de Commande {p['ref']}</title>
<style>
  body {{ font-family: Arial, sans-serif; font-size: 12px; color: #1a1a2e; margin: 30px; }}
  h1   {{ font-size: 22px; color: #6c63ff; margin-bottom: 4px; }}
  .sub {{ color: #6b7280; font-size: 11px; }}
  .header {{ display: flex; justify-content: space-between; margin-bottom: 24px; }}
  .company {{ font-weight: bold; font-size: 14px; }}
  .badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px;
             background: #f59e0b; color: #fff; font-size: 10px; font-weight: bold; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
  th    {{ background: #6c63ff; color: #fff; padding: 8px; text-align: left; font-size: 11px; }}
  td    {{ padding: 7px 8px; border-bottom: 1px solid #e5e7eb; }}
  tr:nth-child(even) td {{ background: #f9fafb; }}
  .total-row td {{ font-weight: bold; background: #ede9fe; font-size: 13px; }}
  .footer {{ margin-top: 30px; color: #9ca3af; font-size: 10px; text-align: center; }}
</style>
</head>
<body>
<div class="header">
  <div>
    <div class="company">{company}</div>
    <div class="sub">{address}</div>
    <div class="sub">Tél : {phone}</div>
  </div>
  <div style="text-align:right">
    <h1>BON DE COMMANDE</h1>
    <div class="sub">{p['ref']}</div>
    <div class="sub">{p['created_at'][:10]}</div>
    <div class="badge">{status_fr}</div>
  </div>
</div>

<table>
  <tr style="background:#f3f0ff">
    <td><b>Fournisseur :</b> {p.get('supplier_name','—')}</td>
    <td><b>Notes :</b> {p.get('notes','—')}</td>
  </tr>
</table>

<table>
  <thead>
    <tr><th>Réf.</th><th>Désignation</th><th style="text-align:center">Qté</th>
        <th style="text-align:right">P.U. MAD</th><th style="text-align:right">Total MAD</th></tr>
  </thead>
  <tbody>
    {rows_html}
    <tr class="total-row">
      <td colspan="3"></td>
      <td style="text-align:right">TOTAL :</td>
      <td style="text-align:right">{p['total']:,.2f} MAD</td>
    </tr>
  </tbody>
</table>

<div class="footer">
  Document généré par OptiGest Pro — {datetime.now().strftime('%d/%m/%Y %H:%M')}
</div>
</body>
</html>"""

        # Sauvegarde HTML dans temp (s'ouvre dans navigateur)
        path = os.path.join(tempfile.gettempdir(), f"BC_{p['ref']}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return path

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 2 — RÉCEPTION
    # ══════════════════════════════════════════════════════════════════════════
    def _build_reception(self):
        tab = self.tabs.tab("📦  Réception")

        ctk_label(tab, "Bons de commande en attente de réception",
                  size=12, bold=True, color=T["text_muted"]).pack(anchor="w", pady=(8, 6))
        sep(tab, pady=(0, 8))

        # Headers
        hdr = ctk.CTkFrame(tab, fg_color=T["surface3"], corner_radius=0)
        hdr.pack(fill="x")
        for lbl, w in [("Référence", 100), ("Fournisseur", 180),
                       ("Total", 100), ("Date", 130), ("Action", 120)]:
            ctk.CTkLabel(hdr, text=lbl, font=(T["font"], 10, "bold"),
                         text_color=T["text_muted"], width=w, anchor="w").pack(
                side="left", padx=8, pady=6)

        self.recep_sf = ctk.CTkScrollableFrame(tab, fg_color="transparent",
                                                scrollbar_button_color=T["surface3"])
        self.recep_sf.pack(fill="both", expand=True)
        self._refresh_reception()

    def _refresh_reception(self):
        for w in self.recep_sf.winfo_children():
            w.destroy()
        pending = get_purchases(status="ordered")
        if not pending:
            ctk_label(self.recep_sf,
                      "✅  Aucune commande en attente",
                      color=T["success"]).pack(pady=30)
            return
        for i, p in enumerate(pending):
            bg = T["surface"] if i % 2 == 0 else T["surface2"]
            row = ctk.CTkFrame(self.recep_sf, fg_color=bg, corner_radius=0, height=42)
            row.pack(fill="x"); row.pack_propagate(False)
            for v, w, c in [
                (p["ref"],                              100, T["accent"]),
                ((p.get("supplier_name") or "")[:22],  180, T["text"]),
                (f"{p['total']:,.0f} MAD",              100, T["text"]),
                (p["created_at"][:10],                  130, T["text_muted"]),
            ]:
                ctk.CTkLabel(row, text=v, font=(T["font"], 10),
                             text_color=c, width=w, anchor="w").pack(side="left", padx=8)
            ctk_button(row, "✅  Réceptionner",
                       command=lambda pid=p["id"]: self._receive_from_tab(pid),
                       style="success", width=110, height=30).pack(side="left", padx=4)

    def _receive_from_tab(self, pid):
        receive_purchase(pid, self.current_user["id"])
        self._refresh_reception()
        self._refresh_bons()
        self._toast("✅  Marchandise reçue — stock mis à jour")

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 3 — STATISTIQUES
    # ══════════════════════════════════════════════════════════════════════════
    def _build_stats(self):
        tab = self.tabs.tab("📊  Statistiques")
        sf = ctk.CTkScrollableFrame(tab, fg_color="transparent",
                                     scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True)

        stats = get_purchase_stats()

        # KPIs
        kpi_row = ctk.CTkFrame(sf, fg_color="transparent")
        kpi_row.pack(fill="x", pady=(8, 16))
        for i in range(3):
            kpi_row.columnconfigure(i, weight=1)

        for i, (label, val, color) in enumerate([
            ("Achats ce mois (reçus)", f"{stats['total_month']:,.0f} MAD", T["primary"]),
            ("Commandes en attente",   str(stats["pending"]),               T["warning"]),
            ("Commandes reçues",       str(stats["received"]),              T["success"]),
        ]):
            card = ctk.CTkFrame(kpi_row, fg_color=T["surface"],
                                corner_radius=14, border_width=1, border_color=T["border"])
            card.grid(row=0, column=i, padx=6, sticky="nsew", ipady=10)
            ctk_label(card, label, size=10, color=T["text_muted"]).pack(pady=(12, 4))
            ctk_label(card, val, size=20, bold=True, color=color).pack()

        # Top fournisseurs
        sep(sf, pady=(0, 12))
        ctk_label(sf, "🏆  Top Fournisseurs", size=13, bold=True).pack(anchor="w", pady=(0, 8))

        if not stats["top_suppliers"]:
            ctk_label(sf, "Aucune donnée", color=T["text_muted"]).pack(pady=20)
            return

        hdr = ctk.CTkFrame(sf, fg_color=T["surface3"], corner_radius=0)
        hdr.pack(fill="x")
        for lbl, w in [("Fournisseur", 200), ("Nb commandes", 120), ("Total achats", 140)]:
            ctk.CTkLabel(hdr, text=lbl, font=(T["font"], 10, "bold"),
                         text_color=T["text_muted"], width=w, anchor="w").pack(
                side="left", padx=8, pady=6)

        for i, s in enumerate(stats["top_suppliers"]):
            bg = T["surface"] if i % 2 == 0 else T["surface2"]
            row = ctk.CTkFrame(sf, fg_color=bg, corner_radius=0, height=36)
            row.pack(fill="x"); row.pack_propagate(False)
            for v, w, c in [
                ((s.get("name") or "")[:26], 200, T["text"]),
                (str(s["cnt"]),              120, T["text_muted"]),
                (f"{s['total']:,.0f} MAD",  140, T["accent"]),
            ]:
                ctk.CTkLabel(row, text=v, font=(T["font"], 10),
                             text_color=c, width=w, anchor="w").pack(side="left", padx=8)

    # ══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    def _toast(self, msg: str):
        toast = ctk.CTkFrame(self, fg_color=T["surface2"], corner_radius=10,
                             border_width=1, border_color=T["border"])
        toast.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)
        color = T["success"] if "✅" in msg else T["danger"]
        ctk.CTkLabel(toast, text=msg, font=(T["font"], 11),
                     text_color=color).pack(padx=16, pady=10)
        self.after(3000, toast.destroy)