import customtkinter as ctk
from ui.widgets import KPICard, ctk_label, ctk_button, ctk_frame, sep
from config import T
from database.models import get_dashboard_stats, get_stock_alerts

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as mpatches


class Dashboard(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color=T["bg"], corner_radius=0)
        self.current_user = current_user
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk_label(hdr, "📊  Tableau de bord", size=18, bold=True).pack(side="left")
        ctk_button(hdr, "🔄  Actualiser", command=self._refresh,
                   style="ghost", width=120, height=32).pack(side="right")
        ctk_label(hdr, self._greeting(), size=11, color=T["text_muted"]).pack(side="right", padx=16)

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                           scrollbar_button_color=T["surface3"])
        self.body.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        self._load()

    def _greeting(self):
        from datetime import datetime
        h = datetime.now().hour
        name = self.current_user["full_name"].split()[0]
        g = "Bonjour" if 5 <= h < 12 else "Bon après-midi" if h < 18 else "Bonsoir"
        return f"{g}, {name} 👋"

    def _refresh(self):
        for w in self.body.winfo_children():
            w.destroy()
        self._load()

    def _load(self):
        stats = get_dashboard_stats()
        alerts = get_stock_alerts()
        self._build_kpis(stats)
        self._build_charts(stats)
        self._build_bottom(stats, alerts)

    def _build_kpis(self, s):
        frame = ctk.CTkFrame(self.body, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 16))
        for i in range(6):
            frame.columnconfigure(i, weight=1)

        prev_month = s["monthly_ca"][-2] if len(s["monthly_ca"]) >= 2 else 0
        cur_month  = s["monthly_ca"][-1] if s["monthly_ca"] else 0
        delta = ((cur_month - prev_month) / prev_month * 100) if prev_month else None

        kpis = [
            ("CA Aujourd'hui",  f"{s['sales_today']:,.0f} MAD",  "💰", T["primary"],    None),
            ("CA Ce Mois",      f"{s['sales_month']:,.0f} MAD",  "📅", T["accent"],     delta),
            ("CA Année",        f"{s['sales_year']:,.0f} MAD",   "🏆", T["success"],    None),
            ("Factures/mois",   str(s["invoices_month"]),         "🧾", T["info"],       None),
            ("Stock bas ⚠",    str(s["low_stock"]),              "📦", T["warning"],    None),
            ("Clients actifs",  str(s["total_customers"]),        "👥", T["text_dim"],   None),
        ]
        for i, (title, val, icon, color, delta_) in enumerate(kpis):
            card = KPICard(frame, title, val, icon, color, delta_)
            card.grid(row=0, column=i, padx=5, sticky="nsew", ipady=4)

    def _build_charts(self, s):
        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", pady=(0, 16))
        row.columnconfigure(0, weight=3)
        row.columnconfigure(1, weight=2)

        self._chart_bar(row, s)
        self._chart_pie(row, s)

    def _chart_bar(self, parent, s):
        card = ctk.CTkFrame(parent, fg_color=T["surface"], corner_radius=16,
                            border_width=1, border_color=T["border"])
        card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        ctk_label(card, "📈  CA Mensuel — 12 derniers mois", size=12, bold=True,
                  color=T["text"]).pack(anchor="w", padx=16, pady=(14, 0))
        sep(card, pady=(8, 0))

        fig = Figure(figsize=(7, 2.8), dpi=96)
        fig.patch.set_facecolor(T["mpl_bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(T["mpl_bg"])

        x = range(len(s["monthly_labels"]))
        bars = ax.bar(x, s["monthly_ca"], color=T["mpl_bar1"], width=0.6,
                      zorder=3, linewidth=0)
        # Gradient effect: last bar accent
        bars[-1].set_color(T["accent"])

        ax.plot(x, s["monthly_ca"], color=T["mpl_line"], linewidth=1.5,
                marker="o", markersize=3, alpha=0.6, zorder=4)

        ax.set_xticks(list(x))
        ax.set_xticklabels(s["monthly_labels"], color=T["mpl_fg"], fontsize=8)
        ax.tick_params(axis="y", colors=T["mpl_fg"], labelsize=8)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
            lambda v, _: f"{v/1000:.0f}k"))
        ax.grid(axis="y", color=T["mpl_grid"], linewidth=0.5, zorder=1)
        ax.spines[:].set_visible(False)
        ax.tick_params(axis="x", length=0)
        fig.tight_layout(pad=1.2)

        canvas = FigureCanvasTkAgg(fig, master=card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    def _chart_pie(self, parent, s):
        card = ctk.CTkFrame(parent, fg_color=T["surface"], corner_radius=16,
                            border_width=1, border_color=T["border"])
        card.grid(row=0, column=1, sticky="nsew")
        ctk_label(card, "🥧  Ventes par Catégorie", size=12, bold=True,
                  color=T["text"]).pack(anchor="w", padx=16, pady=(14, 0))
        sep(card, pady=(8, 0))

        cats = s.get("cat_data", [])
        if not cats:
            ctk_label(card, "Pas de données", color=T["text_muted"]).pack(expand=True)
            return

        labels = [c["category"] for c in cats]
        sizes  = [c["cnt"] for c in cats]
        colors = T["mpl_pie"][:len(labels)]

        fig = Figure(figsize=(3.4, 2.8), dpi=96)
        fig.patch.set_facecolor(T["mpl_bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(T["mpl_bg"])
        wedges, texts, autotexts = ax.pie(
            sizes, labels=None, autopct="%1.0f%%",
            colors=colors, startangle=90,
            pctdistance=0.75,
            wedgeprops={"linewidth": 2, "edgecolor": T["mpl_bg"]})
        for at in autotexts:
            at.set_color(T["mpl_fg"]); at.set_fontsize(8)
        # Donut
        centre = matplotlib.patches.Circle((0, 0), 0.5, fc=T["mpl_bg"])
        ax.add_patch(centre)
        legend = [mpatches.Patch(color=c, label=l) for c, l in zip(colors, labels)]
        ax.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.5, -0.12),
                  ncol=3, fontsize=7, frameon=False,
                  labelcolor=T["mpl_fg"])
        fig.tight_layout(pad=0.5)

        canvas = FigureCanvasTkAgg(fig, master=card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    def _build_bottom(self, s, alerts):
        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", pady=(0, 8))
        row.columnconfigure(0, weight=3)
        row.columnconfigure(1, weight=2)

        self._recent_sales(row, s)
        self._stock_alerts(row, alerts)

    def _recent_sales(self, parent, s):
        card = ctk.CTkFrame(parent, fg_color=T["surface"], corner_radius=16,
                            border_width=1, border_color=T["border"])
        card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        ctk_label(card, "🧾  Dernières Ventes", size=12, bold=True).pack(anchor="w", padx=16, pady=(14, 0))
        sep(card, pady=(8, 0))

        cols = [("Facture", 90), ("Client", 160), ("Total", 100), ("Paiement", 110), ("Date", 130)]
        hdr = ctk.CTkFrame(card, fg_color=T["surface2"], corner_radius=0)
        hdr.pack(fill="x")
        for lbl, w in cols:
            ctk.CTkLabel(hdr, text=lbl, font=(T["font"], 10, "bold"),
                         text_color=T["text_muted"], width=w, anchor="w").pack(side="left", padx=8, pady=6)

        sf = ctk.CTkScrollableFrame(card, fg_color="transparent", height=200,
                                    scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True, padx=0, pady=0)

        for i, sale in enumerate(s["recent_sales"]):
            bg = T["surface"] if i % 2 == 0 else T["surface2"]
            row_ = ctk.CTkFrame(sf, fg_color=bg, corner_radius=0, height=36)
            row_.pack(fill="x")
            row_.pack_propagate(False)
            vals = [
                sale["invoice_number"],
                (sale.get("full_name") or "—")[:22],
                f"{sale['total']:,.0f} MAD",
                sale["payment_method"],
                sale["created_at"][:16],
            ]
            widths = [90, 160, 100, 110, 130]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(row_, text=v, font=(T["font"], 10),
                             text_color=T["text"], width=w, anchor="w").pack(side="left", padx=8)

    def _stock_alerts(self, parent, alerts):
        card = ctk.CTkFrame(parent, fg_color=T["surface"], corner_radius=16,
                            border_width=1, border_color=T["border"])
        card.grid(row=0, column=1, sticky="nsew")

        count = len(alerts)
        color = T["danger"] if count > 0 else T["success"]
        title = f"⚠  Alertes Stock  ({count})" if count else "✅  Stock OK"
        ctk_label(card, title, size=12, bold=True, color=color).pack(anchor="w", padx=16, pady=(14, 0))
        sep(card, pady=(8, 0))

        if not alerts:
            ctk_label(card, "Aucun produit en rupture", color=T["text_muted"]).pack(expand=True, pady=30)
            return

        sf = ctk.CTkScrollableFrame(card, fg_color="transparent", height=230,
                                    scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True)

        for i, p in enumerate(alerts[:15]):
            bg = T["surface"] if i % 2 == 0 else T["surface2"]
            row_ = ctk.CTkFrame(sf, fg_color=bg, corner_radius=8)
            row_.pack(fill="x", padx=8, pady=2)
            left = ctk.CTkFrame(row_, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=10, pady=6)
            ctk.CTkLabel(left, text=p["name"][:28], font=(T["font"], 10, "bold"),
                         text_color=T["text"], anchor="w").pack(anchor="w")
            ctk.CTkLabel(left, text=p.get("reference",""), font=(T["font"], 9),
                         text_color=T["text_muted"], anchor="w").pack(anchor="w")
            stock_color = T["danger"] if p["stock"] == 0 else T["warning"]
            ctk.CTkLabel(row_, text=f"{p['stock']} u", font=(T["font"], 11, "bold"),
                         text_color=stock_color, width=48).pack(side="right", padx=10)
