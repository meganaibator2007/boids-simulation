"""Двумерный вектор для расчёта движения бойдов."""

from __future__ import annotations

import math


class Vector2:
    """Вектор на плоскости с базовыми операциями линейной алгебры.

    Класс неизменяемый по смыслу: все методы возвращают новый вектор,
    кроме оператора ``+=``, который нужен для быстрого накопления сумм.
    """

    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        """Создать вектор с координатами ``(x, y)``."""
        self.x = float(x)
        self.y = float(y)

    @classmethod
    def from_angle(cls, angle: float, length: float = 1.0) -> Vector2:
        """Создать вектор заданной длины, повёрнутый на ``angle`` радиан."""
        return cls(math.cos(angle) * length, math.sin(angle) * length)

    def __add__(self, other: Vector2) -> Vector2:
        return Vector2(self.x + other.x, self.y + other.y)

    def __iadd__(self, other: Vector2) -> Vector2:
        self.x += other.x
        self.y += other.y
        return self

    def __sub__(self, other: Vector2) -> Vector2:
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vector2:
        return Vector2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> Vector2:
        return Vector2(self.x / scalar, self.y / scalar)

    def __neg__(self) -> Vector2:
        return Vector2(-self.x, -self.y)

    def __repr__(self) -> str:
        return f"Vector2({self.x:.3f}, {self.y:.3f})"

    def length_squared(self) -> float:
        """Вернуть квадрат длины (быстрее, чем длина: без корня)."""
        return self.x * self.x + self.y * self.y

    def length(self) -> float:
        """Вернуть длину вектора."""
        return math.hypot(self.x, self.y)

    def angle(self) -> float:
        """Вернуть угол наклона вектора к оси X в радианах."""
        return math.atan2(self.y, self.x)

    def normalized(self) -> Vector2:
        """Вернуть единичный вектор того же направления.

        Для нулевого вектора возвращается нулевой вектор.
        """
        length = self.length()
        if length == 0:
            return Vector2()
        return Vector2(self.x / length, self.y / length)

    def with_length(self, length: float) -> Vector2:
        """Вернуть вектор того же направления, но заданной длины."""
        return self.normalized() * length

    def limited(self, max_length: float) -> Vector2:
        """Вернуть вектор, длина которого не превышает ``max_length``."""
        if self.length_squared() > max_length * max_length:
            return self.with_length(max_length)
        return Vector2(self.x, self.y)

    def copy(self) -> Vector2:
        """Вернуть копию вектора."""
        return Vector2(self.x, self.y)
