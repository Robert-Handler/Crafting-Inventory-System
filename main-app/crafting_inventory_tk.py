# crafting_inventory_tk.py
from __future__ import annotations
import sys
import math
import time
import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Callable, Dict, Any

# ---------------------------
# Data model & App State
# ---------------------------

CATEGORIES = ["Yarn", "Fabric", "Tool", "Notion", "Other"]
UNITS = ["skein", "g", "m", "yd", "pair", "pcs"]

@dataclass
class Supply:
    id: int
    name: str
    category: str
    quantity: float
    unit: str
    color: str = ""
    brand: str = ""
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    updated: datetime = field(default_factory=datetime.now)

    def to_row(self) -> List[str]:
        tags_str = ", ".join(self.tags)
        return [
            self.name,
            self.category,
            f"{self.quantity:g}",
            self.unit,
            self.color or "-",
            self.updated.strftime("%Y-%m-%d"),
            "View/Edit",
        ]

class AppState:
    def __init__(self):
        self.current_user: Optional[str] = None
        # seed with example data for paper prototype and demo
        self.supplies: List[Supply] = [
            Supply(
                id=1, name="DK Yarn Blue", category="Yarn",
                quantity=3.0, unit="skein", color="Blue",
                brand="Cascade", tags=["dk", "wool", "blue"],
                notes="For winter hat project.",
                updated=datetime(2026, 1, 19)
            ),
            Supply(
                id=2, name="Cotton Fabric", category="Fabric",
                quantity=2.5, unit="yd", color="White",
                brand="Kona", tags=["cotton", "white", "quilting"],
                notes="For quilt borders.",
                updated=datetime(2026, 1, 19)
            ),
            Supply(
                id=3, name="4mm Needles", category="Tool",
                quantity=1, unit="pair", color="",
                brand="", tags=[],
                notes="",
                updated=datetime(2026, 1, 15)
            ),
            Supply(
                id=4, name="Worsted Yarn Red", category="Yarn",
                quantity=2.0, unit="skein", color="Red",
                brand="Lion Brand", tags=["worsted", "acrylic", "red"],
                notes="Scarf project.",
                updated=datetime(2026, 1, 20)
            ),
            Supply(
                id=5, name="Cotton Batting", category="Fabric",
                quantity=1.0, unit="yd", color="Natural",
                brand="Warm & Natural", tags=["batting", "quilt"],
                notes="Low loft.",
                updated=datetime(2026, 1, 22)
            ),
            Supply(
                id=6, name="Zipper 9-inch", category="Notion",
                quantity=4.0, unit="pcs", color="Black",
                brand="YKK", tags=["zipper", "bags", "notion"],
                notes="For pouches.",
                updated=datetime(2026, 1, 18)
            ),
            Supply(
                id=7, name="All-Purpose Thread", category="Notion",
                quantity=200.0, unit="g", color="Ivory",
                brand="Gutermann", tags=["poly", "thread"],
                notes="500m spool; approx weight for tracking.",
                updated=datetime(2026, 1, 23)
            ),
            Supply(
                id=8, name="Elastic 1-inch", category="Notion",
                quantity=5.0, unit="m", color="White",
                brand="Dritz", tags=["elastic", "waistband"],
                notes="Non-roll.",
                updated=datetime(2026, 1, 21)
            ),
            Supply(
                id=9, name="Embroidery Floss Set", category="Notion",
                quantity=24.0, unit="pcs", color="Assorted",
                brand="DMC", tags=["floss", "embroidery", "assorted"],
                notes="24-skein assorted pack.",
                updated=datetime(2026, 1, 17)
            ),
            Supply(
                id=10, name="Rotary Cutter Blades 45mm", category="Tool",
                quantity=5.0, unit="pcs", color="",
                brand="Olfa", tags=["rotary", "blades", "cutting"],
                notes="Replacement blades.",
                updated=datetime(2026, 1, 24)
            ),
            Supply(
                id=11, name="Pins – Glass Head", category="Notion",
                quantity=100.0, unit="pcs", color="Assorted",
                brand="Clover", tags=["pins", "notion"],
                notes="Heat-resistant heads.",
                updated=datetime(2026, 1, 16)
            ),
            Supply(
                id=12, name="Linen Fabric Natural", category="Fabric",
                quantity=1.75, unit="yd", color="Natural",
                brand="Robert Kaufman", tags=["linen", "garment"],
                notes="Pre-washed.",
                updated=datetime(2026, 1, 25)
            ),
            Supply(
                id=13, name="Blocking Mats", category="Tool",
                quantity=9.0, unit="pcs", color="Gray",
                brand="KnitIQ", tags=["blocking", "knitting"],
                notes="Interlocking tiles for blocking.",
                updated=datetime(2026, 1, 26)
            ),
        ]
        self.next_id: int = 4

        # UI state
        self.search_query: str = ""
        self.sort_by: str = "name"  # name | quantity | updated
        self.sort_dir: str = "asc"  # asc | desc
        self.filter_categories: set[str] = set()
        self.filter_units: set[str] = set()
        self.filter_color: str = ""
        self.filter_tags: str = ""

        # pagination
        self.page_size: int = 10
        self.page_index: int = 0  # zero-based

    # --- supply operations ---
    def add_supply(self, s: Supply) -> Supply:
        s.id = self.next_id
        self.next_id += 1
        s.updated = datetime.now()
        self.supplies.append(s)
        return s

    def update_supply(self, s: Supply) -> None:
        s.updated = datetime.now()

    def delete_supply(self, supply_id: int) -> None:
        self.supplies = [x for x in self.supplies if x.id != supply_id]

    def find_by_id(self, supply_id: int) -> Optional[Supply]:
        for s in self.supplies:
            if s.id == supply_id:
                return s
        return None

    # --- filtering & sorting & pagination ---
    def _matches_filters(self, s: Supply) -> bool:
        # search across name, category, tags
        q = self.search_query.lower().strip()
        if q:
            hay = " ".join([s.name, s.category, " ".join(s.tags)]).lower()
            if q not in hay:
                return False

        if self.filter_categories and s.category not in self.filter_categories:
            return False
        if self.filter_units and s.unit not in self.filter_units:
            return False
        if self.filter_color:
            if self.filter_color.lower() not in (s.color or "").lower():
                return False
        if self.filter_tags:
            # substring match in joined tags
            if self.filter_tags.lower() not in " ".join(s.tags).lower():
                return False
        return True

    def _sort_key(self, s: Supply):
        if self.sort_by == "name":
            return s.name.lower()
        if self.sort_by == "quantity":
            return s.quantity
        if self.sort_by == "updated":
            return s.updated
        return s.name.lower()

    def query_supplies(self) -> tuple[List[Supply], int]:
        rows = [s for s in self.supplies if self._matches_filters(s)]
        rows.sort(key=self._sort_key, reverse=(self.sort_dir == "desc"))
        total = len(rows)

        # pagination window
        start = self.page_index * self.page_size
        end = start + self.page_size
        return rows[start:end], total

# ---------------------------
# Utility: Banner (S5)
# ---------------------------

class Banner(ttk.Frame):
    """Inline, non-blocking banner for success/info/warn/error with optional Retry."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(padding=(8, 6))
        self._type = tk.StringVar(value="info")
        self._msg = tk.StringVar(value="")
        self._retry_cb: Optional[Callable[[], None]] = None

        self.icon = ttk.Label(self, text="ℹ")
        self.label = ttk.Label(self, textvariable=self._msg, wraplength=800)
        self.btn_retry = ttk.Button(self, text="Retry", command=self._on_retry)
        self.btn_close = ttk.Button(self, text="Dismiss", command=self._on_close)

        self.columnconfigure(1, weight=1)
        self.icon.grid(row=0, column=0, padx=(4, 8))
        self.label.grid(row=0, column=1, sticky="w")
        self.btn_retry.grid(row=0, column=2, padx=4)
        self.btn_close.grid(row=0, column=3, padx=4)

        self.hide()

    def show(self, kind: str, message: str, retry: Optional[Callable[[], None]] = None):
        self._type.set(kind)
        self._msg.set(message)
        self._retry_cb = retry

        # Color hint via style; fallback to background on classic theme
        bg = {"success": "#E6F4EA", "info": "#E8F0FE", "warn": "#FEF7E0", "error": "#FDE7E9"}.get(kind, "#E8F0FE")
        fg = {"success": "#137333", "info": "#1A73E8", "warn": "#B06000", "error": "#C5221F"}.get(kind, "#1A73E8")
        icon = {"success": "✓", "info": "ℹ", "warn": "⚠", "error": "⛔"}.get(kind, "ℹ")

        # use tk.Frame to force bg color
        try:
            self["style"] = ""  # ensure no ttk style overrides
        except Exception:
            pass
        self.configure(style="")

        for child in (self, self.icon, self.label):
            try:
                child.configure(background=bg)
            except tk.TclError:
                pass  # on some ttk themes background can't be set; it's okay

        self.icon.configure(text=icon, foreground=fg)
        self.label.configure(foreground=fg)
        self.btn_retry.grid() if retry else self.btn_retry.grid_remove()
        self.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 8))
        self.update_idletasks()

    def hide(self):
        self.grid_remove()

    def _on_retry(self):
        if self._retry_cb:
            self._retry_cb()

    def _on_close(self):
        self.hide()

# ---------------------------
# Sort & Filter Dialog (S4)
# ---------------------------

class SortFilterDialog(tk.Toplevel):
    def __init__(self, master, state: AppState, on_apply: Callable[[], None]):
        super().__init__(master)
        self.title("Sort & Filter")
        self.resizable(False, False)
        self.state = state
        self.on_apply = on_apply

        container = ttk.Frame(self, padding=12)
        container.grid(sticky="nsew")
        # Sort by
        frm_sort = ttk.LabelFrame(container, text="Sort by")
        frm_sort.grid(row=0, column=0, sticky="ew", padx=(0, 0), pady=(0, 8))
        self.sort_var = tk.StringVar(value=state.sort_by)
        ttk.Radiobutton(frm_sort, text="Name", variable=self.sort_var, value="name").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Radiobutton(frm_sort, text="Quantity", variable=self.sort_var, value="quantity").grid(row=0, column=1, sticky="w", padx=8, pady=4)
        ttk.Radiobutton(frm_sort, text="Last Updated", variable=self.sort_var, value="updated").grid(row=0, column=2, sticky="w", padx=8, pady=4)

        frm_dir = ttk.LabelFrame(container, text="Direction")
        frm_dir.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.dir_var = tk.StringVar(value=state.sort_dir)
        ttk.Radiobutton(frm_dir, text="Asc", variable=self.dir_var, value="asc").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Radiobutton(frm_dir, text="Desc", variable=self.dir_var, value="desc").grid(row=0, column=1, sticky="w", padx=8, pady=4)

        # Filters
        frm_filters = ttk.LabelFrame(container, text="Filter by")
        frm_filters.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        # categories
        self.vars_cat: Dict[str, tk.BooleanVar] = {}
        ttk.Label(frm_filters, text="Category:").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 0))
        cat_frame = ttk.Frame(frm_filters)
        cat_frame.grid(row=1, column=0, columnspan=3, sticky="w", padx=8)
        for i, c in enumerate(CATEGORIES):
            v = tk.BooleanVar(value=c in state.filter_categories)
            self.vars_cat[c] = v
            ttk.Checkbutton(cat_frame, text=c, variable=v).grid(row=0, column=i, padx=4, pady=4, sticky="w")

        # units
        self.vars_unit: Dict[str, tk.BooleanVar] = {}
        ttk.Label(frm_filters, text="Unit:").grid(row=2, column=0, sticky="w", padx=8, pady=(8, 0))
        unit_frame = ttk.Frame(frm_filters)
        unit_frame.grid(row=3, column=0, columnspan=3, sticky="w", padx=8)
        for i, u in enumerate(UNITS):
            v = tk.BooleanVar(value=u in state.filter_units)
            self.vars_unit[u] = v
            ttk.Checkbutton(unit_frame, text=u, variable=v).grid(row=0, column=i, padx=4, pady=4, sticky="w")

        # color / tags
        ttk.Label(frm_filters, text="Color:").grid(row=4, column=0, sticky="w", padx=8, pady=(8, 0))
        self.ent_color = ttk.Entry(frm_filters, width=24)
        self.ent_color.insert(0, state.filter_color)
        self.ent_color.grid(row=5, column=0, sticky="w", padx=8)

        ttk.Label(frm_filters, text="Tags (substring):").grid(row=4, column=1, sticky="w", padx=8, pady=(8, 0))
        self.ent_tags = ttk.Entry(frm_filters, width=24)
        self.ent_tags.insert(0, state.filter_tags)
        self.ent_tags.grid(row=5, column=1, sticky="w", padx=8)

        # Buttons
        frm_btns = ttk.Frame(container)
        frm_btns.grid(row=3, column=0, sticky="e")
        ttk.Button(frm_btns, text="Apply", command=self._apply).grid(row=0, column=0, padx=4)
        ttk.Button(frm_btns, text="Clear all", command=self._clear).grid(row=0, column=1, padx=4)
        ttk.Button(frm_btns, text="Cancel", command=self.destroy).grid(row=0, column=2, padx=4)

        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _apply(self):
        self.state.sort_by = self.sort_var.get()
        self.state.sort_dir = self.dir_var.get()
        self.state.filter_categories = {k for k, v in self.vars_cat.items() if v.get()}
        self.state.filter_units = {k for k, v in self.vars_unit.items() if v.get()}
        self.state.filter_color = self.ent_color.get().strip()
        self.state.filter_tags = self.ent_tags.get().strip()
        self.state.page_index = 0
        self.on_apply()
        self.destroy()

    def _clear(self):
        self.sort_var.set("name")
        self.dir_var.set("asc")
        for v in self.vars_cat.values():
            v.set(False)
        for v in self.vars_unit.values():
            v.set(False)
        self.ent_color.delete(0, tk.END)
        self.ent_tags.delete(0, tk.END)

# ---------------------------
# Screens (S0, S1, S2, S3a, S3b)
# ---------------------------

class LoginScreen(ttk.Frame):
    """S0: Welcome/Login"""
    def __init__(self, master, app: "App"):
        super().__init__(master, padding=16)
        self.app = app
        ttk.Label(self, text="Crafting Inventory", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 12))
        # form
        frm = ttk.LabelFrame(self, text="Welcome")
        frm.grid(row=1, column=0, sticky="ew")
        ttk.Label(frm, text="Username").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))
        self.ent_user = ttk.Entry(frm, width=32)
        self.ent_user.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
        ttk.Label(frm, text="Password").grid(row=2, column=0, sticky="w", padx=10, pady=(8, 4))
        self.ent_pass = ttk.Entry(frm, show="•", width=32)
        self.ent_pass.grid(row=3, column=0, sticky="w", padx=10, pady=(0, 8))
        self.var_remember = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Remember me", variable=self.var_remember).grid(row=4, column=0, sticky="w", padx=10, pady=(0,10))

        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, sticky="w", padx=10, pady=(0, 10))
        ttk.Button(btns, text="Log in", command=self._login).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(btns, text="Help", command=lambda: messagebox.showinfo("Help", "Enter your credentials. Press Enter to submit.")).grid(row=0, column=1)

        # key bindings
        self.ent_user.bind("<Return>", lambda e: self._login())
        self.ent_pass.bind("<Return>", lambda e: self._login())

        # status/banner area (S5)
        self.banner = Banner(self)
        # initial hint
        self.after(250, lambda: self.banner.show("info", "Tip: Press Enter to submit."))

    def focus_first(self):
        self.ent_user.focus_set()

    def _login(self):
        u = self.ent_user.get().strip()
        p = self.ent_pass.get().strip()
        if not u or not p:
            self.banner.show("warn", "Please enter both username and password.")
            return
        # For Sprint 1, any non-empty credentials are "valid"
        self.app.state.current_user = u
        self.app.show_inventory()
        self.app.show_banner("success", f"Welcome, {u}!")

class InventoryScreen(ttk.Frame):
    """S1: Inventory Home (list, search, sort/filter, add, pagination)"""
    def __init__(self, master, app: "App"):
        super().__init__(master, padding=(10,10))
        self.app = app

        # Topbar
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text="Crafting Inventory", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, sticky="w")
        self.lbl_user = ttk.Label(top, text="User: -")
        self.lbl_user.grid(row=0, column=1, sticky="e", padx=(8, 4))
        ttk.Button(top, text="Logout", command=self._logout).grid(row=0, column=2, sticky="e")

        # Status/banner area is in App (S5)

        # Header row with search & actions
        hdr = ttk.Frame(self)
        hdr.grid(row=2, column=0, sticky="ew", pady=(8,4))
        ttk.Label(hdr, text="Inventory", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(hdr, text="[i]", foreground="#555").grid(row=0, column=1, sticky="w", padx=(6,0))

        search_row = ttk.Frame(self)
        search_row.grid(row=3, column=0, sticky="ew", pady=(2, 8))
        search_row.columnconfigure(0, weight=1)
        self.ent_search = ttk.Entry(search_row)
        self.ent_search.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.ent_search.insert(0, self.app.state.search_query)
        ttk.Button(search_row, text="Sort & Filter", command=self._open_sort_filter).grid(row=0, column=1, padx=(0, 6))
        ttk.Button(search_row, text="Add Supply", command=self._add_supply).grid(row=0, column=2)

        # Table

        columns = ("Name", "Category", "Qty", "Unit", "Color", "Updated", "Action", "ActionID")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)

        # headings
        self.tree.heading("Name", text="Name")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Qty", text="Qty")
        self.tree.heading("Unit", text="Unit")
        self.tree.heading("Color", text="Color")
        self.tree.heading("Updated", text="Updated")
        self.tree.heading("Action", text="View/Edit")
        self.tree.heading("ActionID", text="")  # hidden

        # widths
        self.tree.column("Name", width=200)
        self.tree.column("Category", width=90)
        self.tree.column("Qty", width=60, anchor="e")
        self.tree.column("Unit", width=60, anchor="center")
        self.tree.column("Color", width=90)
        self.tree.column("Updated", width=100, anchor="center")
        self.tree.column("Action", width=90, anchor="center")
        self.tree.column("ActionID", width=0, stretch=False)  # hide

        # Place the Treeview in the grid and let it expand
        self.tree.grid(row=4, column=0, sticky="nsew", pady=(0, 4))

        # (Optional but recommended) Hide the internal ActionID column from display
        self.tree["displaycolumns"] = ("Name", "Category", "Qty", "Unit", "Color", "Updated", "Action")

        # Enable double-click to open detail view
        self.tree.bind("<Double-1>", self._on_double_click)

        # Pagination
        pag = ttk.Frame(self)
        pag.grid(row=5, column=0, sticky="ew", pady=(6, 0))
        self.btn_prev = ttk.Button(pag, text="< Prev", command=lambda: self._go_page(-1))
        self.btn_prev.grid(row=0, column=0, padx=4)
        self.page_buttons_frame = ttk.Frame(pag)
        self.page_buttons_frame.grid(row=0, column=1, padx=4)
        self.btn_next = ttk.Button(pag, text="Next >", command=lambda: self._go_page(1))
        self.btn_next.grid(row=0, column=2, padx=4)

        # Status line (inline info)
        self.lbl_info = ttk.Label(self, text="", foreground="#444")
        self.lbl_info.grid(row=6, column=0, sticky="w", pady=(4,0))

        # bindings
        self.ent_search.bind("<Return>", lambda e: self._apply_search())

        # make grid stretch
        self.rowconfigure(4, weight=1)
        self.columnconfigure(0, weight=1)

    def on_show(self):
        self.lbl_user.config(text=f"User: {self.app.state.current_user or '-'}")
        self.refresh_table()

    def _logout(self):
        self.app.confirm_logout()

    def _add_supply(self):
        self.app.show_add_supply()

    def _open_sort_filter(self):
        SortFilterDialog(self, self.app.state, on_apply=self._on_filters_applied)

    def _on_filters_applied(self):
        self.app.state.page_index = 0
        self.refresh_table()
        # Build message
        s = []
        if self.app.state.filter_categories:
            s.append(f"Category={','.join(sorted(self.app.state.filter_categories))}")
        if self.app.state.filter_color:
            s.append(f"Color={self.app.state.filter_color}")
        if self.app.state.filter_tags:
            s.append(f"Tags={self.app.state.filter_tags}")
        msg = "Filters applied: " + ", ".join(s) if s else "Sort updated."
        self.app.show_banner("info", msg)

    def _apply_search(self):
        self.app.state.search_query = self.ent_search.get().strip()
        self.app.state.page_index = 0
        self.refresh_table()

    def _on_double_click(self, event):
        item_id = self.tree.focus()
        if not item_id:
            return
        supply_id = int(self.tree.set(item_id, "ActionID"))
        self.app.show_detail(supply_id)

    def _go_page(self, delta: int):
        _, total = self.app.state.query_supplies()
        page_count = max(1, math.ceil(total / self.app.state.page_size))
        new_index = max(0, min(self.app.state.page_index + delta, page_count - 1))
        if new_index != self.app.state.page_index:
            self.app.state.page_index = new_index
            self.refresh_table()

    def refresh_table(self):
        # build data
        rows, total = self.app.state.query_supplies()

        # clear
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        # add rows

        for s in rows:
            vals = s.to_row() + [s.id]
            self.tree.insert("", "end", values=vals)

        # info & pagination buttons
        shown = len(rows)
        self.lbl_info.config(text=f"{shown} results (of {total})")
        self._rebuild_page_buttons(total)

    def _rebuild_page_buttons(self, total: int):
        for w in self.page_buttons_frame.winfo_children():
            w.destroy()
        page_count = max(1, math.ceil(total / self.app.state.page_size))
        cur = self.app.state.page_index

        # Show up to 7 page buttons centered around current
        start = max(0, cur - 3)
        end = min(page_count, start + 7)
        start = max(0, end - 7)

        def make_cmd(i):
            return lambda: self._set_page(i)

        for i in range(start, end):
            txt = str(i + 1)
            btn = ttk.Button(self.page_buttons_frame, text=txt, command=make_cmd(i))
            if i == cur:
                btn.state(["disabled"])
            btn.grid(row=0, column=i - start, padx=2)

        # enable/disable prev/next
        self.btn_prev.state(["!disabled"] if cur > 0 else ["disabled"])
        self.btn_next.state(["!disabled"] if cur < page_count - 1 else ["disabled"])

    def _set_page(self, i: int):
        if i != self.app.state.page_index:
            self.app.state.page_index = i
            self.refresh_table()

class DetailScreen(ttk.Frame):
    """S2: Supply Detail/Edit"""
    def __init__(self, master, app: "App"):
        super().__init__(master, padding=12)
        self.app = app
        self._current_id: Optional[int] = None

        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew")
        ttk.Button(top, text="← Back to Inventory", command=self.app.show_inventory).grid(row=0, column=0, sticky="w")
        ttk.Label(top, text="Edit Supply", font=("Segoe UI", 12, "bold")).grid(row=0, column=1, sticky="w", padx=8)

        form = ttk.Frame(self)
        form.grid(row=1, column=0, sticky="nsew", pady=(10,0))
        # Name
        ttk.Label(form, text="Name").grid(row=0, column=0, sticky="w")
        self.ent_name = ttk.Entry(form, width=40)
        self.ent_name.grid(row=0, column=1, sticky="w", padx=8, pady=4)
        # Category
        ttk.Label(form, text="Category").grid(row=1, column=0, sticky="w")
        self.cmb_cat = ttk.Combobox(form, values=CATEGORIES, state="readonly", width=20)
        self.cmb_cat.grid(row=1, column=1, sticky="w", padx=8, pady=4)
        # Quantity & Unit
        ttk.Label(form, text="Quantity").grid(row=2, column=0, sticky="w")
        self.ent_qty = ttk.Entry(form, width=10)
        self.ent_qty.grid(row=2, column=1, sticky="w", padx=8, pady=4)
        ttk.Label(form, text="Unit").grid(row=2, column=2, sticky="w")
        self.cmb_unit = ttk.Combobox(form, values=UNITS, state="readonly", width=12)
        self.cmb_unit.grid(row=2, column=3, sticky="w", padx=8, pady=4)
        # Color / Brand / Tags
        ttk.Label(form, text="Color").grid(row=3, column=0, sticky="w")
        self.ent_color = ttk.Entry(form, width=20)
        self.ent_color.grid(row=3, column=1, sticky="w", padx=8, pady=4)
        ttk.Label(form, text="Brand").grid(row=3, column=2, sticky="w")
        self.ent_brand = ttk.Entry(form, width=20)
        self.ent_brand.grid(row=3, column=3, sticky="w", padx=8, pady=4)
        ttk.Label(form, text="Tags (comma-separated)").grid(row=4, column=0, sticky="w")
        self.ent_tags = ttk.Entry(form, width=40)
        self.ent_tags.grid(row=4, column=1, columnspan=3, sticky="ew", padx=8, pady=4)
        # Notes
        ttk.Label(form, text="Notes").grid(row=5, column=0, sticky="nw")
        self.txt_notes = tk.Text(form, width=60, height=6, wrap="word")
        self.txt_notes.grid(row=5, column=1, columnspan=3, sticky="ew", padx=8, pady=4)

        # Buttons
        btns = ttk.Frame(self)
        btns.grid(row=2, column=0, sticky="w", pady=8)
        ttk.Button(btns, text="Save changes", command=self._save).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(btns, text="Cancel", command=self.app.show_inventory).grid(row=0, column=1, padx=(0, 6))
        self.btn_delete = ttk.Button(btns, text="Delete", command=self._delete)
        self.btn_delete.grid(row=0, column=2, padx=(6, 0))

    def load(self, supply_id: int):
        s = self.app.state.find_by_id(supply_id)
        if not s:
            self.app.show_banner("error", "Item not found.")
            self.app.show_inventory()
            return
        self._current_id = s.id
        self.ent_name.delete(0, tk.END); self.ent_name.insert(0, s.name)
        self.cmb_cat.set(s.category)
        self.ent_qty.delete(0, tk.END); self.ent_qty.insert(0, f"{s.quantity:g}")
        self.cmb_unit.set(s.unit)
        self.ent_color.delete(0, tk.END); self.ent_color.insert(0, s.color or "")
        self.ent_brand.delete(0, tk.END); self.ent_brand.insert(0, s.brand or "")
        self.ent_tags.delete(0, tk.END); self.ent_tags.insert(0, ", ".join(s.tags))
        self.txt_notes.delete("1.0", tk.END); self.txt_notes.insert("1.0", s.notes or "")

    def _save(self):
        if self._current_id is None:
            return
        ok, msg = self._validate()
        if not ok:
            self.app.show_banner("warn", msg)
            return
        s = self.app.state.find_by_id(self._current_id)
        if not s:
            self.app.show_banner("error", "Item not found.")
            return
        # apply
        s.name = self.ent_name.get().strip()
        s.category = self.cmb_cat.get().strip()
        s.quantity = float(self.ent_qty.get().strip())
        s.unit = self.cmb_unit.get().strip()
        s.color = self.ent_color.get().strip()
        s.brand = self.ent_brand.get().strip()
        s.tags = [t.strip() for t in self.ent_tags.get().split(",") if t.strip()]
        s.notes = self.txt_notes.get("1.0", tk.END).strip()
        self.app.state.update_supply(s)
        self.app.show_banner("success", "Saved successfully.")
        self.app.show_inventory()

    def _delete(self):
        if self._current_id is None:
            return
        if messagebox.askyesno("Delete", "Are you sure you want to delete this item?"):
            self.app.state.delete_supply(self._current_id)
            self.app.show_banner("info", "Item deleted.")
            self.app.show_inventory()

    def _validate(self) -> tuple[bool, str]:
        name = self.ent_name.get().strip()
        cat = self.cmb_cat.get().strip()
        qty = self.ent_qty.get().strip()
        unit = self.cmb_unit.get().strip()
        if not name:
            return False, "Name is required."
        if not cat:
            return False, "Category is required."
        if not unit:
            return False, "Unit is required."
        try:
            q = float(qty)
            if q < 0:
                return False, "Quantity must be a number ≥ 0."
        except ValueError:
            return False, "Quantity must be a number ≥ 0."
        return True, ""

class AddManualScreen(ttk.Frame):
    """S3a: Add Supply (Manual)"""
    def __init__(self, master, app: "App"):
        super().__init__(master, padding=12)
        self.app = app

        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew")
        ttk.Button(top, text="← Back to Inventory", command=self.app.show_inventory).grid(row=0, column=0, sticky="w")
        ttk.Label(top, text="Add Supply", font=("Segoe UI", 12, "bold")).grid(row=0, column=1, sticky="w", padx=8)

        form = ttk.Frame(self)
        form.grid(row=1, column=0, sticky="nsew", pady=(10,0))

        ttk.Label(form, text="Name*").grid(row=0, column=0, sticky="w")
        self.ent_name = ttk.Entry(form, width=40)
        self.ent_name.grid(row=0, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(form, text="Category*").grid(row=1, column=0, sticky="w")
        self.cmb_cat = ttk.Combobox(form, values=CATEGORIES, state="readonly", width=20)
        self.cmb_cat.grid(row=1, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(form, text="Unit*").grid(row=1, column=2, sticky="w")
        self.cmb_unit = ttk.Combobox(form, values=UNITS, state="readonly", width=12)
        self.cmb_unit.grid(row=1, column=3, sticky="w", padx=8, pady=4)

        ttk.Label(form, text="Quantity*").grid(row=2, column=0, sticky="w")
        self.ent_qty = ttk.Entry(form, width=10)
        self.ent_qty.grid(row=2, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(form, text="Color").grid(row=3, column=0, sticky="w")
        self.ent_color = ttk.Entry(form, width=20)
        self.ent_color.grid(row=3, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(form, text="Brand").grid(row=3, column=2, sticky="w")
        self.ent_brand = ttk.Entry(form, width=20)
        self.ent_brand.grid(row=3, column=3, sticky="w", padx=8, pady=4)

        ttk.Label(form, text="Tags (comma-separated)").grid(row=4, column=0, sticky="w")
        self.ent_tags = ttk.Entry(form, width=40)
        self.ent_tags.grid(row=4, column=1, columnspan=3, sticky="ew", padx=8, pady=4)

        ttk.Label(form, text="Notes").grid(row=5, column=0, sticky="nw")
        self.txt_notes = tk.Text(form, width=60, height=6, wrap="word")
        self.txt_notes.grid(row=5, column=1, columnspan=3, sticky="ew", padx=8, pady=4)

        btns = ttk.Frame(self)
        btns.grid(row=2, column=0, sticky="w", pady=8)
        ttk.Button(btns, text="Save item", command=self._save).grid(row=0, column=0, padx=(0,6))
        ttk.Button(btns, text="Cancel", command=self.app.show_inventory).grid(row=0, column=1)

        ttk.Label(self, text="Fields marked * are required.").grid(row=3, column=0, sticky="w", padx=2)

    def _validate(self) -> tuple[bool, str]:
        name = self.ent_name.get().strip()
        cat = self.cmb_cat.get().strip()
        qty = self.ent_qty.get().strip()
        unit = self.cmb_unit.get().strip()
        if not name:
            return False, "Name is required."
        if not cat:
            return False, "Category is required."
        if not unit:
            return False, "Unit is required."
        try:
            q = float(qty)
            if q < 0:
                return False, "Quantity must be a number ≥ 0."
        except ValueError:
            return False, "Quantity must be a number ≥ 0."
        return True, ""

    def _save(self):
        ok, msg = self._validate()
        if not ok:
            self.app.show_banner("warn", msg)
            return
        s = Supply(
            id=0,
            name=self.ent_name.get().strip(),
            category=self.cmb_cat.get().strip(),
            quantity=float(self.ent_qty.get().strip()),
            unit=self.cmb_unit.get().strip(),
            color=self.ent_color.get().strip(),
            brand=self.ent_brand.get().strip(),
            tags=[t.strip() for t in self.ent_tags.get().split(",") if t.strip()],
            notes=self.txt_notes.get("1.0", tk.END).strip(),
        )
        self.app.state.add_supply(s)
        self.app.show_banner("success", "Item created.")
        self.app.show_inventory()

class AddLookupScreen(ttk.Frame):
    """S3b: Add Supply via Lookup (optional)"""
    def __init__(self, master, app: "App"):
        super().__init__(master, padding=12)
        self.app = app

        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew")
        ttk.Button(top, text="← Back", command=self.app.show_inventory).grid(row=0, column=0, sticky="w")
        ttk.Label(top, text="Add Supply via Lookup", font=("Segoe UI", 12, "bold")).grid(row=0, column=1, sticky="w", padx=8)

        frm = ttk.Frame(self)
        frm.grid(row=1, column=0, sticky="nsew", pady=(10,0))
        ttk.Label(frm, text="Barcode/SKU").grid(row=0, column=0, sticky="w")
        self.ent_code = ttk.Entry(frm, width=30)
        self.ent_code.grid(row=0, column=1, sticky="w", padx=8)
        ttk.Button(frm, text="Lookup", command=self._lookup).grid(row=0, column=2, padx=4)

        # result fields
        self._fields: Dict[str, ttk.Entry | ttk.Combobox] = {}
        row = 1
        for label, wid, typ in [
            ("Name", 40, "entry"),
            ("Brand", 20, "entry"),
            ("Category", 20, "combo"),
            ("Unit", 12, "combo"),
            ("Default Qty", 10, "entry"),
            ("Color", 20, "entry"),
        ]:
            ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w", pady=(6,2))
            if typ == "entry":
                e = ttk.Entry(frm, width=wid)
            else:
                e = ttk.Combobox(frm, values=(CATEGORIES if label=="Category" else UNITS), state="readonly", width=wid)
            e.grid(row=row, column=1, sticky="w", padx=8)
            self._fields[label] = e
            row += 1

        btns = ttk.Frame(self)
        btns.grid(row=2, column=0, sticky="w", pady=8)
        ttk.Button(btns, text="Save item", command=self._save).grid(row=0, column=0, padx=(0,6))
        ttk.Button(btns, text="Cancel", command=self.app.show_inventory).grid(row=0, column=1)

        self._demo_catalog = {
            "0123456789": dict(Name="DK Yarn Blue", Brand="Cascade", Category="Yarn", Unit="skein", **{"Default Qty":"1", "Color":"Blue"}),
        }

    def _lookup(self):
        code = self.ent_code.get().strip()
        rec = self._demo_catalog.get(code)
        if not rec:
            self.app.show_banner("error", "Not found—switch to Manual Add?")
            return
        # fill results (editable)
        for k, v in rec.items():
            w = self._fields[k]
            if isinstance(w, ttk.Combobox):
                w.set(v)
            else:
                w.delete(0, tk.END)
                w.insert(0, v)

    def _save(self):
        # Minimal validation; push user to manual on gaps
        name = self._fields["Name"].get().strip()
        cat = self._fields["Category"].get().strip()
        unit = self._fields["Unit"].get().strip()
        qty = self._fields["Default Qty"].get().strip() or "1"
        if not name or not cat or not unit:
            self.app.show_banner("warn", "Please complete Name, Category, and Unit (or switch to Manual Add).")
            return
        try:
            q = float(qty)
            if q < 0:
                raise ValueError()
        except ValueError:
            self.app.show_banner("warn", "Default Qty must be a number ≥ 0.")
            return
        s = Supply(
            id=0,
            name=name,
            category=cat,
            quantity=q,
            unit=unit,
            color=self._fields["Color"].get().strip(),
            brand=self._fields["Brand"].get().strip(),
        )
        self.app.state.add_supply(s)
        self.app.show_banner("success", "Item created.")
        self.app.show_inventory()

# ---------------------------
# App Shell (navigation, banner, logout)
# ---------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Crafting Inventory")
        self.geometry("860x640")
        self.minsize(800, 560)

        self.state = AppState()

        # Root layout: Topbar (title row), Banner (S5), Content frame
        self.topbar = ttk.Frame(self, padding=(10, 10, 10, 0))
        self.topbar.grid(row=0, column=0, sticky="ew")
        ttk.Label(self.topbar, text="Crafting Inventory", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w")

        self.banner = Banner(self)
        # placeholder grid row for banner is row=1 (Banner handles its own show/hide)

        self.content = ttk.Frame(self, padding=(10, 0, 10, 10))
        self.content.grid(row=2, column=0, sticky="nsew")
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        # Screens
        self.screens: Dict[str, ttk.Frame] = {
            "login": LoginScreen(self.content, self),
            "inventory": InventoryScreen(self.content, self),
            "detail": DetailScreen(self.content, self),
            "add_manual": AddManualScreen(self.content, self),
            "add_lookup": AddLookupScreen(self.content, self),
        }
        for s in self.screens.values():
            s.grid(row=0, column=0, sticky="nsew")

        self.show_login()

    # --- Navigation ---
    def _raise(self, key: str):
        self.screens[key].tkraise()
        # call screen-specific hooks
        if key == "login":
            self.screens["login"].focus_first()
        if key == "inventory":
            self.screens["inventory"].on_show()

    def show_login(self):
        self._raise("login")

    def show_inventory(self):
        self._raise("inventory")

    def show_detail(self, supply_id: int):
        scr: DetailScreen = self.screens["detail"]  # type: ignore
        scr.load(supply_id)
        self._raise("detail")

    def show_add_supply(self):
        self._raise("add_manual")

    def show_add_lookup(self):
        self._raise("add_lookup")

    def show_banner(self, kind: str, message: str, retry: Optional[Callable[[], None]] = None):
        self.banner.show(kind, message, retry)

    # --- Logout (S6) ---
    def confirm_logout(self):
        dlg = tk.Toplevel(self)
        dlg.title("Logout")
        dlg.resizable(False, False)
        frm = ttk.Frame(dlg, padding=12)
        frm.grid(sticky="nsew")
        ttk.Label(frm, text="Are you sure you want to logout?").grid(row=0, column=0, columnspan=2, pady=(0, 12))
        ttk.Button(frm, text="Logout", command=lambda: self._do_logout(dlg)).grid(row=1, column=0, padx=4)
        ttk.Button(frm, text="Cancel", command=dlg.destroy).grid(row=1, column=1, padx=4)
        dlg.transient(self); dlg.grab_set()
        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)

    def _do_logout(self, dlg: tk.Toplevel):
        dlg.destroy()
        self.state.current_user = None
        self.show_login()
        self.show_banner("info", "Logged out.")

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()