"""Главное окно приложения и цикл анимации."""

from __future__ import annotations

import time
import tkinter as tk

from src import config
from src.models.flock import Flock
from src.renderers.renderer import Renderer


class App:
    """Приложение «Бойды»: окно, холст и главный цикл анимации.

    Класс связывает модель (``Flock``), которая считает движение,
    и ``Renderer``, который его рисует.
    """

    def __init__(self) -> None:
        """Создать окно и холст."""
        self.root = tk.Tk()
        self.root.title("Бойды — моделирование стаи")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=config.CANVAS_WIDTH,
                                height=config.CANVAS_HEIGHT,
                                bg=config.BACKGROUND_COLOR,
                                highlightthickness=0)
        self.canvas.pack()

        self.flock = Flock(config.CANVAS_WIDTH, config.CANVAS_HEIGHT,
                           config.DEFAULT_BOID_COUNT)
        self.renderer = Renderer(self.canvas)

        self.paused = False
        self.fps = float(config.FPS)
        self._last_frame = time.perf_counter()
        self._bind_events()

    def _bind_events(self) -> None:
        """Назначить клавиши и действия мыши."""
        for force, key in config.FORCE_KEYS.items():
            self.root.bind(key, lambda _e, f=force: self.toggle_force(f))
        self.root.bind("<space>", lambda _e: self.toggle_pause())
        self.root.bind("<Key>", self._on_key)
        self.canvas.bind("<Button-1>", self.add_boids)

    def _on_key(self, event: tk.Event) -> None:
        """Обработать буквенные клавиши в английской и русской раскладке.

        Проверяется введённый символ, а не название клавиши, поэтому
        R и V работают и тогда, когда включена русская раскладка
        (на тех же клавишах там буквы К и М).
        """
        char = event.char.lower()
        if char in ("r", "к"):
            self.reset()
        elif char in ("v", "м"):
            self.toggle_radius()

    # ------------------------------------------------------------------
    # Действия пользователя
    # ------------------------------------------------------------------
    def toggle_force(self, force: str) -> None:
        """Включить или выключить одну из трёх сил стаи."""
        attribute = f"{force}_enabled"
        setattr(self.flock.settings, attribute,
                not getattr(self.flock.settings, attribute))

    def toggle_pause(self) -> None:
        """Поставить симуляцию на паузу или продолжить."""
        self.paused = not self.paused

    def reset(self) -> None:
        """Перемешать стаю: новые случайные положения и скорости."""
        self.flock.reset()

    def toggle_radius(self) -> None:
        """Показать или скрыть радиусы обзора выделенного бойда."""
        self.renderer.show_radius = not self.renderer.show_radius

    def add_boids(self, event: tk.Event) -> None:
        """Добавить несколько бойдов в точку щелчка мыши."""
        for _ in range(config.BOIDS_PER_CLICK):
            if len(self.flock.boids) >= config.MAX_BOID_COUNT:
                break
            self.flock.add_boid(event.x, event.y)

    # ------------------------------------------------------------------
    # Главный цикл
    # ------------------------------------------------------------------
    def tick(self) -> None:
        """Один кадр анимации: шаг модели, отрисовка, планирование кадра."""
        now = time.perf_counter()
        frame_time = now - self._last_frame
        self._last_frame = now
        if frame_time > 0:
            # Сглаженный FPS: экспоненциальное скользящее среднее.
            self.fps = 0.9 * self.fps + 0.1 / frame_time

        if not self.paused:
            self.flock.step()
        self.renderer.draw(self.flock, self.fps, self.paused)
        self.root.after(config.FRAME_DELAY_MS, self.tick)

    def run(self) -> None:
        """Запустить анимацию и главный цикл tkinter."""
        self.tick()
        self.root.mainloop()
