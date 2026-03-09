"""
keygen.py — Interface graphique de génération de licences OptiGest Pro
======================================================================
Placer à côté de main.py. Usage : python keygen.py
OUTIL PRIVÉ — ne pas distribuer aux clients.
"""

import customtkinter as ctk
import hashlib, hmac, datetime, os

_SECRET = b"0ptiG3st#Qu3id!2025$M@roc"
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys_log.txt")

DUREES = {
    "1 mois":    30,
    "3 mois":    90,
    "6 mois":   180,
    "1 an":     365,
    "2 ans":    730,
    "Permanent": None,
}


def generate_key(machine_id: str, expiry: str) -> str:
    mid_clean = machine_id.replace("-", "").upper()
    payload   = f"{mid_clean}:{expiry}".encode()
    digest    = hmac.new(_SECRET, payload, hashlib.sha256).hexdigest()
    if expiry == "permanent":
        prefix = "PERM"
    else:
        d    = datetime.datetime.strptime(expiry, "%Y-%m-%d")
        days = (d - datetime.datetime(2020, 1, 1)).days
        prefix = f"{days:04X}"
    raw = (prefix + digest[:16]).upper()
    return f"{raw[0:5]}-{raw[5:10]}-{raw[10:15]}-{raw[15:20]}"


def log_key(mid, expiry, key):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}]  MID: {mid}  Expiry: {expiry:<12}  Key: {key}\n")


class KeygenApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("OptiGest Pro — Générateur de Licences")
        self.geometry("520x540")
        self.resizable(False, False)
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="🔑  Générateur de Licences",
                     font=("Segoe UI", 18, "bold"),
                     text_color="#6c63ff").pack(pady=16)
        ctk.CTkLabel(hdr, text="OptiGest Pro — OUTIL PRIVÉ",
                     font=("Segoe UI", 10),
                     text_color="#6b7280").pack(pady=(0, 12))

        body = ctk.CTkFrame(self, fg_color="#0f0f1a", corner_radius=0)
        body.pack(fill="both", expand=True, padx=30, pady=20)

        # Machine ID
        ctk.CTkLabel(body, text="Machine ID du client",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#9ca3af").pack(anchor="w", pady=(0, 4))

        mid_frame = ctk.CTkFrame(body, fg_color="transparent")
        mid_frame.pack(fill="x")
        self.mid_var = ctk.StringVar()
        self.mid_entry = ctk.CTkEntry(mid_frame,
                                      textvariable=self.mid_var,
                                      placeholder_text="XXXX-XXXX-XXXX-XXXX",
                                      font=("Consolas", 13),
                                      height=42, corner_radius=8,
                                      border_color="#374151",
                                      fg_color="#1f2937")
        self.mid_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(mid_frame, text="Coller",
                      command=self._paste,
                      fg_color="#374151", hover_color="#4b5563",
                      width=60, height=42, corner_radius=8).pack(side="left", padx=(6, 0))

        # Durée
        ctk.CTkLabel(body, text="Durée de la licence",
                     font=("Segoe UI", 11, "bold"),
                     text_color="#9ca3af").pack(anchor="w", pady=(16, 6))

        self.dur_var = ctk.StringVar(value="1 an")
        dur_frame = ctk.CTkFrame(body, fg_color="transparent")
        dur_frame.pack(fill="x")
        for i, d in enumerate(DUREES.keys()):
            ctk.CTkRadioButton(dur_frame, text=d,
                               variable=self.dur_var, value=d,
                               font=("Segoe UI", 11),
                               text_color="#e5e7eb",
                               fg_color="#6c63ff",
                               border_color="#374151").grid(
                row=i // 3, column=i % 3, sticky="w", padx=10, pady=4)

        # Générer
        ctk.CTkButton(body, text="⚡  Générer la clé",
                      command=self._generate,
                      fg_color="#6c63ff", hover_color="#5b52e0",
                      font=("Segoe UI", 13, "bold"),
                      height=44, corner_radius=10).pack(fill="x", pady=(20, 0))

        # Résultat
        self.result_frame = ctk.CTkFrame(body,
                                          fg_color="#111827",
                                          corner_radius=10,
                                          border_width=1,
                                          border_color="#374151")
        self.result_frame.pack(fill="x", pady=(16, 0))

        self.key_label = ctk.CTkLabel(self.result_frame,
                                       text="—",
                                       font=("Consolas", 16, "bold"),
                                       text_color="#6c63ff")
        self.key_label.pack(pady=(14, 2))

        self.exp_label = ctk.CTkLabel(self.result_frame,
                                       text="",
                                       font=("Segoe UI", 10),
                                       text_color="#9ca3af")
        self.exp_label.pack(pady=(0, 6))

        btn_row = ctk.CTkFrame(self.result_frame, fg_color="transparent")
        btn_row.pack(pady=(0, 10))
        ctk.CTkButton(btn_row, text="📋  Copier la clé",
                      command=self._copy,
                      fg_color="#1d4ed8", hover_color="#1e40af",
                      width=130, height=34, corner_radius=8).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="📄  Voir journal",
                      command=self._open_log,
                      fg_color="#374151", hover_color="#4b5563",
                      width=130, height=34, corner_radius=8).pack(side="left", padx=4)

        self._generated_key = ""

    def _paste(self):
        try:
            txt = self.clipboard_get().strip()
            self.mid_var.set(txt)
        except Exception:
            pass

    def _generate(self):
        mid = self.mid_var.get().strip().upper()
        if not mid:
            self.key_label.configure(text="⚠  Entrez un Machine ID", text_color="#ef4444")
            return

        dur = self.dur_var.get()
        days = DUREES[dur]
        if days is None:
            expiry = "permanent"
            exp_txt = "Licence permanente"
        else:
            exp_date = datetime.date.today() + datetime.timedelta(days=days)
            expiry = exp_date.strftime("%Y-%m-%d")
            exp_txt = f"Expire le : {exp_date.strftime('%d/%m/%Y')}"

        key = generate_key(mid, expiry)
        self._generated_key = key
        log_key(mid, expiry, key)

        self.key_label.configure(text=key, text_color="#6c63ff")
        self.exp_label.configure(text=exp_txt)

    def _copy(self):
        if self._generated_key:
            self.clipboard_clear()
            self.clipboard_append(self._generated_key)
            self.key_label.configure(text_color="#22c55e")
            self.after(1500, lambda: self.key_label.configure(text_color="#6c63ff"))

    def _open_log(self):
        if os.path.exists(LOG_FILE):
            os.startfile(LOG_FILE)
        else:
            self.key_label.configure(text="Aucun journal", text_color="#9ca3af")


if __name__ == "__main__":
    app = KeygenApp()
    app.mainloop()
