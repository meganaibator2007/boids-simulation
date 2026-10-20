"""Стая бойдов и три правила Крейга Рейнольдса.

Каждый бойд видит только соседей в радиусе обзора и на каждом шаге
складывает три управляющие силы:

* разделение (separation) — не подлетать к соседям слишком близко;
* выравнивание (alignment) — лететь в ту же сторону, что и соседи;
* сплочение (cohesion) — держаться ближе к центру группы соседей.

Из этих простых локальных правил возникает сложное поведение стаи.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from src.models.boid import Boid
from src.models.vector import Vector2

# Названия сил, общие для модели, интерфейса и отрисовки.
FORCES = ("separation", "alignment", "cohesion")


@dataclass
class FlockSettings:
    """Параметры стаи, которые можно менять во время работы программы."""

    separation_weight: float = 1.6
    alignment_weight: float = 1.0
    cohesion_weight: float = 0.9
    separation_enabled: bool = True
    alignment_enabled: bool = True
    cohesion_enabled: bool = True
    perception_radius: float = 60.0
    separation_radius: float = 24.0
    max_speed: float = 3.5
    min_speed: float = 1.5
    max_force: float = 0.08

    def weight(self, force: str) -> float:
        """Вернуть вес силы с учётом того, включена ли она."""
        if not getattr(self, f"{force}_enabled"):
            return 0.0
        return getattr(self, f"{force}_weight")


def wrap_delta(delta: float, size: float) -> float:
    """Вернуть кратчайшее смещение по одной оси в тороидальном мире.

    Если объекты стоят у противоположных краёв экрана, то через край
    они ближе друг к другу, чем через весь экран. Сдвиг на половину
    размера и взятие остатка переводят смещение в диапазон
    ``[-size / 2, size / 2)``.
    """
    return (delta + size / 2) % size - size / 2


class Flock:
    """Стая бойдов в прямоугольном тороидальном мире."""

    def __init__(self, width: float, height: float, count: int,
                 settings: FlockSettings | None = None,
                 rng: random.Random | None = None) -> None:
        """Создать стаю из ``count`` бойдов в мире ``width`` x ``height``."""
        self.width = width
        self.height = height
        self.settings = settings or FlockSettings()
        self.rng = rng or random.Random()
        self.boids: list[Boid] = []
        self.reset(count)

    # ------------------------------------------------------------------
    # Управление составом стаи
    # ------------------------------------------------------------------
    def reset(self, count: int | None = None) -> None:
        """Пересоздать стаю со случайными положениями и скоростями."""
        if count is None:
            count = len(self.boids)
        self.boids = []
        for _ in range(count):
            self.add_boid(self.rng.uniform(0, self.width),
                          self.rng.uniform(0, self.height))

    def add_boid(self, x: float, y: float) -> Boid:
        """Добавить бойда в точку ``(x, y)`` со случайной скоростью.

        Направление выбирается равновероятно, а модуль скорости — между
        минимальной и максимальной, чтобы стая с самого начала двигалась
        естественно, а не стояла на месте.
        """
        s = self.settings
        velocity = Vector2.from_angle(self.rng.uniform(0, 2 * math.pi),
                                      self.rng.uniform(s.min_speed,
                                                       s.max_speed))
        boid = Boid(Vector2(x, y), velocity)
        self.boids.append(boid)
        return boid

    def set_count(self, count: int) -> None:
        """Довести количество бойдов до ``count``, сохранив остальных."""
        while len(self.boids) < count:
            self.add_boid(self.rng.uniform(0, self.width),
                          self.rng.uniform(0, self.height))
        del self.boids[count:]

    # ------------------------------------------------------------------
    # Поиск соседей
    # ------------------------------------------------------------------
    def _build_grid(self) -> tuple[dict, float, int, int]:
        """Разложить бойдов по ячейкам сетки со стороной = радиусу обзора.

        Тогда все соседи бойда лежат в его ячейке или в восьми соседних,
        и вместо перебора всех пар (O(n^2)) проверяется лишь небольшая
        часть стаи.
        """
        cell = self.settings.perception_radius
        cols = max(1, int(self.width // cell))
        rows = max(1, int(self.height // cell))
        grid: dict[tuple[int, int], list[Boid]] = {}
        for boid in self.boids:
            key = (int(boid.position.x / self.width * cols) % cols,
                   int(boid.position.y / self.height * rows) % rows)
            grid.setdefault(key, []).append(boid)
        return grid, cell, cols, rows

    def neighbors(self, boid: Boid, grid_data: tuple | None = None
                  ) -> list[tuple[Boid, Vector2, float]]:
        """Вернуть соседей бойда в радиусе обзора.

        Каждый элемент — кортеж ``(сосед, смещение, квадрат расстояния)``,
        где смещение — кратчайший вектор от бойда к соседу с учётом
        тороидальной геометрии.
        """
        grid, _, cols, rows = grid_data or self._build_grid()
        radius_sq = self.settings.perception_radius ** 2
        cx = int(boid.position.x / self.width * cols) % cols
        cy = int(boid.position.y / self.height * rows) % rows
        cells = {((cx + dx) % cols, (cy + dy) % rows)
                 for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        result = []
        for key in cells:
            for other in grid.get(key, ()):
                if other is boid:
                    continue
                dx = wrap_delta(other.position.x - boid.position.x,
                                self.width)
                dy = wrap_delta(other.position.y - boid.position.y,
                                self.height)
                dist_sq = dx * dx + dy * dy
                if dist_sq < radius_sq:
                    result.append((other, Vector2(dx, dy), dist_sq))
        return result

    # ------------------------------------------------------------------
    # Три силы Рейнольдса
    # ------------------------------------------------------------------
    def _steer(self, boid: Boid, direction: Vector2) -> Vector2:
        """Перевести желаемое направление в управляющую силу.

        Формула Рейнольдса: сила = желаемая скорость - текущая скорость,
        где желаемая скорость направлена по ``direction`` и равна
        максимальной. Сила ограничивается ``max_force``, поэтому бойд
        поворачивает плавно, а не мгновенно.
        """
        if direction.length_squared() == 0:
            return Vector2()
        desired = direction.with_length(self.settings.max_speed)
        return (desired - boid.velocity).limited(self.settings.max_force)

    def separation(self, boid: Boid, neighbors: list) -> Vector2:
        """Сила разделения: оттолкнуться от слишком близких соседей.

        Вектор от соседа к бойду делится на квадрат расстояния, то есть
        направление нормируется, а величина убывает как 1/d: чем ближе
        сосед, тем сильнее отталкивание.
        """
        limit_sq = self.settings.separation_radius ** 2
        push = Vector2()
        for _, offset, dist_sq in neighbors:
            if 0 < dist_sq < limit_sq:
                push += -offset / dist_sq
        return self._steer(boid, push)

    def alignment(self, boid: Boid, neighbors: list) -> Vector2:
        """Сила выравнивания: повернуть по средней скорости соседей."""
        if not neighbors:
            return Vector2()
        average = Vector2()
        for other, _, _ in neighbors:
            average += other.velocity
        return self._steer(boid, average / len(neighbors))

    def cohesion(self, boid: Boid, neighbors: list) -> Vector2:
        """Сила сплочения: лететь к центру масс соседей.

        Центр масс считается через среднее смещение до соседей, а не
        через среднее координат: так он верно находится и тогда, когда
        группа «разрезана» краем экрана.
        """
        if not neighbors:
            return Vector2()
        center = Vector2()
        for _, offset, _ in neighbors:
            center += offset
        return self._steer(boid, center / len(neighbors))

    def forces(self, boid: Boid, neighbors: list) -> dict[str, Vector2]:
        """Вернуть все три силы для бойда без учёта весов."""
        return {
            "separation": self.separation(boid, neighbors),
            "alignment": self.alignment(boid, neighbors),
            "cohesion": self.cohesion(boid, neighbors),
        }

    # ------------------------------------------------------------------
    # Шаг симуляции
    # ------------------------------------------------------------------
    def step(self) -> None:
        """Продвинуть симуляцию на один кадр.

        Сначала силы считаются для всех бойдов по «старым» положениям,
        и только потом все бойды двигаются. Иначе бойды, обработанные
        раньше, влияли бы на остальных уже из нового положения.
        """
        s = self.settings
        grid_data = self._build_grid()
        for boid in self.boids:
            neighbors = self.neighbors(boid, grid_data)
            for name, force in self.forces(boid, neighbors).items():
                weight = s.weight(name)
                if weight:
                    boid.apply_force(force * weight)
        for boid in self.boids:
            boid.update(s.max_speed, s.min_speed)
            boid.wrap(self.width, self.height)
