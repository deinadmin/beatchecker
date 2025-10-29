"""CustomTkinter application for BeatChecker."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import traceback
from typing import Literal, Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox

from . import config
from .analyze import AnalysisError, AnalysisResult, analyze_audio
from .download import DownloadError, download_youtube_audio

__all__ = ["BeatCheckerApp", "run"]

StateLiteral = Literal["initial", "loading", "results"]


def _resolve_color(value: str | tuple[str, ...]) -> str:
    if isinstance(value, tuple):
        for item in reversed(value):
            if item and item != "transparent":
                return item
        return "#1a1a1a"

    if value == "transparent" or not value:
        return "#1a1a1a"

    return value


class Spinner(ctk.CTkCanvas):
    """Simple animated spinner for loading state."""

    def __init__(self, master: ctk.CTkBaseClass | None, *, size: int = 96, line_width: int = 8,
                 line_color: str | None = None) -> None:
        bg_color = _resolve_color(master.cget("fg_color")) if master is not None else "#1a1a1a"
        super().__init__(master, width=size, height=size, bg=bg_color, highlightthickness=0)
        self.configure(background=bg_color)
        self._size = size
        self._line_width = line_width
        self._line_color = line_color or config.PRIMARY_COLOR
        inset = line_width // 2
        self._arc = self.create_arc(
            inset,
            inset,
            size - inset,
            size - inset,
            start=0,
            extent=300,
            style="arc",
            outline=self._line_color,
            width=line_width,
        )
        self._job: Optional[str] = None
        self._angle = 0

    def start(self) -> None:
        if self._job is None:
            self._animate()

    def stop(self) -> None:
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None

    def _animate(self) -> None:
        self._angle = (self._angle + 10) % 360
        self.itemconfigure(self._arc, start=self._angle)
        self._job = self.after(16, self._animate)


class BeatCheckerApp(ctk.CTk):
    """Main window for the BeatChecker desktop application."""

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(config.WINDOW_TITLE)
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.resizable(False, False)

        self._is_processing = False
        self._analysis_thread: Optional[threading.Thread] = None
        self._latest_results: Optional[AnalysisResult] = None
        self._state: StateLiteral = "initial"
        self._is_transitioning = False
        self._current_frame: ctk.CTkFrame | None = None
        self._transition_steps = 14
        self._transition_duration = 240  # milliseconds
        self._pending_state: Optional[StateLiteral] = None

        self._frames: dict[StateLiteral, ctk.CTkFrame] = {}

        self._build_state_views()
        self._show_initial_state()

    # ------------------------------------------------------------------
    # UI construction
    def _build_state_views(self) -> None:
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.pack(expand=True, fill="both", padx=40, pady=40)

        self._frames["initial"] = self._build_initial_state(self.content_container)
        self._frames["loading"] = self._build_loading_state(self.content_container)
        self._frames["results"] = self._build_results_state(self.content_container)

    def _build_initial_state(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        stack = ctk.CTkFrame(content, fg_color="transparent")
        stack.grid(row=0, column=0)

        title = ctk.CTkLabel(
            stack,
            text="BeatChecker",
            font=ctk.CTkFont(size=42, weight="bold"),
        )
        title.pack(pady=(0, 8))

        subtitle = ctk.CTkLabel(
            stack,
            text="Let's check that beat.",
            font=ctk.CTkFont(size=18),
            text_color="#A0A4AF",
        )
        subtitle.pack(pady=(0, 24))

        self.url_var = ctk.StringVar()
        self.url_entry = ctk.CTkEntry(
            stack,
            width=560,
            height=48,
            textvariable=self.url_var,
            placeholder_text="Paste YouTube URL",
        )
        self.url_entry.pack(pady=(0, 16))
        self.url_entry.bind("<Return>", lambda _: self.start_analysis())

        self.analyze_button = ctk.CTkButton(
            stack,
            text="Analyze Beat",
            width=200,
            height=46,
            command=self.start_analysis,
        )
        self.analyze_button.pack()

        self.initial_error_label = ctk.CTkLabel(
            stack,
            text="",
            text_color=config.ERROR_COLOR,
            wraplength=420,
            justify="center",
        )
        self.initial_error_label.pack(pady=(16, 0))

        return frame

    def _build_loading_state(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.grid(row=0, column=0, sticky="nsew")
        content.pack_propagate(False)

        self.loading_spinner = Spinner(content, size=110, line_width=10)
        self.loading_spinner.pack(pady=(0, 24))

        self.loading_status_var = ctk.StringVar(value="Preparing analysis...")
        self.loading_status_label = ctk.CTkLabel(
            content,
            textvariable=self.loading_status_var,
            font=ctk.CTkFont(size=18),
        )
        self.loading_status_label.pack()

        return frame

    def _build_results_state(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(
            frame,
            corner_radius=18,
            fg_color="#1E1E24",
            border_width=1,
            border_color="#2A2D35",
        )
        card.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        title = ctk.CTkLabel(
            card,
            text="Analysis Finished! Results:",
            font=ctk.CTkFont(size=26, weight="bold"),
        )
        title.pack(pady=(28, 20))

        self.results_bpm_label = ctk.CTkLabel(
            card,
            text="BPM: --",
            font=ctk.CTkFont(size=40, weight="bold"),
        )
        self.results_bpm_label.pack(pady=(0, 12))

        self.results_key_label = ctk.CTkLabel(
            card,
            text="Key: --",
            font=ctk.CTkFont(size=22),
        )
        self.results_key_label.pack()

        self.results_path_label = ctk.CTkLabel(
            card,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#A0A4AF",
            wraplength=420,
            justify="center",
        )
        self.results_path_label.pack(pady=(12, 16))

        buttons_row = ctk.CTkFrame(card, fg_color="transparent")
        buttons_row.pack(padx=24, fill="x")
        buttons_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="buttons")

        self.save_button = ctk.CTkButton(
            buttons_row,
            text="Save to Files",
            command=self._save_results_to_file,
            height=42,
        )
        self.save_button.grid(row=0, column=0, padx=6, pady=(0, 0), sticky="ew")

        self.drag_button = ctk.CTkButton(
            buttons_row,
            text="Drag to DAW",
            command=self._handle_drag_request,
            height=42,
        )
        self.drag_button.grid(row=0, column=1, padx=6, sticky="ew")

        self.home_button = ctk.CTkButton(
            buttons_row,
            text="Back to Home",
            command=self._return_home,
            height=42,
        )
        self.home_button.grid(row=0, column=2, padx=6, sticky="ew")

        self.results_feedback_var = ctk.StringVar(value="")
        self.results_feedback_label = ctk.CTkLabel(
            card,
            textvariable=self.results_feedback_var,
            text_color=config.SUCCESS_COLOR,
            font=ctk.CTkFont(size=13),
            wraplength=420,
            justify="center",
        )
        self.results_feedback_label.pack(pady=(16, 24))

        return frame

    # ------------------------------------------------------------------
    def _show_initial_state(self) -> None:
        initial_frame = self._frames["initial"]
        initial_frame.place(relx=0.5, rely=0.5, anchor="center")
        self._current_frame = initial_frame
        self.url_entry.focus_set()

    # ------------------------------------------------------------------
    # Event handlers
    def start_analysis(self) -> None:
        if self._is_processing or self._is_transitioning:
            return

        url = self.url_var.get().strip()
        if not url:
            self._show_initial_error("Please enter a valid YouTube URL.")
            return

        self._show_initial_error("")
        self._begin_processing()

        self._analysis_thread = threading.Thread(target=self._run_analysis, args=(url,), daemon=True)
        self._analysis_thread.start()

    def _run_analysis(self, url: str) -> None:
        try:
            self._update_loading("⏳ Downloading beat...")
            audio_file = download_youtube_audio(url)

            self._update_loading("🎵 Analyzing audio...")
            results = analyze_audio(audio_file)

            self.after(0, lambda: self._handle_success(results))
        except ValueError as exc:
            self.after(0, self._handle_failure, str(exc))
        except DownloadError as exc:
            self.after(0, self._handle_failure, str(exc))
        except AnalysisError as exc:
            self.after(0, self._handle_failure, str(exc))
        except Exception:
            captured_trace = traceback.format_exc()
            self.after(
                0,
                lambda: self._handle_failure(
                    "Unexpected error occurred during analysis. See console for details."
                ),
            )
            print(captured_trace)  # Debug aid for developers

    # ------------------------------------------------------------------
    # State transitions
    def _transition_to(self, target_state: StateLiteral) -> None:
        if target_state == self._state and not self._is_transitioning:
            return

        if self._is_transitioning:
            if target_state != self._state:
                self._pending_state = target_state
            return

        target_frame = self._frames[target_state]
        if self._current_frame is None:
            target_frame.place(relx=0.5, rely=0.5, anchor="center")
            self._current_frame = target_frame
            self._state = target_state
            self._on_enter_state(target_state)
            return

        self._is_transitioning = True
        self._pending_state = None
        self._on_exit_state(self._state)

        target_frame.place(relx=0.5, rely=1.5, anchor="center")
        if target_state == "loading":
            self.loading_spinner.start()

        steps = self._transition_steps
        interval = max(1, self._transition_duration // steps)

        def animate(step: int) -> None:
            progress = step / steps
            current_rely = 0.5 - progress
            target_rely = 1.5 - progress
            self._current_frame.place_configure(rely=current_rely)
            target_frame.place_configure(rely=target_rely)

            if step < steps:
                self.after(interval, animate, step + 1)
            else:
                self._current_frame.place_forget()
                target_frame.place_configure(rely=0.5)
                self._current_frame = target_frame
                self._state = target_state
                self._is_transitioning = False
                self._on_enter_state(target_state)

                if self._pending_state and self._pending_state != target_state:
                    next_state = self._pending_state
                    self._pending_state = None
                    self.after(0, self._transition_to, next_state)
                else:
                    self._pending_state = None

        animate(0)

    def _on_exit_state(self, state: StateLiteral) -> None:
        if state == "loading":
            self.loading_spinner.stop()

    def _on_enter_state(self, state: StateLiteral) -> None:
        if state == "initial":
            self.analyze_button.configure(state=ctk.NORMAL)
            self.url_entry.focus_set()
        elif state == "loading":
            self.analyze_button.configure(state=ctk.DISABLED)
        elif state == "results":
            self.analyze_button.configure(state=ctk.DISABLED)

    # ------------------------------------------------------------------
    # Workflow helpers
    def _begin_processing(self) -> None:
        self._is_processing = True
        self._latest_results = None
        self.results_feedback_var.set("")
        self._transition_to("loading")

    def _update_loading(self, message: str) -> None:
        self.after(0, self.loading_status_var.set, message)

    def _handle_success(self, results: AnalysisResult) -> None:
        self._latest_results = results
        self._is_processing = False
        self._update_results_view(results)
        self._transition_to("results")

    def _handle_failure(self, message: str) -> None:
        self._is_processing = False
        self._show_initial_error(message)
        self._transition_to("initial")

    def _update_results_view(self, results: AnalysisResult) -> None:
        self.results_bpm_label.configure(text=f"BPM: {int(results.bpm)}")
        self.results_key_label.configure(text=f"Key: {results.key}")
        self.results_path_label.configure(text=f"Source file: {results.file_path}")
        self.results_feedback_var.set("")

    def _show_initial_error(self, message: str) -> None:
        self.initial_error_label.configure(text=message)

    def _save_results_to_file(self) -> None:
        if not self._latest_results:
            return

        source = self._latest_results.file_path
        destination = filedialog.asksaveasfilename(
            title="Save Beat As",
            defaultextension=".mp3",
            initialfile=source.name,
            filetypes=(("MP3 Audio", "*.mp3"), ("All Files", "*.*")),
        )

        if not destination:
            return

        try:
            shutil.copy2(source, destination)
        except OSError as exc:
            messagebox.showerror("Save Failed", f"Could not save file.\n{exc}")
            return

        self.results_feedback_var.set("Beat saved successfully.")

    def _handle_drag_request(self) -> None:
        if not self._latest_results:
            return

        path = self._latest_results.file_path.resolve()
        try:
            self.clipboard_clear()
            self.clipboard_append(str(path))
        except Exception:
            pass

        self._reveal_file_location(path)
        self.results_feedback_var.set(
            "Opened file location. Drag the MP3 from the file explorer into your DAW."
        )

    def _reveal_file_location(self, path: os.PathLike[str]) -> None:
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", "-R", str(path)], check=False)
            elif sys.platform.startswith("win"):
                subprocess.run(["explorer", "/select,", str(path)], check=False)
            else:
                subprocess.run(["xdg-open", str(os.fspath(os.path.dirname(path)))], check=False)
        except Exception as exc:
            messagebox.showwarning("Reveal Failed", f"Could not open file location.\n{exc}")

    def _return_home(self) -> None:
        if self._is_transitioning:
            return
        self._latest_results = None
        self.url_var.set("")
        self.results_feedback_var.set("")
        self._transition_to("initial")

    # ------------------------------------------------------------------
    # Public API
    def run(self) -> None:
        """Start the Tk main loop."""
        self.mainloop()


def run() -> None:
    """Launch the BeatChecker application."""
    app = BeatCheckerApp()
    app.run()
