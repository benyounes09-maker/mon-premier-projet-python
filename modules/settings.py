"""
modules/settings.py — Module Paramètres & Licence OptiGest Pro v3
==================================================================
Onglets :
  1. Société       — infos société, logo path, coordonnées
  2. Facturation   — TVA, préfixes, devise, pied de page facture
  3. Sauvegarde    — backup manuel + auto + restauration
  4. Affichage     — thème dark/light, langue
  5. Licence       — statut, activation, Machine ID
  6. Journal       — audit trail complet
"""

import customtkinter as ctk
import os, shutil, datetime
from tkinter import filedialog, messagebox
from config import T, APP_NAME, APP_VERSION, set_theme
from ui.widgets import ctk_label, ctk_button, ctk_entry, ctk_combo, sep
from database.models import get_settings, set_setting, get_audit_log
from license import (get_machine_id, format_machine_id, check_license,
                     activate_license, show_lock_screen)


class Settings(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color=T["bg"], corner_radius=0)
        self.current_user = current_user
        self._settings = get_settings()
        self._build()

    def _s(self, key, default=""):
        return self._settings.get(key, default)

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk_label(hdr, "⚙   Paramètres", size=18, bold=True).pack(side="left")

        # Tabs
        self.tabs = ctk.CTkTabview(self, fg_color=T["surface"],
                                    segmented_button_fg_color=T["surface2"],
                                    segmented_button_selected_color=T["primary"],
                                    segmented_button_selected_hover_color=T["primary_dk"],
                                    segmented_button_unselected_color=T["surface2"],
                                    segmented_button_unselected_hover_color=T["surface3"],
                                    text_color=T["text"],
                                    text_color_disabled=T["text_muted"],
                                    border_color=T["border"],
                                    border_width=1,
                                    corner_radius=16)
        self.tabs.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        for tab in ["🏢  Société", "🧾  Facturation", "💾  Sauvegarde",
                    "🎨  Affichage", "🔑  Licence", "📋  Journal"]:
            self.tabs.add(tab)

        self._build_societe()
        self._build_facturation()
        self._build_sauvegarde()
        self._build_affichage()
        self._build_licence()
        self._build_journal()

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 1 — SOCIÉTÉ
    # ══════════════════════════════════════════════════════════════════════════
    def _build_societe(self):
        tab = self.tabs.tab("🏢  Société")
        sf = ctk.CTkScrollableFrame(tab, fg_color="transparent",
                                    scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True)

        self._soc_vars = {}
        fields = [
            ("Nom de la société *",  "company_name",    "OptiGest Wholesale"),
            ("Adresse",              "company_address",  ""),
            ("Ville",                "company_city",     ""),
            ("Code postal",          "company_zip",      ""),
            ("Téléphone",            "company_phone",    ""),
            ("Email",                "company_email",    ""),
            ("Site web",             "company_website",  ""),
            ("ICE",                  "company_ice",      ""),
            ("IF",                   "company_if",       ""),
            ("RC",                   "company_rc",       ""),
            ("CNSS",                 "company_cnss",     ""),
            ("Banque",               "company_bank",     ""),
            ("RIB / IBAN",           "company_rib",      ""),
        ]
        # 2-column grid
        grid = ctk.CTkFrame(sf, fg_color="transparent")
        grid.pack(fill="x", padx=8, pady=8)
        for i, (label, key, default) in enumerate(fields):
            col = i % 2
            row = i // 2
            grid.columnconfigure(col*2, weight=1)
            f = ctk.CTkFrame(grid, fg_color="transparent")
            f.grid(row=row, column=col*2, padx=12, pady=4, sticky="ew")
            ctk_label(f, label, size=10, color=T["text_muted"]).pack(anchor="w", pady=(0, 2))
            var = ctk.StringVar(value=self._s(key, default))
            self._soc_vars[key] = var
            ctk_entry(f, textvariable=var, width=240).pack(anchor="w")

        sep(sf, pady=(12, 8))
        self._save_btn(sf, self._save_societe)

    def _save_societe(self):
        for k, v in self._soc_vars.items():
            set_setting(k, v.get())
        self._settings = get_settings()
        self._toast("✅  Informations société enregistrées")

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 2 — FACTURATION
    # ══════════════════════════════════════════════════════════════════════════
    def _build_facturation(self):
        tab = self.tabs.tab("🧾  Facturation")
        sf = ctk.CTkScrollableFrame(tab, fg_color="transparent",
                                    scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True)

        self._fac_vars = {}
        card = self._section_card(sf, "Numérotation des documents")
        for label, key, default in [
            ("Préfixe Facture",       "prefix_invoice",  "FAC"),
            ("Préfixe Bon de livraison", "prefix_bl",    "BL"),
            ("Préfixe Avoir",         "prefix_avoir",    "AVO"),
            ("Numéro de départ",      "invoice_start",   "1"),
        ]:
            self._field_in(card, label, key, default, self._fac_vars)

        card2 = self._section_card(sf, "Taxes et Devise")
        for label, key, default in [
            ("TVA par défaut (%)",    "tva_rate",        "20"),
            ("Devise",                "currency",        "MAD"),
            ("Délai de paiement (j)", "payment_delay",   "30"),
        ]:
            self._field_in(card2, label, key, default, self._fac_vars)

        card3 = self._section_card(sf, "Pied de page facture")
        ctk_label(card3, "Texte pied de page", size=10, color=T["text_muted"]).pack(anchor="w", padx=16, pady=(8, 2))
        footer_var = ctk.StringVar(value=self._s("invoice_footer", "Merci de votre confiance."))
        self._fac_vars["invoice_footer"] = footer_var
        ctk.CTkTextbox(card3, height=80, fg_color=T["input_bg"],
                       border_color=T["border"], text_color=T["text"],
                       font=(T["font"], 11), corner_radius=8).pack(
            fill="x", padx=16, pady=(0, 12))

        sep(sf, pady=(8, 8))
        self._save_btn(sf, self._save_facturation)

    def _save_facturation(self):
        for k, v in self._fac_vars.items():
            set_setting(k, v.get())
        self._settings = get_settings()
        self._toast("✅  Paramètres facturation enregistrés")

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 3 — SAUVEGARDE
    # ══════════════════════════════════════════════════════════════════════════
    def _build_sauvegarde(self):
        tab = self.tabs.tab("💾  Sauvegarde")
        sf = ctk.CTkScrollableFrame(tab, fg_color="transparent",
                                    scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True)

        # Sauvegarde manuelle
        card = self._section_card(sf, "Sauvegarde manuelle")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)
        ctk_label(inner, "Créez une copie de sécurité de votre base de données.",
                  size=11, color=T["text_muted"]).pack(anchor="w", pady=(0, 12))
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(anchor="w")
        ctk_button(btn_row, "💾  Sauvegarder maintenant",
                   command=self._backup_now, style="primary",
                   width=200, height=38).pack(side="left", padx=(0, 10))
        ctk_button(btn_row, "📂  Choisir le dossier",
                   command=self._choose_backup_dir, style="ghost",
                   width=160, height=38).pack(side="left")
        self.backup_dir_label = ctk_label(inner, self._s("backup_dir", "Non configuré"),
                                           size=10, color=T["text_muted"])
        self.backup_dir_label.pack(anchor="w", pady=(8, 0))

        # Sauvegarde auto
        card2 = self._section_card(sf, "Sauvegarde automatique")
        inner2 = ctk.CTkFrame(card2, fg_color="transparent")
        inner2.pack(fill="x", padx=16, pady=12)
        auto_row = ctk.CTkFrame(inner2, fg_color="transparent")
        auto_row.pack(anchor="w")
        ctk_label(auto_row, "Activer la sauvegarde automatique", size=11).pack(side="left")
        self.auto_backup_var = ctk.BooleanVar(value=self._s("auto_backup", "0") == "1")
        ctk.CTkSwitch(auto_row, text="", variable=self.auto_backup_var,
                      button_color=T["primary"], progress_color=T["primary"]).pack(side="left", padx=10)
        ctk_label(inner2, "Fréquence", size=10, color=T["text_muted"]).pack(anchor="w", pady=(10, 2))
        self.backup_freq_var = ctk.StringVar(value=self._s("backup_freq", "Quotidien"))
        ctk_combo(inner2, ["Quotidien", "Hebdomadaire", "Mensuel"],
                  variable=self.backup_freq_var, width=180).pack(anchor="w")
        ctk_button(inner2, "💾  Sauvegarder config auto",
                   command=self._save_backup_config, style="accent",
                   width=200, height=36).pack(anchor="w", pady=(12, 0))

        # Restauration
        card3 = self._section_card(sf, "Restaurer une sauvegarde")
        inner3 = ctk.CTkFrame(card3, fg_color="transparent")
        inner3.pack(fill="x", padx=16, pady=12)
        ctk_label(inner3,
                  "⚠  La restauration remplace toutes les données actuelles.",
                  size=10, color=T["warning"]).pack(anchor="w", pady=(0, 10))
        ctk_button(inner3, "📂  Restaurer depuis un fichier",
                   command=self._restore, style="danger",
                   width=200, height=38).pack(anchor="w")

        self._list_backups(sf)

    def _backup_now(self):
        from config import DB_PATH
        backup_dir = self._s("backup_dir", "")
        if not backup_dir or not os.path.isdir(backup_dir):
            backup_dir = filedialog.askdirectory(title="Choisir le dossier de sauvegarde")
            if not backup_dir:
                return
            set_setting("backup_dir", backup_dir)
            self.backup_dir_label.configure(text=backup_dir)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(backup_dir, f"optigest_backup_{ts}.db")
        try:
            shutil.copy2(DB_PATH, dest)
            self._toast(f"✅  Sauvegarde créée : {os.path.basename(dest)}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Sauvegarde échouée :\n{e}")

    def _choose_backup_dir(self):
        d = filedialog.askdirectory(title="Dossier de sauvegarde")
        if d:
            set_setting("backup_dir", d)
            self.backup_dir_label.configure(text=d)

    def _save_backup_config(self):
        set_setting("auto_backup", "1" if self.auto_backup_var.get() else "0")
        set_setting("backup_freq", self.backup_freq_var.get())
        self._toast("✅  Configuration sauvegarde enregistrée")

    def _restore(self):
        from config import DB_PATH
        path = filedialog.askopenfilename(
            title="Sélectionner un fichier de sauvegarde",
            filetypes=[("Base de données", "*.db"), ("Tous les fichiers", "*.*")])
        if not path:
            return
        if not messagebox.askyesno("Confirmation",
                                    "Cette opération remplacera TOUTES vos données.\n\nContinuer ?"):
            return
        try:
            shutil.copy2(path, DB_PATH)
            self._toast("✅  Restauration réussie — redémarrez l'application")
        except Exception as e:
            messagebox.showerror("Erreur", f"Restauration échouée :\n{e}")

    def _list_backups(self, parent):
        card = self._section_card(parent, "Sauvegardes disponibles")
        backup_dir = self._s("backup_dir", "")
        if not backup_dir or not os.path.isdir(backup_dir):
            ctk_label(card, "Aucun dossier de sauvegarde configuré",
                      color=T["text_muted"]).pack(padx=16, pady=12)
            return
        files = sorted(
            [f for f in os.listdir(backup_dir) if f.startswith("optigest_backup_")],
            reverse=True)[:10]
        if not files:
            ctk_label(card, "Aucune sauvegarde trouvée", color=T["text_muted"]).pack(padx=16, pady=12)
            return
        for f in files:
            fpath = os.path.join(backup_dir, f)
            size = os.path.getsize(fpath) / 1024
            row = ctk.CTkFrame(card, fg_color=T["surface2"], corner_radius=8)
            row.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(row, text=f[:40], font=(T["font"], 10),
                         text_color=T["text"], anchor="w").pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(row, text=f"{size:.0f} Ko", font=(T["font"], 9),
                         text_color=T["text_muted"]).pack(side="right", padx=10)

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 4 — AFFICHAGE
    # ══════════════════════════════════════════════════════════════════════════
    def _build_affichage(self):
        tab = self.tabs.tab("🎨  Affichage")
        sf = ctk.CTkScrollableFrame(tab, fg_color="transparent",
                                    scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True)

        card = self._section_card(sf, "Thème de l'interface")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=16)

        # Theme toggle
        theme_row = ctk.CTkFrame(inner, fg_color="transparent")
        theme_row.pack(anchor="w")
        ctk_label(theme_row, "Mode sombre", size=12).pack(side="left")
        current_dark = self._s("theme", "dark") == "dark"
        self.dark_var = ctk.BooleanVar(value=current_dark)
        ctk.CTkSwitch(theme_row, text="", variable=self.dark_var,
                      button_color=T["primary"], progress_color=T["primary"],
                      command=self._apply_theme).pack(side="left", padx=12)

        # Preview cards
        sep(inner, pady=(16, 12))
        ctk_label(inner, "Aperçu des couleurs", size=10, color=T["text_muted"]).pack(anchor="w", pady=(0, 8))
        colors_row = ctk.CTkFrame(inner, fg_color="transparent")
        colors_row.pack(anchor="w")
        for name, color in [("Primaire", T["primary"]), ("Accent", T["accent"]),
                             ("Succès", T["success"]), ("Danger", T["danger"]),
                             ("Warning", T["warning"])]:
            c = ctk.CTkFrame(colors_row, width=70, height=50, corner_radius=8, fg_color=color)
            c.pack(side="left", padx=4)
            c.pack_propagate(False)
            ctk.CTkLabel(c, text=name, font=(T["font"], 8), text_color="#fff").place(
                relx=.5, rely=.5, anchor="center")

        # Taille de police
        card2 = self._section_card(sf, "Taille de police")
        inner2 = ctk.CTkFrame(card2, fg_color="transparent")
        inner2.pack(fill="x", padx=16, pady=12)
        ctk_label(inner2, "Taille de base", size=10, color=T["text_muted"]).pack(anchor="w", pady=(0, 4))
        self.font_size_var = ctk.StringVar(value=self._s("font_size", "12"))
        ctk_combo(inner2, ["10", "11", "12", "13", "14"], variable=self.font_size_var, width=100).pack(anchor="w")

        sep(sf, pady=(12, 8))
        self._save_btn(sf, self._save_affichage)

    def _apply_theme(self):
        mode = "dark" if self.dark_var.get() else "light"
        set_theme(mode)
        import customtkinter as ctk2
        ctk2.set_appearance_mode(mode)
        set_setting("theme", mode)

    def _save_affichage(self):
        mode = "dark" if self.dark_var.get() else "light"
        set_setting("theme", mode)
        set_setting("font_size", self.font_size_var.get())
        self._toast("✅  Préférences d'affichage enregistrées")

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 5 — LICENCE
    # ══════════════════════════════════════════════════════════════════════════
    def _build_licence(self):
        tab = self.tabs.tab("🔑  Licence")
        sf = ctk.CTkScrollableFrame(tab, fg_color="transparent",
                                    scrollbar_button_color=T["surface3"])
        sf.pack(fill="both", expand=True)

        # Statut actuel
        ok, info = check_license()
        status_card = ctk.CTkFrame(sf, corner_radius=14, border_width=2,
                                   fg_color=T["surface"],
                                   border_color=T["success"] if ok else T["danger"])
        status_card.pack(fill="x", padx=8, pady=(8, 16))
        inner = ctk.CTkFrame(status_card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        icon  = "✅" if ok else "🔒"
        color = T["success"] if ok else T["danger"]
        status_txt = "Licence active" if ok else "Licence non activée"
        ctk.CTkLabel(inner, text=f"{icon}  {status_txt}",
                     font=(T["font"], 15, "bold"), text_color=color).pack(anchor="w")
        exp_txt = f"Expiration : {info}" if ok else info
        ctk.CTkLabel(inner, text=exp_txt,
                     font=(T["font"], 11), text_color=T["text_muted"]).pack(anchor="w", pady=(4, 0))

        # Machine ID
        card = self._section_card(sf, "Identifiant de ce poste")
        mid = get_machine_id()
        mid_fmt = format_machine_id(mid)
        inner2 = ctk.CTkFrame(card, fg_color="transparent")
        inner2.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(inner2, text=mid_fmt,
                     font=("Consolas", 20, "bold"), text_color=T["accent"]).pack(anchor="w")
        ctk_label(inner2, "Communiquez ce code à votre revendeur pour obtenir votre clé de licence.",
                  size=10, color=T["text_muted"]).pack(anchor="w", pady=(4, 8))
        ctk_button(inner2, "📋  Copier l'identifiant",
                   command=lambda: self._copy_mid(mid_fmt),
                   style="ghost", width=180, height=34).pack(anchor="w")

        # Activation
        act_card = self._section_card(sf, "Activer / Changer la licence")
        act_inner = ctk.CTkFrame(act_card, fg_color="transparent")
        act_inner.pack(fill="x", padx=16, pady=16)
        ctk_label(act_inner, "Clé de licence", size=10, color=T["text_muted"]).pack(anchor="w", pady=(0, 4))
        self.lic_key_var = ctk.StringVar(value=self._s("license_key", ""))
        key_entry = ctk.CTkEntry(act_inner, textvariable=self.lic_key_var,
                                  placeholder_text="XXXXX-XXXXX-XXXXX-XXXXX",
                                  fg_color=T["input_bg"], border_color=T["border"],
                                  text_color=T["text"], font=("Consolas", 13),
                                  height=42, corner_radius=8)
        key_entry.pack(fill="x")
        key_entry.bind("<Return>", lambda e: self._activate_key())
        self.lic_msg_var = ctk.StringVar()
        ctk.CTkLabel(act_inner, textvariable=self.lic_msg_var,
                     font=(T["font"], 10), text_color=T["text_muted"]).pack(anchor="w", pady=(6, 0))
        ctk_button(act_inner, "🔓  Activer",
                   command=self._activate_key,
                   style="primary", width=140, height=40).pack(anchor="w", pady=(10, 0))

        # Infos version
        info_card = self._section_card(sf, "Informations")
        ctk.CTkLabel(info_card,
                     text=f"  {APP_NAME}  v{APP_VERSION}\n  Python {__import__('sys').version.split()[0]}\n  CustomTkinter",
                     font=("Consolas", 11), text_color=T["text_muted"],
                     justify="left").pack(anchor="w", padx=16, pady=12)

    def _copy_mid(self, mid_fmt):
        self.clipboard_clear()
        self.clipboard_append(mid_fmt)
        self._toast("📋  Identifiant copié")

    def _activate_key(self):
        key = self.lic_key_var.get().strip()
        if not key:
            self.lic_msg_var.set("❌  Saisissez une clé")
            return
        ok, info = activate_license(key)
        if ok:
            exp = "permanente" if info == "permanent" else f"jusqu'au {info}"
            self.lic_msg_var.set(f"✅  Licence activée — valide {exp}")
        else:
            self.lic_msg_var.set(f"❌  {info}")

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 6 — JOURNAL D'AUDIT
    # ══════════════════════════════════════════════════════════════════════════
    def _build_journal(self):
        tab = self.tabs.tab("📋  Journal")
        hdr = ctk.CTkFrame(tab, fg_color="transparent")
        hdr.pack(fill="x", pady=(8, 4))
        ctk_label(hdr, "Journal d'activité", size=13, bold=True).pack(side="left")
        ctk_button(hdr, "🔄 Actualiser", command=self._refresh_journal,
                   style="ghost", width=110, height=30).pack(side="right")

        # Column headers
        self.journal_frame = ctk.CTkFrame(tab, fg_color=T["surface2"], corner_radius=10)
        self.journal_frame.pack(fill="both", expand=True)

        cols = [("Utilisateur",130),("Action",120),("Module",100),("Détail",200),("Date",130)]
        hdr2 = ctk.CTkFrame(self.journal_frame, fg_color=T["surface3"], corner_radius=0)
        hdr2.pack(fill="x")
        for l, w in cols:
            ctk.CTkLabel(hdr2, text=l, font=(T["font"], 10, "bold"),
                         text_color=T["text_muted"], width=w, anchor="w").pack(side="left", padx=8, pady=8)

        self.journal_sf = ctk.CTkScrollableFrame(self.journal_frame, fg_color="transparent",
                                                  scrollbar_button_color=T["surface3"])
        self.journal_sf.pack(fill="both", expand=True)
        self._refresh_journal()

    def _refresh_journal(self):
        for w in self.journal_sf.winfo_children():
            w.destroy()
        logs = get_audit_log(200)
        if not logs:
            ctk_label(self.journal_sf, "Aucune activité enregistrée",
                      color=T["text_muted"]).pack(pady=30)
            return
        for i, log in enumerate(logs):
            bg = T["surface"] if i % 2 == 0 else T["surface2"]
            row = ctk.CTkFrame(self.journal_sf, fg_color=bg, corner_radius=0, height=34)
            row.pack(fill="x"); row.pack_propagate(False)
            for v, w, c in [
                ((log.get("full_name") or "Système")[:16], 130, T["text"]),
                (log.get("action", "")[:14],               120, T["primary"]),
                (log.get("module", "")[:12],               100, T["text_dim"]),
                (log.get("detail", "")[:28],               200, T["text_muted"]),
                (log.get("created_at", "")[:16],           130, T["text_muted"]),
            ]:
                ctk.CTkLabel(row, text=v, font=(T["font"], 9),
                             text_color=c, width=w, anchor="w").pack(side="left", padx=6)

    # ══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    def _section_card(self, parent, title):
        card = ctk.CTkFrame(parent, fg_color=T["surface"], corner_radius=12,
                            border_width=1, border_color=T["border"])
        card.pack(fill="x", padx=8, pady=(0, 12))
        ctk.CTkLabel(card, text=title, font=(T["font"], 11, "bold"),
                     text_color=T["text"]).pack(anchor="w", padx=16, pady=(12, 0))
        ctk.CTkFrame(card, fg_color=T["border"], height=1, corner_radius=0).pack(
            fill="x", pady=(8, 0))
        return card

    def _field_in(self, card, label, key, default, var_dict):
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=4)
        ctk_label(inner, label, size=10, color=T["text_muted"]).pack(anchor="w", pady=(0, 2))
        var = ctk.StringVar(value=self._s(key, default))
        var_dict[key] = var
        ctk_entry(inner, textvariable=var, width=260).pack(anchor="w")

    def _save_btn(self, parent, command):
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=(0, 8))
        ctk_button(btn_frame, "💾  Enregistrer", command=command,
                   style="primary", width=160, height=40).pack(side="left")

    def _toast(self, msg: str):
        """Notification discrète en bas."""
        toast = ctk.CTkFrame(self, fg_color=T["surface2"], corner_radius=10,
                             border_width=1, border_color=T["border"])
        toast.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)
        ctk.CTkLabel(toast, text=msg, font=(T["font"], 11),
                     text_color=T["success"]).pack(padx=16, pady=10)
        self.after(3000, toast.destroy)
