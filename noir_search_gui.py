from __future__ import annotations

import json
import logging
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

import noir_search as core

COLORS = {
    "page": "#050505",
    "page_alt": "#090909",
    "header": "#0A0A0A",
    "card": "#101010",
    "card_alt": "#141414",
    "card_soft": "#191919",
    "ink": "#F2F2F2",
    "muted": "#9A9A9A",
    "accent": "#FFFFFF",
    "accent_dark": "#D6D6D6",
    "accent_secondary": "#B8B8B8",
    "teal": "#E6E6E6",
    "sand": "#151515",
    "line": "#262626",
    "success": "#FFFFFF",
    "warning": "#D0D0D0",
    "danger": "#9A9A9A",
    "console": "#020202",
    "console_text": "#F5F5F5",
    "console_dim": "#8C8C8C",
}

FONTS = {
    "title": ("Bahnschrift", 30, "bold"),
    "subtitle": ("Segoe UI", 11),
    "section": ("Bahnschrift", 12, "bold"),
    "label": ("Bahnschrift SemiBold", 10),
    "body": ("Segoe UI", 10),
    "mono": ("Consolas", 10),
    "badge": ("Bahnschrift SemiBold", 9),
    "micro": ("Segoe UI", 9),
}


class QueueLogHandler(logging.Handler):
    def __init__(self, event_queue: queue.Queue):
        super().__init__()
        self.event_queue = event_queue

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
        except Exception:
            message = record.getMessage()
        self.event_queue.put(("log", record.levelname.lower(), message))


class AutomationStudio:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.runtime_base_path = core.resolve_runtime_base_path()
        self.resource_base_path = core.resolve_resource_base_path()
        self.event_queue: queue.Queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker_thread: threading.Thread | None = None

        self.config_path_var = tk.StringVar()
        self.queries_path_var = tk.StringVar()
        self.log_path_var = tk.StringVar()
        self.start_url_var = tk.StringVar(value=core.DEFAULT_START_URL)
        self.delay_var = tk.StringVar(value=str(core.DEFAULT_DELAY_SECONDS))
        self.keep_open_var = tk.StringVar(value=str(core.DEFAULT_KEEP_OPEN_SECONDS))
        self.timeout_var = tk.StringVar(value=str(core.DEFAULT_TIMEOUT_SECONDS))
        self.headless_var = tk.BooleanVar(value=False)
        self.query_info_var = tk.StringVar(value="5 busca(s)")
        self.summary_var = tk.StringVar(value="Pronto")
        self.current_item_var = tk.StringVar(value="")

        self.status_badge: tk.Label | None = None
        self.start_button: ttk.Button | None = None
        self.dry_run_button: ttk.Button | None = None
        self.stop_button: ttk.Button | None = None
        self.progress_bar: ttk.Progressbar | None = None
        self.preview_list: tk.Listbox | None = None
        self.log_output: ScrolledText | None = None

        self._configure_window()
        self._configure_style()
        self._build_layout()
        self._load_initial_state()
        self._refresh_query_preview()
        self.root.after(120, self._process_event_queue)

    def _configure_window(self) -> None:
        self.root.title("Noir Search Studio")
        self.root.geometry("1260x820")
        self.root.minsize(1120, 720)
        self.root.configure(bg=COLORS["page"])

    def _configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Accent.TButton",
            font=FONTS["label"],
            padding=(16, 11),
            foreground="#050505",
            background=COLORS["accent"],
            borderwidth=0,
        )
        style.map(
            "Accent.TButton",
            background=[("active", COLORS["accent_dark"]), ("disabled", COLORS["line"])],
            foreground=[("disabled", "#A9C8D3")],
        )

        style.configure(
            "Ghost.TButton",
            font=FONTS["label"],
            padding=(12, 10),
            foreground=COLORS["ink"],
            background=COLORS["card_soft"],
            borderwidth=1,
            relief="solid",
        )
        style.map(
            "Ghost.TButton",
            background=[("active", "#202020"), ("disabled", COLORS["line"])],
        )

        style.configure(
            "Danger.TButton",
            font=FONTS["label"],
            padding=(12, 10),
            foreground="white",
            background=COLORS["danger"],
            borderwidth=0,
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#6F6F6F"), ("disabled", COLORS["line"])],
        )

        style.configure(
            "Studio.Horizontal.TProgressbar",
            troughcolor=COLORS["sand"],
            bordercolor=COLORS["sand"],
            background=COLORS["accent"],
            lightcolor=COLORS["accent"],
            darkcolor=COLORS["teal"],
            thickness=16,
        )

    def _build_layout(self) -> None:
        header = tk.Frame(self.root, bg=COLORS["header"], height=124)
        header.pack(fill="x", padx=24, pady=(22, 18))
        header.pack_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title_wrap = tk.Frame(header, bg=COLORS["header"])
        title_wrap.grid(row=0, column=0, sticky="nw", padx=26, pady=(20, 10))

        tk.Label(
            title_wrap,
            text="Noir Search Studio",
            font=FONTS["title"],
            bg=COLORS["header"],
            fg="white",
        ).pack(anchor="w")
        tk.Label(
            title_wrap,
            text="Automacao de pesquisa para o sistema de recompensa Bing.",
            font=FONTS["subtitle"],
            bg=COLORS["header"],
            fg=COLORS["muted"],
        ).pack(anchor="w", pady=(8, 0))

        hero = tk.Canvas(
            header,
            width=340,
            height=84,
            bg=COLORS["header"],
            highlightthickness=0,
        )
        hero.grid(row=0, column=1, sticky="e", padx=24, pady=18)
        self._paint_header_visual(hero)

        content = tk.Frame(self.root, bg=COLORS["page"])
        content.pack(fill="both", expand=True, padx=24, pady=(0, 22))
        content.grid_columnconfigure(0, weight=0)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        controls_card, controls = self._create_card(content, "Controle da Automacao", width=390)
        controls_card.grid(row=0, column=0, sticky="nsw", padx=(0, 18))
        controls_card.grid_propagate(False)

        dashboard_card, dashboard = self._create_card(content, "Painel de Execucao")
        dashboard_card.grid(row=0, column=1, sticky="nsew")
        dashboard.grid_columnconfigure(0, weight=1)
        dashboard.grid_rowconfigure(3, weight=1)

        self._build_controls(controls)
        self._build_dashboard(dashboard)

    def _create_card(self, parent: tk.Widget, title: str, width: int | None = None) -> tuple[tk.Frame, tk.Frame]:
        card = tk.Frame(parent, bg=COLORS["card"])
        if width is not None:
            card.configure(width=width)

        tk.Frame(card, bg=COLORS["line"], height=1).pack(fill="x")

        tk.Label(
            card,
            text=title.upper(),
            font=FONTS["section"],
            bg=COLORS["card"],
            fg=COLORS["accent"],
        ).pack(anchor="w", padx=18, pady=(18, 8))

        body = tk.Frame(card, bg=COLORS["card"])
        body.pack(fill="both", expand=True)
        return card, body

    def _paint_header_visual(self, canvas: tk.Canvas) -> None:
        width = 340
        height = 84
        for x in range(0, width + 1, 22):
            canvas.create_line(x, 0, x, height, fill="#171717")
        for y in range(0, height + 1, 22):
            canvas.create_line(0, y, width, y, fill="#171717")

        canvas.create_arc(18, 8, 148, 82, start=8, extent=286, style="arc", outline=COLORS["accent"], width=2)
        canvas.create_arc(194, 8, 324, 82, start=190, extent=286, style="arc", outline=COLORS["accent_secondary"], width=2)
        canvas.create_line(40, 64, 78, 42, 112, 50, 136, 28, fill=COLORS["accent"], width=3, smooth=True)
        canvas.create_line(206, 58, 234, 34, 264, 44, 312, 22, fill=COLORS["accent_secondary"], width=3, smooth=True)
        canvas.create_oval(84, 22, 96, 34, fill=COLORS["accent"], outline="")
        canvas.create_oval(254, 22, 266, 34, fill=COLORS["accent_secondary"], outline="")

    def _build_controls(self, parent: tk.Frame) -> None:
        body = tk.Frame(parent, bg=COLORS["card"])
        body.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        body.grid_columnconfigure(0, weight=1)

        self._add_path_field(
            body,
            row=0,
            label="Arquivo de configuracao",
            variable=self.config_path_var,
            browse_command=self._browse_config_file,
            button_text="Abrir",
        )
        self._add_path_field(
            body,
            row=1,
            label="Arquivo de buscas",
            variable=self.queries_path_var,
            browse_command=self._browse_queries_file,
            button_text="Escolher",
        )
        self._add_path_field(
            body,
            row=2,
            label="Arquivo de log",
            variable=self.log_path_var,
            browse_command=self._browse_log_file,
            button_text="Salvar em",
        )

        self._add_input_field(body, row=3, label="URL inicial", variable=self.start_url_var)

        metrics = tk.Frame(body, bg=COLORS["card"])
        metrics.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        for column in range(3):
            metrics.grid_columnconfigure(column, weight=1)

        self._add_metric_field(metrics, 0, "Delay (s)", self.delay_var)
        self._add_metric_field(metrics, 1, "Timeout (s)", self.timeout_var)
        self._add_metric_field(metrics, 2, "Fim aberto (s)", self.keep_open_var)

        check_wrap = tk.Frame(body, bg=COLORS["card"])
        check_wrap.grid(row=5, column=0, sticky="w", pady=(16, 0))
        tk.Checkbutton(
            check_wrap,
            text="Executar em segundo plano (headless)",
            variable=self.headless_var,
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["ink"],
            activebackground=COLORS["card"],
            activeforeground=COLORS["ink"],
            selectcolor=COLORS["card_alt"],
            highlightthickness=0,
            bd=0,
            relief="flat",
        ).pack(anchor="w")

        info_box = tk.Frame(body, bg=COLORS["card_soft"])
        info_box.grid(row=6, column=0, sticky="ew", pady=(18, 0))
        tk.Label(
            info_box,
            textvariable=self.query_info_var,
            justify="left",
            wraplength=310,
            font=FONTS["body"],
            bg=COLORS["card_soft"],
            fg=COLORS["muted"],
        ).pack(anchor="w", padx=14, pady=12)

        button_row = tk.Frame(body, bg=COLORS["card"])
        button_row.grid(row=7, column=0, sticky="ew", pady=(18, 0))
        for column in range(2):
            button_row.grid_columnconfigure(column, weight=1)

        ttk.Button(
            button_row,
            text="Carregar JSON",
            style="Ghost.TButton",
            command=self._load_config_from_dialog,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(
            button_row,
            text="Salvar JSON",
            style="Ghost.TButton",
            command=self._save_config_to_disk,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _build_dashboard(self, parent: tk.Frame) -> None:
        summary_row = tk.Frame(parent, bg=COLORS["card"])
        summary_row.grid(row=0, column=0, sticky="ew", padx=18)
        summary_row.grid_columnconfigure(0, weight=1)

        summary_text = tk.Frame(summary_row, bg=COLORS["card"])
        summary_text.grid(row=0, column=0, sticky="w")

        tk.Label(
            summary_text,
            textvariable=self.summary_var,
            font=("Bahnschrift", 15, "bold"),
            bg=COLORS["card"],
            fg=COLORS["ink"],
        ).pack(anchor="w")
        tk.Label(
            summary_text,
            textvariable=self.current_item_var,
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["muted"],
        ).pack(anchor="w", pady=(4, 0))

        self.status_badge = tk.Label(
            summary_row,
            text="Pronto",
            font=FONTS["badge"],
            bg=COLORS["card_alt"],
            fg=COLORS["accent"],
            padx=14,
            pady=8,
        )
        self.status_badge.grid(row=0, column=1, sticky="e")

        progress_wrap = tk.Frame(parent, bg=COLORS["card"])
        progress_wrap.grid(row=1, column=0, sticky="ew", padx=18, pady=(16, 0))
        progress_wrap.grid_columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(
            progress_wrap,
            mode="determinate",
            maximum=1,
            value=0,
            style="Studio.Horizontal.TProgressbar",
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew")

        action_row = tk.Frame(parent, bg=COLORS["card"])
        action_row.grid(row=2, column=0, sticky="ew", padx=18, pady=(18, 16))

        self.start_button = ttk.Button(
            action_row,
            text="Iniciar automacao",
            style="Accent.TButton",
            command=lambda: self._start_run(dry_run=False),
        )
        self.start_button.pack(side="left")

        self.dry_run_button = ttk.Button(
            action_row,
            text="Dry run",
            style="Ghost.TButton",
            command=lambda: self._start_run(dry_run=True),
        )
        self.dry_run_button.pack(side="left", padx=10)

        self.stop_button = ttk.Button(
            action_row,
            text="Parar",
            style="Danger.TButton",
            command=self._request_stop,
            state="disabled",
        )
        self.stop_button.pack(side="left")

        columns = tk.Frame(parent, bg=COLORS["card"])
        columns.grid(row=3, column=0, sticky="nsew", padx=18, pady=(0, 18))
        columns.grid_columnconfigure(0, weight=0)
        columns.grid_columnconfigure(1, weight=1)
        columns.grid_rowconfigure(0, weight=1)

        preview_card = tk.Frame(columns, bg=COLORS["card_soft"], width=280)
        preview_card.grid(row=0, column=0, sticky="nsw", padx=(0, 14))
        preview_card.grid_propagate(False)

        tk.Frame(preview_card, bg=COLORS["line"], height=1).pack(fill="x")

        tk.Label(
            preview_card,
            text="FILA",
            font=FONTS["label"],
            bg=COLORS["card_soft"],
            fg=COLORS["accent"],
        ).pack(anchor="w", padx=14, pady=(14, 10))

        self.preview_list = tk.Listbox(
            preview_card,
            bg=COLORS["card_soft"],
            fg=COLORS["ink"],
            relief="flat",
            highlightthickness=0,
            selectbackground=COLORS["accent"],
            selectforeground="#031017",
            activestyle="none",
            font=FONTS["body"],
        )
        self.preview_list.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        log_card = tk.Frame(columns, bg=COLORS["console"])
        log_card.grid(row=0, column=1, sticky="nsew")
        log_card.grid_columnconfigure(0, weight=1)
        log_card.grid_rowconfigure(1, weight=1)

        tk.Frame(log_card, bg=COLORS["line"], height=1).grid(row=0, column=0, sticky="ew")

        tk.Label(
            log_card,
            text="CONSOLE",
            font=FONTS["label"],
            bg=COLORS["console"],
            fg=COLORS["accent"],
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 10))

        self.log_output = ScrolledText(
            log_card,
            wrap="word",
            bg=COLORS["console"],
            fg=COLORS["console_text"],
            insertbackground=COLORS["console_text"],
            relief="flat",
            font=FONTS["mono"],
            padx=12,
            pady=12,
        )
        self.log_output.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.log_output.tag_configure("info", foreground=COLORS["console_text"])
        self.log_output.tag_configure("warning", foreground="#CFCFCF")
        self.log_output.tag_configure("error", foreground="#B0B0B0")
        self.log_output.tag_configure("system", foreground=COLORS["accent_secondary"])
        self.log_output.configure(state="disabled")

    def _add_path_field(
        self,
        parent: tk.Widget,
        *,
        row: int,
        label: str,
        variable: tk.StringVar,
        browse_command,
        button_text: str,
    ) -> None:
        wrap = tk.Frame(parent, bg=COLORS["card"])
        wrap.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        wrap.grid_columnconfigure(0, weight=1)

        tk.Label(
            wrap,
            text=label,
            font=FONTS["label"],
            bg=COLORS["card"],
            fg=COLORS["muted"],
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        row_frame = tk.Frame(wrap, bg=COLORS["card"])
        row_frame.grid(row=1, column=0, sticky="ew")
        row_frame.grid_columnconfigure(0, weight=1)

        entry = tk.Entry(
            row_frame,
            textvariable=variable,
            relief="flat",
            bd=0,
            font=FONTS["body"],
            bg=COLORS["card_alt"],
            fg=COLORS["ink"],
            insertbackground=COLORS["accent"],
            highlightthickness=1,
            highlightbackground=COLORS["line"],
            highlightcolor=COLORS["accent"],
        )
        entry.grid(row=0, column=0, sticky="ew", ipady=10, padx=(0, 8))

        ttk.Button(
            row_frame,
            text=button_text,
            style="Ghost.TButton",
            command=browse_command,
        ).grid(row=0, column=1, sticky="e")

    def _add_input_field(self, parent: tk.Widget, *, row: int, label: str, variable: tk.StringVar) -> None:
        wrap = tk.Frame(parent, bg=COLORS["card"])
        wrap.grid(row=row, column=0, sticky="ew", pady=(0, 12))

        tk.Label(
            wrap,
            text=label,
            font=FONTS["label"],
            bg=COLORS["card"],
            fg=COLORS["muted"],
        ).pack(anchor="w", pady=(0, 6))

        tk.Entry(
            wrap,
            textvariable=variable,
            relief="flat",
            bd=0,
            font=FONTS["body"],
            bg=COLORS["card_alt"],
            fg=COLORS["ink"],
            insertbackground=COLORS["accent"],
            highlightthickness=1,
            highlightbackground=COLORS["line"],
            highlightcolor=COLORS["accent"],
        ).pack(fill="x", ipady=10)

    def _add_metric_field(self, parent: tk.Widget, column: int, label: str, variable: tk.StringVar) -> None:
        wrap = tk.Frame(parent, bg=COLORS["card"])
        wrap.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 6, 0))

        tk.Label(
            wrap,
            text=label,
            font=FONTS["label"],
            bg=COLORS["card"],
            fg=COLORS["muted"],
        ).pack(anchor="w", pady=(0, 6))

        tk.Entry(
            wrap,
            textvariable=variable,
            relief="flat",
            bd=0,
            font=FONTS["body"],
            bg=COLORS["card_alt"],
            fg=COLORS["ink"],
            insertbackground=COLORS["accent"],
            highlightthickness=1,
            highlightbackground=COLORS["line"],
            highlightcolor=COLORS["accent"],
            width=10,
        ).pack(fill="x", ipady=10)

    def _load_initial_state(self) -> None:
        default_config_path = self.runtime_base_path / "config.json"
        example_config_path = self.runtime_base_path / "config.example.json"

        loaded = False
        if default_config_path.exists():
            loaded = self._apply_config_file(default_config_path)
        elif example_config_path.exists():
            loaded = self._apply_config_file(example_config_path, update_config_path=False)

        if not loaded:
            self.config_path_var.set(str(default_config_path))
            self.queries_path_var.set(str(self.runtime_base_path / "queries.txt"))
            self.log_path_var.set(str(self.runtime_base_path / core.DEFAULT_LOG_RELATIVE_PATH))
        elif not self.config_path_var.get().strip():
            self.config_path_var.set(str(default_config_path))

        self.queries_path_var.trace_add("write", lambda *_: self._refresh_query_preview())

    def _apply_config_file(self, file_path: Path, *, update_config_path: bool = True) -> bool:
        try:
            settings = core.load_json_config(file_path)
        except (FileNotFoundError, ValueError):
            return False

        config_base = file_path.parent
        if update_config_path:
            self.config_path_var.set(str(file_path))

        queries_file = settings.get("queries_file")
        if queries_file:
            self.queries_path_var.set(str(core.resolve_config_path(queries_file, config_base)))
        else:
            self.queries_path_var.set(str(self.runtime_base_path / "queries.txt"))

        log_file = settings.get("log_file")
        if log_file:
            self.log_path_var.set(str(core.resolve_config_path(log_file, config_base)))
        else:
            self.log_path_var.set(str(self.runtime_base_path / core.DEFAULT_LOG_RELATIVE_PATH))

        self.start_url_var.set(str(settings.get("start_url", core.DEFAULT_START_URL)))
        self.delay_var.set(str(settings.get("delay_seconds", core.DEFAULT_DELAY_SECONDS)))
        self.keep_open_var.set(str(settings.get("keep_open_seconds", core.DEFAULT_KEEP_OPEN_SECONDS)))
        self.timeout_var.set(str(settings.get("timeout_seconds", core.DEFAULT_TIMEOUT_SECONDS)))
        self.headless_var.set(bool(settings.get("headless", False)))
        return True

    def _resolve_form_path(self, raw_value: str) -> Path | None:
        cleaned = raw_value.strip()
        if not cleaned:
            return None
        return core.resolve_config_path(cleaned, self.runtime_base_path)

    def _refresh_query_preview(self) -> None:
        if self.preview_list is None:
            return

        self.preview_list.delete(0, tk.END)
        try:
            queries_file = self._resolve_form_path(self.queries_path_var.get())
            if queries_file is None:
                runtime_queries = self.runtime_base_path / "queries.txt"
                queries_file = runtime_queries if runtime_queries.exists() else None
            queries = core.load_queries(queries_file)
            for item in queries:
                self.preview_list.insert(tk.END, item)
            origin = str(queries_file) if queries_file else "lista interna"
            self.query_info_var.set(f"{len(queries)} busca(s) prontas. Origem: {origin}")
        except Exception as exc:
            self.preview_list.insert(tk.END, "Nao foi possivel carregar a lista.")
            self.query_info_var.set(str(exc))

    def _build_form_config(self, *, dry_run: bool) -> core.AppConfig:
        queries_file = self._resolve_form_path(self.queries_path_var.get())
        log_file = self._resolve_form_path(self.log_path_var.get())
        config_file = self._resolve_form_path(self.config_path_var.get())

        if log_file is None:
            log_file = self.runtime_base_path / core.DEFAULT_LOG_RELATIVE_PATH

        try:
            delay_seconds = float(self.delay_var.get().strip())
            keep_open_seconds = float(self.keep_open_var.get().strip())
            timeout_seconds = int(float(self.timeout_var.get().strip()))
        except ValueError as exc:
            raise ValueError("Delay, timeout e fim aberto precisam ser numericos.") from exc

        return core.create_app_config(
            config_file=config_file,
            queries_file=queries_file,
            delay_seconds=delay_seconds,
            keep_open_seconds=keep_open_seconds,
            timeout_seconds=timeout_seconds,
            start_url=self.start_url_var.get().strip(),
            headless=self.headless_var.get(),
            dry_run=dry_run,
            log_file=log_file,
        )

    def _start_run(self, *, dry_run: bool) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo("Execucao em andamento", "Ja existe uma automacao rodando.")
            return

        try:
            config = self._build_form_config(dry_run=dry_run)
            if not dry_run and config.queries_file is not None:
                queries = core.refresh_local_queries_file(config.queries_file)
            else:
                queries = core.load_queries(config.queries_file)
        except Exception as exc:
            messagebox.showerror("Configuracao invalida", str(exc))
            return

        if self.log_output is not None:
            self.log_output.configure(state="normal")
            self.log_output.delete("1.0", tk.END)
            self.log_output.configure(state="disabled")

        self.stop_event = threading.Event()
        self._set_running_state(True)
        self._set_status("Validando..." if dry_run else "Executando", COLORS["warning"])
        self.summary_var.set("Dry run em andamento." if dry_run else "Automacao em andamento.")
        self.current_item_var.set(f"{len(queries)} busca(s) na fila.")

        if self.progress_bar is not None:
            self.progress_bar.configure(maximum=max(1, len(queries)), value=0)

        self.worker_thread = threading.Thread(
            target=self._run_worker,
            args=(config,),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_worker(self, config: core.AppConfig) -> None:
        handler = QueueLogHandler(self.event_queue)
        handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s", "%H:%M:%S"))

        logger = core.setup_logging(
            config.log_file,
            include_console=False,
            extra_handlers=[handler],
        )

        def progress_callback(index: int, total: int, query: str, status: str) -> None:
            self.event_queue.put(("progress", index, total, query, status))

        try:
            logger.info("Studio pronto para rodar. Log salvo em %s", config.log_file)
            summary = core.execute_automation(
                config,
                resource_base_path=self.resource_base_path,
                logger=logger,
                progress_callback=progress_callback,
                should_stop=self.stop_event.is_set,
            )
            self.event_queue.put(("done", summary))
        except (FileNotFoundError, ValueError) as exc:
            logger.error("Erro de configuracao: %s", exc)
            self.event_queue.put(("failed", str(exc)))
        except Exception as exc:
            logger.exception("Erro inesperado: %s", exc)
            self.event_queue.put(("failed", str(exc)))

    def _request_stop(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            self.stop_event.set()
            self._set_status("Parando...", COLORS["danger"])
            self.current_item_var.set("Pedido de parada enviado. Aguardando o proximo ponto seguro.")

    def _process_event_queue(self) -> None:
        while True:
            try:
                event = self.event_queue.get_nowait()
            except queue.Empty:
                break

            kind = event[0]
            if kind == "log":
                _, level, message = event
                self._append_log(message, level)
            elif kind == "progress":
                _, index, total, query, status = event
                self._update_progress(index, total, query, status)
            elif kind == "done":
                _, summary = event
                self._finish_run(summary)
            elif kind == "failed":
                _, message = event
                self._finish_failure(message)

        self.root.after(120, self._process_event_queue)

    def _update_progress(self, index: int, total: int, query: str, status: str) -> None:
        if self.progress_bar is not None:
            self.progress_bar.configure(maximum=max(1, total), value=index)

        suffix_map = {
            "success": "enviada",
            "timeout": "com timeout",
            "error": "com erro",
            "preview": "em preview",
        }
        suffix = suffix_map.get(status, "processada")
        self.current_item_var.set(f"[{index}/{total}] {query} ({suffix})")

    def _finish_run(self, summary: core.RunSummary) -> None:
        self._set_running_state(False)

        if summary.cancelled:
            self._set_status("Interrompido", COLORS["danger"])
            self.summary_var.set(
                f"Interrompido apos {summary.successes + summary.failures} item(ns) processados."
            )
        elif summary.dry_run:
            self._set_status("Dry run OK", COLORS["teal"])
            self.summary_var.set(f"Dry run concluido com {summary.total_queries} busca(s) validadas.")
        else:
            self._set_status("Concluido", COLORS["success"])
            self.summary_var.set(
                f"Concluido: {summary.successes} sucesso(s), {summary.failures} falha(s)."
            )

        elapsed = int(summary.duration_seconds)
        self.current_item_var.set(f"Tempo total: {elapsed} segundo(s).")

    def _finish_failure(self, message: str) -> None:
        self._set_running_state(False)
        self._set_status("Falhou", COLORS["danger"])
        self.summary_var.set("A execucao terminou com erro.")
        self.current_item_var.set(message)
        messagebox.showerror("Erro na execucao", message)

    def _set_status(self, text: str, color: str) -> None:
        if self.status_badge is not None:
            self.status_badge.configure(text=text, bg=color)

    def _set_running_state(self, running: bool) -> None:
        start_state = "disabled" if running else "normal"
        stop_state = "normal" if running else "disabled"

        if self.start_button is not None:
            self.start_button.configure(state=start_state)
        if self.dry_run_button is not None:
            self.dry_run_button.configure(state=start_state)
        if self.stop_button is not None:
            self.stop_button.configure(state=stop_state)

    def _append_log(self, message: str, level: str) -> None:
        if self.log_output is None:
            return

        tag = level if level in {"info", "warning", "error"} else "system"
        self.log_output.configure(state="normal")
        self.log_output.insert(tk.END, f"{message}\n", tag)
        self.log_output.see(tk.END)
        self.log_output.configure(state="disabled")

    def _browse_config_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Escolha o arquivo JSON",
            initialdir=str(self.runtime_base_path),
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
        )
        if file_path:
            self.config_path_var.set(file_path)

    def _browse_queries_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Escolha o arquivo de buscas",
            initialdir=str(self.runtime_base_path),
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
        )
        if file_path:
            self.queries_path_var.set(file_path)

    def _browse_log_file(self) -> None:
        file_path = filedialog.asksaveasfilename(
            title="Defina o arquivo de log",
            initialdir=str(self.runtime_base_path),
            initialfile="noir_search.log",
            defaultextension=".log",
            filetypes=[("Log", "*.log"), ("Texto", "*.txt"), ("Todos", "*.*")],
        )
        if file_path:
            self.log_path_var.set(file_path)

    def _load_config_from_dialog(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Carregar configuracao JSON",
            initialdir=str(self.runtime_base_path),
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
        )
        if not file_path:
            return

        if not self._apply_config_file(Path(file_path)):
            messagebox.showerror("Erro ao carregar", "Nao foi possivel ler esse arquivo JSON.")
            return

        self._refresh_query_preview()
        self._append_log(f"Configuracao carregada de {file_path}", "system")

    def _save_config_to_disk(self) -> None:
        file_path = self.config_path_var.get().strip()
        if not file_path:
            file_path = str(self.runtime_base_path / "config.json")

        save_path = filedialog.asksaveasfilename(
            title="Salvar configuracao",
            initialdir=str(Path(file_path).parent if file_path else self.runtime_base_path),
            initialfile=Path(file_path).name,
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
        )
        if not save_path:
            return

        try:
            target_path = Path(save_path)
            data = {
                "queries_file": self._serialize_path_for_config(
                    self._resolve_form_path(self.queries_path_var.get()),
                    target_path.parent,
                ),
                "delay_seconds": float(self.delay_var.get().strip()),
                "keep_open_seconds": float(self.keep_open_var.get().strip()),
                "timeout_seconds": int(float(self.timeout_var.get().strip())),
                "start_url": self.start_url_var.get().strip(),
                "headless": self.headless_var.get(),
                "log_file": self._serialize_path_for_config(
                    self._resolve_form_path(self.log_path_var.get()),
                    target_path.parent,
                ),
            }

            target_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except ValueError:
            messagebox.showerror("Erro ao salvar", "Delay, timeout e fim aberto precisam ser numericos.")
            return
        except OSError as exc:
            messagebox.showerror("Erro ao salvar", str(exc))
            return

        self.config_path_var.set(str(target_path))
        self._append_log(f"Configuracao salva em {target_path}", "system")

    def _serialize_path_for_config(self, path_value: Path | None, config_dir: Path) -> str | None:
        if path_value is None:
            return None
        try:
            return str(path_value.relative_to(config_dir))
        except ValueError:
            return str(path_value)


def main() -> None:
    root = tk.Tk()
    AutomationStudio(root)
    root.mainloop()


if __name__ == "__main__":
    main()
