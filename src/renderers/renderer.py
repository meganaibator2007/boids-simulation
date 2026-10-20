"""Отрисовка стаи на холсте tkinter."""

from __future__ import annotations

import colorsys
import math
import tkinter as tk

from src import config
from src.models.flock import FORCES, Flock

# Количество оттенков в палитре: цвет бойда зависит от направления полёта.
PALETTE_SIZE = 36


def _build_palette(size: int) -> list[str]:
    """Построить палитру цветов по кругу оттенков HSV."""
    palette = []
    for i in range(size):
        r, g, b = colorsys.hsv_to_rgb(i / size, 0.55, 0.95)
        palette.append(f"#{int(r * 255):02x}{int(g * 255):02x}"
                       f"{int(b * 255):02x}")
    return palette


class Renderer:
    """Рисует бойдов, радиусы обзора выбранного бойда и информационную панель.

    Фигуры на холсте создаются один раз и затем только перемещаются
    через ``canvas.coords`` — это гораздо быстрее, чем стирать и
    рисовать всё заново на каждом кадре.
    """

    def __init__(self, canvas: tk.Canvas) -> None:
        """Подготовить отрисовку на холсте ``canvas``."""
        self.canvas = canvas
        self.palette = _build_palette(PALETTE_SIZE)
        self.show_radius = True
        self._items: list[int] = []
        self._colors: list[int] = []
        self._perception = canvas.create_oval(0, 0, 0, 0, dash=(3, 4),
                                              outline=config.PERCEPTION_COLOR)
        self._separation = canvas.create_oval(0, 0, 0, 0, dash=(2, 3),
                                              outline=config.SEPARATION_COLOR)
        self._hud = canvas.create_text(12, 10, anchor="nw",
                                       fill=config.TEXT_COLOR,
                                       font=("Helvetica", 12))
        self._hint = canvas.create_text(
            12, config.CANVAS_HEIGHT - 10, anchor="sw",
            fill=config.MUTED_TEXT_COLOR, font=("Helvetica", 11),
            text="1/2/3 — силы   Пробел — пауза   R — сброс   "
                 "V — радиусы   ЛКМ — добавить бойдов")

    def _sync_items(self, count: int) -> None:
        """Создать или удалить фигуры, чтобы их было ровно ``count``."""
        while len(self._items) < count:
            item = self.canvas.create_polygon(0, 0, 0, 0, 0, 0, outline="")
            self._items.append(item)
            self._colors.append(-1)
        while len(self._items) > count:
            self.canvas.delete(self._items.pop())
            self._colors.pop()
        # Надписи и круги всегда поверх бойдов.
        for item in (self._perception, self._separation,
                     self._hud, self._hint):
            self.canvas.tag_raise(item)

    @staticmethod
    def triangle(x: float, y: float, angle: float,
                 size: float) -> list[float]:
        """Вернуть вершины треугольника, «смотрящего» по углу ``angle``.

        Нос находится впереди центра на 2 * size, а две задние вершины
        лежат позади центра и смещены в стороны перпендикулярно курсу
        на 0.7 * size, поэтому треугольник узкий, похожий на птицу.
        """
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        nose = (x + cos_a * size * 2, y + sin_a * size * 2)
        back_x, back_y = x - cos_a * size, y - sin_a * size
        # (-sin, cos) — единичный вектор, перпендикулярный курсу.
        half = size * 0.7
        left = (back_x - sin_a * half, back_y + cos_a * half)
        right = (back_x + sin_a * half, back_y - cos_a * half)
        return [*nose, *left, *right]

    def draw(self, flock: Flock, fps: float, paused: bool) -> None:
        """Отрисовать текущее состояние стаи."""
        self._sync_items(len(flock.boids))
        for index, boid in enumerate(flock.boids):
            angle = boid.heading
            item = self._items[index]
            self.canvas.coords(item, *self.triangle(
                boid.position.x, boid.position.y, angle, config.BOID_SIZE))
            # Номер оттенка по направлению: угол из [-pi, pi] -> [0, N).
            color = int((angle + math.pi) / (2 * math.pi) * PALETTE_SIZE)
            color %= PALETTE_SIZE
            if index == 0 and self.show_radius:
                self.canvas.itemconfig(item, fill=config.HIGHLIGHT_COLOR)
                self._colors[index] = -1
            elif color != self._colors[index]:
                # itemconfig — дорогая операция, поэтому цвет меняется
                # только когда бойд перешёл в другой сектор палитры.
                self.canvas.itemconfig(item, fill=self.palette[color])
                self._colors[index] = color
        self._draw_radius(flock)
        self._draw_hud(flock, fps, paused)

    def _draw_radius(self, flock: Flock) -> None:
        """Показать радиус обзора и радиус разделения первого бойда."""
        if not self.show_radius or not flock.boids:
            self.canvas.itemconfig(self._perception, state="hidden")
            self.canvas.itemconfig(self._separation, state="hidden")
            return
        pos = flock.boids[0].position
        for item, radius in (
                (self._perception, flock.settings.perception_radius),
                (self._separation, flock.settings.separation_radius)):
            self.canvas.itemconfig(item, state="normal")
            self.canvas.coords(item, pos.x - radius, pos.y - radius,
                               pos.x + radius, pos.y + radius)

    def _draw_hud(self, flock: Flock, fps: float, paused: bool) -> None:
        """Обновить текст со статистикой и состоянием сил."""
        states = []
        for force in FORCES:
            mark = "вкл" if getattr(flock.settings,
                                    f"{force}_enabled") else "выкл"
            states.append(f"[{config.FORCE_KEYS[force]}] "
                          f"{config.FORCE_TITLES[force]}: {mark}")
        status = "  ПАУЗА" if paused else ""
        self.canvas.itemconfig(
            self._hud,
            text=f"Бойдов: {len(flock.boids)}   FPS: {fps:4.0f}{status}\n"
                 + "   ".join(states))
