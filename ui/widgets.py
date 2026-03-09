import customtkinter as ctk
from config import T

def apply_ctk_theme(mode="dark"):
    ctk.set_appearance_mode(mode)
    ctk.set_default_color_theme("blue")

def ctk_frame(parent, **kw):
    kw.setdefault("fg_color", T["surface"])
    kw.setdefault("corner_radius", 12)
    return ctk.CTkFrame(parent, **kw)

def ctk_card(parent, **kw):
    kw.setdefault("fg_color", T["surface"])
    kw.setdefault("corner_radius", 16)
    kw.setdefault("border_width", 1)
    kw.setdefault("border_color", T["border"])
    return ctk.CTkFrame(parent, **kw)

def ctk_label(parent, text, size=13, bold=False, color=None, **kw):
    weight = "bold" if bold else "normal"
    kw["text_color"] = color or T["text"]
    return ctk.CTkLabel(parent, text=text,
                        font=(T["font"], size, weight), **kw)

def ctk_button(parent, text, command=None, style="primary", width=120, height=36, **kw):
    colors = {
        "primary": (T["primary"],      T["primary_dk"]),
        "success": (T["success"],      "#16a34a"),
        "danger":  (T["danger"],       "#dc2626"),
        "ghost":   (T["surface2"],     T["surface3"]),
        "accent":  (T["accent"],       T["accent_dk"]),
    }
    fg, hover = colors.get(style, colors["primary"])
    return ctk.CTkButton(parent, text=text, command=command,
                         fg_color=fg, hover_color=hover,
                         text_color="#ffffff",
                         font=(T["font"], 12, "bold"),
                         corner_radius=8, width=width, height=height, **kw)

def ctk_entry(parent, placeholder="", width=200, **kw):
    kw.setdefault("fg_color", T["input_bg"])
    kw.setdefault("border_color", T["border"])
    kw.setdefault("text_color", T["text"])
    kw.setdefault("placeholder_text_color", T["text_muted"])
    kw.setdefault("corner_radius", 8)
    kw.setdefault("height", 38)
    return ctk.CTkEntry(parent, placeholder_text=placeholder,
                        width=width, font=(T["font"], 12), **kw)

def ctk_combo(parent, values, width=180, variable=None, **kw):
    kw.setdefault("fg_color", T["input_bg"])
    kw.setdefault("border_color", T["border"])
    kw.setdefault("text_color", T["text"])
    kw.setdefault("button_color", T["primary"])
    kw.setdefault("dropdown_fg_color", T["surface"])
    kw.setdefault("dropdown_text_color", T["text"])
    kw.setdefault("corner_radius", 8)
    kw.setdefault("height", 38)
    combo = ctk.CTkComboBox(parent, values=values, width=width,
                            font=(T["font"], 12), **kw)
    if variable is not None:
        combo.set(variable.get())
        combo.configure(command=lambda v, var=variable: var.set(v))
        # Sync inverse : si la variable change, met à jour le combo
        variable.trace_add("write", lambda *_, c=combo, v=variable: c.set(v.get()))
    return combo

def sep(parent, orient="h", **kw):
    if orient == "h":
        f = ctk.CTkFrame(parent, height=1, fg_color=T["border"], corner_radius=0)
        f.pack(fill="x", **kw)
    else:
        f = ctk.CTkFrame(parent, width=1, fg_color=T["border"], corner_radius=0)
        f.pack(fill="y", **kw)
    return f

def scrolled_frame(parent, **kw):
    return ctk.CTkScrollableFrame(parent, fg_color=T["bg"],
                                  scrollbar_button_color=T["primary"],
                                  scrollbar_button_hover_color=T["primary_dk"],
                                  **kw)

class KPICard(ctk.CTkFrame):
    def __init__(self, parent, title, value, icon, color, delta=None, **kw):
        super().__init__(parent, fg_color=T["surface"], corner_radius=16,
                         border_width=1, border_color=T["border"], **kw)
        self.configure(cursor="hand2")
        self._build(title, value, icon, color, delta)

    def _build(self, title, value, icon, color, delta):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        # Icon circle — pas de transparence alpha (Tkinter n'accepte que #RRGGBB)
        ic = ctk.CTkFrame(inner, width=48, height=48, corner_radius=12,
                          fg_color=T["surface2"])
        ic.pack(side="left", padx=(0, 14))
        ic.pack_propagate(False)
        ctk.CTkLabel(ic, text=icon, font=("Segoe UI Emoji", 22),
                     text_color=color).place(relx=.5, rely=.5, anchor="center")

        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(right, text=title, font=(T["font"], 10),
                     text_color=T["text_muted"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(right, text=value, font=(T["font"], 20, "bold"),
                     text_color=T["text"], anchor="w").pack(anchor="w", pady=(2,0))
        if delta is not None:
            sign = "▲" if delta >= 0 else "▼"
            col = T["success"] if delta >= 0 else T["danger"]
            ctk.CTkLabel(right, text=f"{sign} {abs(delta):.1f}% vs mois préc.",
                         font=(T["font"], 9), text_color=col, anchor="w").pack(anchor="w")