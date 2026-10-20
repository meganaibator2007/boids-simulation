"""Панель управления: слайдеры весов сил, переключатели и кнопки."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from src import config
from src.models.flock import FORCES, FlockSettings


class ControlPanel(tk.Frame):
    """Боковая панель, связывающая элементы интерфейса с ``FlockSettings``.

    Каждый слайдер и флажок привязан к переменной tkinter. При изменении
    переменной (мышкой или с клавиатуры) срабатывает ``trace_add`` и
    новое значение сразу записывается в настройки стаи.
    """

    def __init__(self, master: tk.Misc, settings: FlockSettings,
                 on_count: Callable[[int], None],
                 on_pause: Callable[[], None],
                 on_reset: Callable[[], None]) -> None:
        """Построить панель для настроек ``settings``.

        ``on_count`` вызывается при изменении количества бойдов,
        ``on_pause`` и ``on_reset`` — при нажатии соответствующих кнопок.
        """
        super().__init__(master, padx=12, pady=10)
        self.settings = settings
        self.on_count = on_count
        self.enabled: dict[str, tk.BooleanVar] = {}
        self.weights: dict[str, tk.DoubleVar] = {}

        self._title("Силы стаи")
        for force in FORCES:
            self._add_force(force)

        self._title("Параметры")
        self._add_slider("Радиус обзора", "perception_radius", 20, 150, 5)
        self._add_slider("Радиус разделения", "separation_radius",
                         5, 60, 1)
        self._add_slider("Максимальная скорость", "max_speed", 2, 8, 0.5)

        self.count = tk.IntVar(value=config.DEFAULT_BOID_COUNT)
        self._scale("Количество бойдов", self.count, config.MIN_BOID_COUNT,
                    config.MAX_BOID_COUNT, 5)
        self.count.trace_add("write", self._count_changed)

        buttons = tk.Frame(self)
        buttons.pack(fill="x", pady=(12, 0))
        self.pause_button = tk.Button(buttons, text="Пауза", width=11,
                                      command=on_pause, takefocus=0)
        self.pause_button.pack(side="left")
        tk.Button(buttons, text="Сброс", width=11, command=on_reset,
                  takefocus=0).pack(side="right")

    # ------------------------------------------------------------------
    # Построение элементов
    # ------------------------------------------------------------------
    def _title(self, text: str) -> None:
        """Добавить заголовок раздела."""
        tk.Label(self, text=text, font=("Helvetica", 13, "bold"),
                 anchor="w").pack(fill="x", pady=(8, 2))

    def _scale(self, label: str, variable: tk.Variable, low: float,
               high: float, resolution: float) -> tk.Scale:
        """Создать горизонтальный слайдер, связанный с ``variable``."""
        scale = tk.Scale(self, label=label, variable=variable,
                         from_=low, to=high, resolution=resolution,
                         orient="horizontal", length=230, takefocus=0)
        scale.pack(fill="x")
        return scale

    def _add_force(self, force: str) -> None:
        """Добавить флажок включения силы и слайдер её веса."""
        title = config.FORCE_TITLES[force]
        key = config.FORCE_KEYS[force]
        enabled = tk.BooleanVar(value=getattr(self.settings,
                                              f"{force}_enabled"))
        tk.Checkbutton(self, text=f"{title}  [{key}]", variable=enabled,
                       anchor="w", takefocus=0).pack(fill="x")
        enabled.trace_add("write", lambda *_: setattr(
            self.settings, f"{force}_enabled", enabled.get()))
        self.enabled[force] = enabled

        weight = tk.DoubleVar(value=getattr(self.settings,
                                            f"{force}_weight"))
        self._scale("Вес", weight, 0, 3, 0.1)
        weight.trace_add("write", lambda *_: setattr(
            self.settings, f"{force}_weight", weight.get()))
        self.weights[force] = weight

    def _add_slider(self, label: str, attribute: str, low: float,
                    high: float, resolution: float) -> None:
        """Добавить слайдер для числового атрибута настроек."""
        variable = tk.DoubleVar(value=getattr(self.settings, attribute))
        self._scale(label, variable, low, high, resolution)
        variable.trace_add("write", lambda *_: setattr(
            self.settings, attribute, variable.get()))

    # ------------------------------------------------------------------
    # Публичные методы
    # ------------------------------------------------------------------
    def toggle_force(self, force: str) -> None:
        """Переключить силу; флажок на панели обновится автоматически."""
        variable = self.enabled[force]
        variable.set(not variable.get())

    def set_paused(self, paused: bool) -> None:
        """Обновить подпись кнопки паузы."""
        self.pause_button.config(text="Продолжить" if paused else "Пауза")

    def set_count(self, count: int) -> None:
        """Показать на слайдере новое количество бойдов."""
        self.count.set(count)

    def _count_changed(self, *_args) -> None:
        """Передать новое значение слайдера количества в приложение."""
        try:
            self.on_count(self.count.get())
        except tk.TclError:
            # Во время ввода значение может быть временно некорректным.
            pass
