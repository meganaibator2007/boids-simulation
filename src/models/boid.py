"""Модель одного бойда — «птицы» в стае."""

from __future__ import annotations

from src.models.vector import Vector2


class Boid:
    """Одна особь стаи: положение, скорость и накопленное ускорение."""

    __slots__ = ("position", "velocity", "acceleration")

    def __init__(self, position: Vector2, velocity: Vector2) -> None:
        """Создать бойда в точке ``position`` со скоростью ``velocity``."""
        self.position = position
        self.velocity = velocity
        self.acceleration = Vector2()

    @property
    def heading(self) -> float:
        """Направление движения в радианах."""
        return self.velocity.angle()

    def apply_force(self, force: Vector2) -> None:
        """Добавить силу к ускорению текущего шага (масса бойда = 1)."""
        self.acceleration += force

    def update(self, max_speed: float, min_speed: float) -> None:
        """Сделать один шаг интегрирования движения (метод Эйлера).

        Скорость ограничивается сверху ``max_speed``, а снизу —
        ``min_speed``, чтобы бойды не зависали на месте: живые птицы
        не умеют висеть в воздухе.
        """
        velocity = (self.velocity + self.acceleration).limited(max_speed)
        if velocity.length_squared() < min_speed * min_speed:
            velocity = velocity.with_length(min_speed)
        self.velocity = velocity
        self.position = self.position + velocity
        self.acceleration = Vector2()

    def wrap(self, width: float, height: float) -> None:
        """Перенести бойда на противоположный край (тороидальный мир)."""
        self.position = Vector2(self.position.x % width,
                                self.position.y % height)
