import json
import random
import re
import threading
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

import requests


API_BASE = "https://swapi.info/api/"
LEGACY_API_BASES = (
    "https://swapi.dev/api",
    "https://swapi.co/api",
    "https://swapi.py4e.com/api",
)
CACHE_PATH = Path.home() / ".starwars_databank_cache.json"
FAVORITES_PATH = Path.home() / ".starwars_databank_favorites.json"
RESOURCES = ("people", "planets", "species", "films", "vehicles", "starships")

COLORS = {
    "bg": "#111318",
    "panel": "#181c23",
    "panel_alt": "#202632",
    "line": "#303846",
    "text": "#f5f1dc",
    "muted": "#aeb6c2",
    "accent": "#f2c94c",
    "accent_hover": "#ffe07a",
    "warning": "#ff8a65",
    "input": "#0f1217",
    "selected": "#31445d",
}


def title_case(value):
    value = clean_value(value)
    if value in {"n/a", "unknown"}:
        return value.upper() if value == "n/a" else "Unknown"
    return value.title()


def clean_value(value, fallback="Unknown"):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def normalize_url(url):
    text = clean_value(url, "").replace("http://", "https://").rstrip("/")
    for legacy_base in LEGACY_API_BASES:
        if text.startswith(legacy_base):
            return f"{API_BASE.rstrip('/')}{text[len(legacy_base):]}"
    return text


def display_name(item):
    return clean_value(item.get("title") or item.get("name"))


def extract_id(url):
    match = re.search(r"/(\d+)/?$", normalize_url(url))
    return match.group(1) if match else ""


def parse_number(value):
    text = clean_value(value, "").replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def birth_year_key(value):
    text = clean_value(value, "").upper()
    match = re.match(r"(\d+(?:\.\d+)?)\s*(BBY|ABY)", text)
    if not match:
        return None
    year = float(match.group(1))
    return -year if match.group(2) == "BBY" else year


def format_birth_year(value):
    text = clean_value(value)
    match = re.match(r"(\d+(?:\.\d+)?)\s*(BBY|ABY)", text.upper())
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return title_case(text)


def format_height(value):
    height = parse_number(value)
    if height is None:
        return title_case(value)
    inches = height / 2.54
    feet = int(inches // 12)
    remaining_inches = round(inches - feet * 12)
    return f"{height:g} cm ({feet} ft {remaining_inches} in)"


def format_mass(value):
    mass = parse_number(value)
    return f"{mass:g} kg" if mass is not None else title_case(value)


class StarWarsDataBank:
    def __init__(self, root):
        self.root = root
        self.catalogs = {name: [] for name in RESOURCES}
        self.people_by_url = {}
        self.label_by_url = {}
        self.current_person = None
        self.loading = False
        self.favorites = self.load_favorites()

        self.search_var = tk.StringVar()
        self.gender_var = tk.StringVar(value="All genders")
        self.sort_var = tk.StringVar(value="Name")
        self.favorites_only_var = tk.BooleanVar(value=False)
        self.stay_on_top_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Starting data link...")
        self.count_var = tk.StringVar(value="0 records")
        self.name_var = tk.StringVar(value="Loading...")
        self.meta_var = tk.StringVar(value="")
        self.favorite_button_var = tk.StringVar(value="Favorite")

        self.field_vars = {
            "Height": tk.StringVar(value="..."),
            "Mass": tk.StringVar(value="..."),
            "Hair": tk.StringVar(value="..."),
            "Skin": tk.StringVar(value="..."),
            "Eyes": tk.StringVar(value="..."),
            "Birth": tk.StringVar(value="..."),
            "Gender": tk.StringVar(value="..."),
            "Homeworld": tk.StringVar(value="..."),
            "Species": tk.StringVar(value="..."),
            "Films": tk.StringVar(value="..."),
            "Vehicles": tk.StringVar(value="..."),
            "Starships": tk.StringVar(value="..."),
        }

        self.configure_window()
        self.configure_styles()
        self.build_menu()
        self.build_layout()
        self.bind_events()
        self.load_data()

    def configure_window(self):
        self.root.title("Star Wars DataBank")
        self.root.geometry("1080x680+420+160")
        self.root.minsize(920, 560)
        self.root.configure(bg=COLORS["bg"])
        self.root.attributes("-topmost", True)
        try:
            self.root.iconbitmap("favicon.ico")
        except tk.TclError:
            pass

    def configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("App.TFrame", background=COLORS["bg"])
        style.configure("Panel.TFrame", background=COLORS["panel"])
        style.configure("PanelAlt.TFrame", background=COLORS["panel_alt"])
        style.configure(
            "Title.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            font=("Segoe UI", 22, "bold"),
        )
        style.configure(
            "Eyebrow.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["accent"],
            font=("Segoe UI", 9, "bold"),
        )
        style.configure(
            "PanelTitle.TLabel",
            background=COLORS["panel"],
            foreground=COLORS["text"],
            font=("Segoe UI", 13, "bold"),
        )
        style.configure(
            "Name.TLabel",
            background=COLORS["panel"],
            foreground=COLORS["text"],
            font=("Segoe UI", 26, "bold"),
        )
        style.configure(
            "Meta.TLabel",
            background=COLORS["panel"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "FieldLabel.TLabel",
            background=COLORS["panel"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "FieldValue.TLabel",
            background=COLORS["panel"],
            foreground=COLORS["text"],
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Status.TLabel",
            background=COLORS["panel_alt"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "TButton",
            background=COLORS["panel_alt"],
            foreground=COLORS["text"],
            bordercolor=COLORS["line"],
            focusthickness=0,
            focuscolor=COLORS["line"],
            padding=(14, 8),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "TButton",
            background=[("active", COLORS["selected"]), ("pressed", COLORS["selected"])],
            foreground=[("active", COLORS["accent_hover"])],
        )
        style.configure(
            "Accent.TButton",
            background=COLORS["accent"],
            foreground="#141414",
            bordercolor=COLORS["accent"],
        )
        style.map(
            "Accent.TButton",
            background=[("active", COLORS["accent_hover"]), ("pressed", COLORS["accent"])],
            foreground=[("active", "#141414")],
        )
        style.configure(
            "TCheckbutton",
            background=COLORS["panel"],
            foreground=COLORS["text"],
            font=("Segoe UI", 10),
        )
        style.map(
            "TCheckbutton",
            background=[("active", COLORS["panel"])],
            foreground=[("active", COLORS["accent_hover"])],
        )
        style.configure(
            "TEntry",
            fieldbackground=COLORS["input"],
            foreground=COLORS["text"],
            insertcolor=COLORS["accent"],
            bordercolor=COLORS["line"],
            lightcolor=COLORS["line"],
            darkcolor=COLORS["line"],
            padding=8,
        )
        style.configure(
            "TCombobox",
            fieldbackground=COLORS["input"],
            background=COLORS["panel_alt"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["accent"],
            bordercolor=COLORS["line"],
            padding=7,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLORS["input"])],
            foreground=[("readonly", COLORS["text"])],
        )
        style.configure(
            "Treeview",
            background=COLORS["panel"],
            fieldbackground=COLORS["panel"],
            foreground=COLORS["text"],
            borderwidth=0,
            rowheight=30,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["panel_alt"],
            foreground=COLORS["accent"],
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        )
        style.map(
            "Treeview",
            background=[("selected", COLORS["selected"])],
            foreground=[("selected", COLORS["text"])],
        )

    def build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New random", command=self.pick_random)
        file_menu.add_command(label="Refresh data", command=lambda: self.load_data(force=True))
        file_menu.add_separator()
        file_menu.add_command(label="Copy summary", command=self.copy_summary)
        file_menu.add_command(label="Open API record", command=self.open_api_record)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.close_app)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_checkbutton(
            label="Stay on top",
            variable=self.stay_on_top_var,
            command=self.toggle_stay_on_top,
        )
        view_menu.add_checkbutton(
            label="Favorites only",
            variable=self.favorites_only_var,
            command=self.apply_filters,
        )

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(
            label="SWAPI documentation",
            command=lambda: webbrowser.open("https://swapi.info/documentation"),
        )

        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="View", menu=view_menu)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)

        self.popup = tk.Menu(self.root, tearoff=0)
        self.popup.add_command(label="New random", command=self.pick_random)
        self.popup.add_command(label="Toggle favorite", command=self.toggle_favorite)
        self.popup.add_command(label="Copy summary", command=self.copy_summary)
        self.popup.add_separator()
        self.popup.add_command(label="Exit", command=self.close_app)

    def build_layout(self):
        shell = ttk.Frame(self.root, style="App.TFrame", padding=18)
        shell.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        shell.columnconfigure(0, weight=0, minsize=360)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(1, weight=1)

        header = ttk.Frame(shell, style="App.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="SWAPI CATALOG", style="Eyebrow.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(header, text="Star Wars DataBank", style="Title.TLabel").grid(
            row=1, column=0, sticky="w"
        )

        header_actions = ttk.Frame(header, style="App.TFrame")
        header_actions.grid(row=0, column=1, rowspan=2, sticky="e")
        ttk.Button(
            header_actions,
            text="Random",
            style="Accent.TButton",
            command=self.pick_random,
        ).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(header_actions, text="Refresh", command=lambda: self.load_data(force=True)).grid(
            row=0, column=1, padx=(0, 8)
        )
        ttk.Button(header_actions, text="Exit", command=self.close_app).grid(row=0, column=2)

        sidebar = ttk.Frame(shell, style="Panel.TFrame", padding=14)
        sidebar.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(3, weight=1)

        ttk.Label(sidebar, text="Character Index", style="PanelTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        search_entry = ttk.Entry(sidebar, textvariable=self.search_var)
        search_entry.grid(row=1, column=0, sticky="ew", pady=(12, 8))
        search_entry.insert(0, "")

        filters = ttk.Frame(sidebar, style="Panel.TFrame")
        filters.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        filters.columnconfigure(0, weight=1)
        filters.columnconfigure(1, weight=1)

        self.gender_combo = ttk.Combobox(
            filters,
            textvariable=self.gender_var,
            values=("All genders", "Female", "Male", "Hermaphrodite", "N/A", "Unknown"),
            state="readonly",
        )
        self.gender_combo.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.sort_combo = ttk.Combobox(
            filters,
            textvariable=self.sort_var,
            values=("Name", "Height", "Mass", "Birth year", "Film count"),
            state="readonly",
        )
        self.sort_combo.grid(row=0, column=1, sticky="ew")

        fav_row = ttk.Frame(sidebar, style="Panel.TFrame")
        fav_row.grid(row=3, column=0, sticky="nsew")
        fav_row.columnconfigure(0, weight=1)
        fav_row.rowconfigure(1, weight=1)
        ttk.Checkbutton(
            fav_row,
            text="Favorites only",
            variable=self.favorites_only_var,
            command=self.apply_filters,
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(fav_row, textvariable=self.count_var, style="Meta.TLabel").grid(
            row=0, column=1, sticky="e", pady=(0, 8)
        )

        self.tree = ttk.Treeview(
            fav_row,
            columns=("gender", "height"),
            show="tree headings",
            selectmode="browse",
        )
        self.tree.heading("#0", text="Name")
        self.tree.heading("gender", text="Gender")
        self.tree.heading("height", text="Height")
        self.tree.column("#0", width=190, minwidth=150, stretch=True)
        self.tree.column("gender", width=92, minwidth=80, stretch=False)
        self.tree.column("height", width=78, minwidth=70, stretch=False, anchor="e")
        self.tree.grid(row=1, column=0, columnspan=2, sticky="nsew")

        scrollbar = ttk.Scrollbar(fav_row, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=2, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        detail = ttk.Frame(shell, style="Panel.TFrame", padding=18)
        detail.grid(row=1, column=1, sticky="nsew")
        detail.columnconfigure(0, weight=1)
        detail.rowconfigure(4, weight=1)

        detail_top = ttk.Frame(detail, style="Panel.TFrame")
        detail_top.grid(row=0, column=0, sticky="ew")
        detail_top.columnconfigure(0, weight=1)
        ttk.Label(detail_top, textvariable=self.name_var, style="Name.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(detail_top, textvariable=self.meta_var, style="Meta.TLabel").grid(
            row=1, column=0, sticky="w", pady=(3, 0)
        )

        detail_actions = ttk.Frame(detail_top, style="Panel.TFrame")
        detail_actions.grid(row=0, column=1, rowspan=2, sticky="e")
        ttk.Button(detail_actions, text="Previous", command=self.select_previous).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(detail_actions, text="Next", command=self.select_next).grid(
            row=0, column=1, padx=(0, 8)
        )
        ttk.Button(
            detail_actions,
            textvariable=self.favorite_button_var,
            command=self.toggle_favorite,
        ).grid(row=0, column=2)

        stats = ttk.Frame(detail, style="Panel.TFrame")
        stats.grid(row=1, column=0, sticky="ew", pady=(20, 12))
        for column in range(4):
            stats.columnconfigure(column, weight=1)
        for index, field in enumerate(("Height", "Mass", "Birth", "Gender")):
            self.build_metric(stats, field, index)

        profile = ttk.Frame(detail, style="Panel.TFrame")
        profile.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        for column in range(3):
            profile.columnconfigure(column, weight=1)
        for index, field in enumerate(("Hair", "Skin", "Eyes", "Homeworld", "Species", "Films")):
            self.build_profile_field(profile, field, index)

        media_frame = ttk.Frame(detail, style="Panel.TFrame")
        media_frame.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        media_frame.columnconfigure(0, weight=1)
        media_frame.columnconfigure(1, weight=1)
        self.vehicles_text = self.build_related_box(media_frame, "Vehicles", 0)
        self.starships_text = self.build_related_box(media_frame, "Starships", 1)

        film_frame = ttk.Frame(detail, style="Panel.TFrame")
        film_frame.grid(row=4, column=0, sticky="nsew")
        film_frame.columnconfigure(0, weight=1)
        film_frame.rowconfigure(1, weight=1)
        ttk.Label(film_frame, text="Film Appearances", style="PanelTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        self.films_text = tk.Text(
            film_frame,
            height=7,
            wrap="word",
            bg=COLORS["input"],
            fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            relief="flat",
            padx=12,
            pady=10,
            font=("Segoe UI", 10),
        )
        self.films_text.grid(row=1, column=0, sticky="nsew")
        self.films_text.configure(state="disabled")

        bottom = ttk.Frame(shell, style="PanelAlt.TFrame", padding=(12, 8))
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        bottom.columnconfigure(0, weight=1)
        ttk.Label(bottom, textvariable=self.status_var, style="Status.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(bottom, text="Copy", command=self.copy_summary).grid(
            row=0, column=1, padx=(8, 0)
        )
        ttk.Button(bottom, text="API", command=self.open_api_record).grid(
            row=0, column=2, padx=(8, 0)
        )

    def build_metric(self, parent, field, column):
        frame = ttk.Frame(parent, style="PanelAlt.TFrame", padding=12)
        frame.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
        ttk.Label(
            frame,
            text=field.upper(),
            background=COLORS["panel_alt"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 8, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            frame,
            textvariable=self.field_vars[field],
            background=COLORS["panel_alt"],
            foreground=COLORS["text"],
            font=("Segoe UI", 12, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    def build_profile_field(self, parent, field, index):
        row = index // 3
        column = index % 3
        frame = ttk.Frame(parent, style="Panel.TFrame")
        frame.grid(row=row, column=column, sticky="ew", padx=(0 if column == 0 else 14, 0), pady=8)
        ttk.Label(frame, text=field, style="FieldLabel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.field_vars[field], style="FieldValue.TLabel").grid(
            row=1, column=0, sticky="w", pady=(2, 0)
        )

    def build_related_box(self, parent, label, column):
        frame = ttk.Frame(parent, style="Panel.TFrame")
        frame.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 12, 0))
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=label, style="PanelTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        text = tk.Text(
            frame,
            height=4,
            wrap="word",
            bg=COLORS["input"],
            fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            relief="flat",
            padx=12,
            pady=10,
            font=("Segoe UI", 10),
        )
        text.grid(row=1, column=0, sticky="ew")
        text.configure(state="disabled")
        return text

    def bind_events(self):
        self.search_var.trace_add("write", lambda *_: self.apply_filters())
        self.gender_combo.bind("<<ComboboxSelected>>", lambda _event: self.apply_filters())
        self.sort_combo.bind("<<ComboboxSelected>>", lambda _event: self.apply_filters())
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.root.bind("<Button-3>", self.show_popup)
        self.root.bind("<Control-r>", lambda _event: self.pick_random())
        self.root.bind("<Control-f>", lambda _event: self.focus_search())
        self.root.bind("<Escape>", lambda _event: self.search_var.set(""))

    def focus_search(self):
        self.root.focus_get()
        for child in self.root.winfo_children():
            self.focus_first_entry(child)

    def focus_first_entry(self, widget):
        if isinstance(widget, ttk.Entry):
            widget.focus_set()
            widget.selection_range(0, tk.END)
            return True
        for child in widget.winfo_children():
            if self.focus_first_entry(child):
                return True
        return False

    def load_favorites(self):
        try:
            return set(json.loads(FAVORITES_PATH.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, TypeError):
            return set()

    def save_favorites(self):
        try:
            FAVORITES_PATH.write_text(
                json.dumps(sorted(self.favorites), indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            self.status_var.set(f"Could not save favorites: {exc}")

    def load_data(self, force=False):
        if self.loading:
            return
        self.loading = True
        self.status_var.set("Loading SWAPI records...")
        self.set_controls_enabled(False)

        if not force:
            cached = self.read_cache()
            if cached:
                self.apply_catalogs(cached, source="cache")
                self.loading = True
                self.status_var.set("Loaded cached records. Refresh data to pull the latest SWAPI data.")

        thread = threading.Thread(target=self.fetch_catalogs, daemon=True)
        thread.start()

    def read_cache(self):
        try:
            payload = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        catalogs = payload.get("catalogs")
        if not isinstance(catalogs, dict) or not catalogs.get("people"):
            return None
        return catalogs

    def write_cache(self, catalogs):
        payload = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "catalogs": catalogs,
        }
        try:
            CACHE_PATH.write_text(json.dumps(payload), encoding="utf-8")
        except OSError:
            pass

    def fetch_catalogs(self):
        try:
            session = requests.Session()
            session.headers.update({"User-Agent": "StarWarsDataBank/2.0"})
            catalogs = {
                resource: self.fetch_all(session, f"{API_BASE}{resource}/")
                for resource in RESOURCES
            }
            self.write_cache(catalogs)
            self.root.after(0, lambda: self.apply_catalogs(catalogs, source="live"))
        except (requests.RequestException, ValueError, TypeError) as exc:
            self.root.after(0, lambda: self.handle_load_error(exc))

    def fetch_all(self, session, url):
        results = []
        next_url = url
        while next_url:
            response = session.get(next_url, timeout=12)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, list):
                results.extend(payload)
                next_url = None
            else:
                results.extend(payload.get("results", []))
                next_url = payload.get("next")
        return results

    def apply_catalogs(self, catalogs, source):
        self.catalogs = {name: list(catalogs.get(name, [])) for name in RESOURCES}
        self.people_by_url = {
            normalize_url(person.get("url")): person for person in self.catalogs["people"]
        }
        self.label_by_url = {}
        for resource in RESOURCES:
            for item in self.catalogs[resource]:
                self.label_by_url[normalize_url(item.get("url"))] = display_name(item)

        self.loading = False
        self.set_controls_enabled(True)
        self.apply_filters(keep_selection=True)
        total = len(self.catalogs["people"])
        if source == "live":
            self.status_var.set(f"Loaded {total} live SWAPI character records.")
        elif not self.current_person and total:
            self.pick_random()

    def handle_load_error(self, exc):
        self.loading = False
        self.set_controls_enabled(True)
        if self.catalogs["people"]:
            self.status_var.set(f"Using cached data. Live refresh failed: {exc}")
            return
        self.status_var.set(f"Could not load SWAPI data: {exc}")
        messagebox.showerror("Star Wars DataBank", f"Could not load SWAPI data:\n\n{exc}")

    def set_controls_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        readonly = "readonly" if enabled else "disabled"
        for widget in self.root.winfo_children():
            self.set_widget_state(widget, state, readonly)

    def set_widget_state(self, widget, state, readonly):
        if isinstance(widget, ttk.Combobox):
            widget.configure(state=readonly)
        elif isinstance(widget, ttk.Button):
            widget.configure(state=state)
        for child in widget.winfo_children():
            self.set_widget_state(child, state, readonly)

    def apply_filters(self, keep_selection=False):
        selected_url = None
        if keep_selection and self.tree.selection():
            selected_url = self.tree.selection()[0]

        people = list(self.catalogs["people"])
        term = self.search_var.get().strip().casefold()
        gender = self.gender_var.get()

        if self.favorites_only_var.get():
            people = [person for person in people if normalize_url(person.get("url")) in self.favorites]

        if gender != "All genders":
            gender_key = gender.casefold()
            people = [
                person
                for person in people
                if title_case(person.get("gender")).casefold() == gender_key
            ]

        if term:
            people = [person for person in people if term in self.search_text(person)]

        people.sort(key=self.sort_key)
        self.populate_tree(people, selected_url=selected_url)

    def search_text(self, person):
        values = [
            person.get("name"),
            person.get("gender"),
            person.get("birth_year"),
            self.resolve_one(person.get("homeworld")),
            self.resolve_many(person.get("species")),
            self.resolve_many(person.get("films")),
        ]
        return " ".join(clean_value(value, "") for value in values).casefold()

    def sort_key(self, person):
        sort = self.sort_var.get()
        name = clean_value(person.get("name")).casefold()
        if sort == "Height":
            value = parse_number(person.get("height"))
            return (value is None, value or 0, name)
        if sort == "Mass":
            value = parse_number(person.get("mass"))
            return (value is None, value or 0, name)
        if sort == "Birth year":
            value = birth_year_key(person.get("birth_year"))
            return (value is None, value or 0, name)
        if sort == "Film count":
            return (-len(person.get("films", [])), name)
        return (name,)

    def populate_tree(self, people, selected_url=None):
        self.tree.delete(*self.tree.get_children())
        for person in people:
            url = normalize_url(person.get("url"))
            name = clean_value(person.get("name"))
            if url in self.favorites:
                name = f"* {name}"
            self.tree.insert(
                "",
                tk.END,
                iid=url,
                text=name,
                values=(title_case(person.get("gender")), clean_value(person.get("height"))),
            )

        count = len(people)
        self.count_var.set(f"{count} record{'s' if count != 1 else ''}")

        if selected_url and self.tree.exists(selected_url):
            self.select_tree_item(selected_url)
            return

        children = self.tree.get_children()
        if children:
            self.select_tree_item(children[0])
        else:
            self.current_person = None
            self.render_empty_state()

    def on_tree_select(self, _event):
        selection = self.tree.selection()
        if not selection:
            return
        self.current_person = self.people_by_url.get(selection[0])
        if self.current_person:
            self.render_person(self.current_person)

    def render_empty_state(self):
        self.name_var.set("No records")
        self.meta_var.set("Adjust search or filters")
        for var in self.field_vars.values():
            var.set("...")
        self.favorite_button_var.set("Favorite")
        self.write_text(self.vehicles_text, "")
        self.write_text(self.starships_text, "")
        self.write_text(self.films_text, "")

    def render_person(self, person):
        url = normalize_url(person.get("url"))
        person_id = extract_id(url)
        homeworld = self.resolve_one(person.get("homeworld"))
        species = self.resolve_many(person.get("species")) or "Human"
        films = self.resolve_many(person.get("films"))
        vehicles = self.resolve_many(person.get("vehicles")) or "None listed"
        starships = self.resolve_many(person.get("starships")) or "None listed"

        self.name_var.set(clean_value(person.get("name")))
        self.meta_var.set(f"Record {person_id} | {homeworld}")
        self.field_vars["Height"].set(format_height(person.get("height")))
        self.field_vars["Mass"].set(format_mass(person.get("mass")))
        self.field_vars["Hair"].set(title_case(person.get("hair_color")))
        self.field_vars["Skin"].set(title_case(person.get("skin_color")))
        self.field_vars["Eyes"].set(title_case(person.get("eye_color")))
        self.field_vars["Birth"].set(format_birth_year(person.get("birth_year")))
        self.field_vars["Gender"].set(title_case(person.get("gender")))
        self.field_vars["Homeworld"].set(homeworld)
        self.field_vars["Species"].set(species)
        self.field_vars["Films"].set(str(len(person.get("films", []))))
        self.field_vars["Vehicles"].set(str(len(person.get("vehicles", []))))
        self.field_vars["Starships"].set(str(len(person.get("starships", []))))
        self.favorite_button_var.set("Unfavorite" if url in self.favorites else "Favorite")
        self.write_text(self.vehicles_text, vehicles)
        self.write_text(self.starships_text, starships)
        self.write_text(self.films_text, films or "None listed")

    def resolve_one(self, url):
        return self.label_by_url.get(normalize_url(url), "Unknown")

    def resolve_many(self, urls):
        values = [self.resolve_one(url) for url in urls or []]
        values = [value for value in values if value and value != "Unknown"]
        return "\n".join(values)

    def write_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def pick_random(self):
        children = self.tree.get_children()
        if not children:
            return
        selected = random.choice(children)
        self.select_tree_item(selected)
        self.status_var.set("Random character selected.")

    def select_next(self):
        self.move_selection(1)

    def select_previous(self):
        self.move_selection(-1)

    def move_selection(self, direction):
        children = self.tree.get_children()
        if not children:
            return
        selection = self.tree.selection()
        if not selection:
            target = children[0]
        else:
            index = children.index(selection[0])
            target = children[(index + direction) % len(children)]
        self.select_tree_item(target)

    def select_tree_item(self, item_id):
        self.tree.selection_set(item_id)
        self.tree.see(item_id)
        person = self.people_by_url.get(item_id)
        if person:
            self.current_person = person
            self.render_person(person)

    def toggle_favorite(self):
        if not self.current_person:
            return
        url = normalize_url(self.current_person.get("url"))
        name = clean_value(self.current_person.get("name"))
        if url in self.favorites:
            self.favorites.remove(url)
            self.status_var.set(f"Removed {name} from favorites.")
        else:
            self.favorites.add(url)
            self.status_var.set(f"Added {name} to favorites.")
        self.save_favorites()
        self.apply_filters(keep_selection=True)
        if self.current_person and normalize_url(self.current_person.get("url")) == url:
            self.render_person(self.current_person)

    def copy_summary(self):
        if not self.current_person:
            return
        summary = self.build_summary(self.current_person)
        self.root.clipboard_clear()
        self.root.clipboard_append(summary)
        self.status_var.set("Character summary copied to clipboard.")

    def build_summary(self, person):
        fields = [
            ("Name", clean_value(person.get("name"))),
            ("Height", format_height(person.get("height"))),
            ("Mass", format_mass(person.get("mass"))),
            ("Birth year", format_birth_year(person.get("birth_year"))),
            ("Gender", title_case(person.get("gender"))),
            ("Homeworld", self.resolve_one(person.get("homeworld"))),
            ("Species", self.resolve_many(person.get("species")) or "Human"),
            ("Films", self.resolve_many(person.get("films")) or "None listed"),
        ]
        return "\n".join(f"{label}: {value}" for label, value in fields)

    def open_api_record(self):
        if not self.current_person:
            return
        webbrowser.open(normalize_url(self.current_person.get("url")))

    def toggle_stay_on_top(self):
        self.root.attributes("-topmost", self.stay_on_top_var.get())

    def show_popup(self, event):
        try:
            self.popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup.grab_release()

    def close_app(self):
        self.root.destroy()


def main():
    window = tk.Tk()
    StarWarsDataBank(window)
    window.mainloop()


if __name__ == "__main__":
    main()
