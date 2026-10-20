"""Тесты математической модели: вектор, бойд и правила стаи."""

import math
import random
import unittest

from src.models.boid import Boid
from src.models.flock import Flock, FlockSettings, wrap_delta
from src.models.vector import Vector2


class VectorTest(unittest.TestCase):
    """Проверка операций с векторами."""

    def test_arithmetic(self):
        """Сложение, вычитание и умножение на число."""
        v = Vector2(1, 2) + Vector2(3, 4) * 2 - Vector2(1, 1)
        self.assertEqual((v.x, v.y), (6.0, 9.0))

    def test_length_and_normalized(self):
        """Длина вектора и длина единичного вектора."""
        v = Vector2(3, 4)
        self.assertAlmostEqual(v.length(), 5)
        self.assertAlmostEqual(v.normalized().length(), 1)

    def test_zero_vector_normalized_is_zero(self):
        """Нормирование нулевого вектора не падает."""
        self.assertEqual(Vector2().normalized().length(), 0)

    def test_limited(self):
        """Длинный вектор укорачивается, короткий не меняется."""
        self.assertAlmostEqual(Vector2(30, 40).limited(5).length(), 5)
        self.assertAlmostEqual(Vector2(1, 1).limited(5).length(),
                               math.sqrt(2))

    def test_from_angle(self):
        """Вектор по углу 90 градусов смотрит вдоль оси Y."""
        v = Vector2.from_angle(math.pi / 2, 2)
        self.assertAlmostEqual(v.x, 0)
        self.assertAlmostEqual(v.y, 2)


class BoidTest(unittest.TestCase):
    """Проверка движения одного бойда."""

    def test_speed_is_limited(self):
        """Скорость не превышает максимальную."""
        boid = Boid(Vector2(), Vector2(1, 0))
        boid.apply_force(Vector2(100, 0))
        boid.update(max_speed=3, min_speed=1)
        self.assertAlmostEqual(boid.velocity.length(), 3)
        self.assertEqual(boid.acceleration.length(), 0)

    def test_minimum_speed(self):
        """Слишком медленный бойд разгоняется до минимума."""
        boid = Boid(Vector2(), Vector2(0.1, 0))
        boid.update(max_speed=3, min_speed=1)
        self.assertAlmostEqual(boid.velocity.length(), 1)

    def test_wrap(self):
        """Вылетевший за край бойд появляется с другой стороны."""
        boid = Boid(Vector2(105, -5), Vector2(1, 0))
        boid.wrap(100, 100)
        self.assertAlmostEqual(boid.position.x, 5)
        self.assertAlmostEqual(boid.position.y, 95)


class WrapDeltaTest(unittest.TestCase):
    """Проверка кратчайшего смещения в тороидальном мире."""

    def test_direct_distance(self):
        """Без перехода через край смещение не меняется."""
        self.assertAlmostEqual(wrap_delta(10, 100), 10)

    def test_distance_through_edge(self):
        """Через край смещение короче, чем через экран."""
        # От x=95 до x=5 короче пройти через край: смещение +10.
        self.assertAlmostEqual(wrap_delta(5 - 95, 100), 10)
        self.assertAlmostEqual(wrap_delta(95 - 5, 100), -10)


def make_flock(*boids, settings=None):
    """Создать стаю в мире 400x400 из заданных бойдов."""
    flock = Flock(400, 400, 0, settings=settings, rng=random.Random(1))
    flock.boids = list(boids)
    return flock


class FlockRulesTest(unittest.TestCase):
    """Проверка трёх правил Рейнольдса."""

    def test_separation_pushes_away(self):
        """Разделение отталкивает от близкого соседа."""
        me = Boid(Vector2(200, 200), Vector2(0, 1))
        other = Boid(Vector2(210, 200), Vector2(0, 1))
        flock = make_flock(me, other)
        force = flock.separation(me, flock.neighbors(me))
        self.assertLess(force.x, 0)  # сосед справа -> толкает влево

    def test_alignment_turns_to_neighbors_heading(self):
        """Выравнивание поворачивает к курсу соседа."""
        me = Boid(Vector2(200, 200), Vector2(0, 2))
        other = Boid(Vector2(230, 200), Vector2(2, 0))
        flock = make_flock(me, other)
        force = flock.alignment(me, flock.neighbors(me))
        self.assertGreater(force.x, 0)
        self.assertLess(force.y, 0)

    def test_cohesion_pulls_to_center(self):
        """Сплочение тянет к центру соседей."""
        me = Boid(Vector2(200, 200), Vector2(0, 0.0))
        others = [Boid(Vector2(240, 190), Vector2()),
                  Boid(Vector2(240, 210), Vector2())]
        flock = make_flock(me, *others)
        force = flock.cohesion(me, flock.neighbors(me))
        self.assertGreater(force.x, 0)
        self.assertAlmostEqual(force.y, 0)

    def test_cohesion_works_through_edge(self):
        """Сплочение видит соседа за краем экрана."""
        me = Boid(Vector2(395, 200), Vector2())
        other = Boid(Vector2(15, 200), Vector2())
        flock = make_flock(me, other)
        force = flock.cohesion(me, flock.neighbors(me))
        self.assertGreater(force.x, 0)  # сосед «справа» через край

    def test_force_is_limited(self):
        """Каждая сила не больше max_force."""
        me = Boid(Vector2(200, 200), Vector2(0, 3))
        other = Boid(Vector2(201, 200), Vector2(0, -3))
        flock = make_flock(me, other)
        for force in flock.forces(me, flock.neighbors(me)).values():
            self.assertLessEqual(force.length(),
                                 flock.settings.max_force + 1e-9)

    def test_no_neighbors_no_force(self):
        """Без соседей силы равны нулю."""
        me = Boid(Vector2(10, 10), Vector2(1, 0))
        far = Boid(Vector2(200, 200), Vector2(1, 0))
        flock = make_flock(me, far)
        for force in flock.forces(me, flock.neighbors(me)).values():
            self.assertEqual(force.length(), 0)

    def test_disabled_force_has_zero_weight(self):
        """Выключенная сила имеет нулевой вес."""
        settings = FlockSettings(alignment_enabled=False)
        self.assertEqual(settings.weight("alignment"), 0)
        self.assertEqual(settings.weight("cohesion"),
                         settings.cohesion_weight)


class FlockTest(unittest.TestCase):
    """Проверка стаи целиком."""

    def test_grid_neighbors_match_brute_force(self):
        """Поиск по сетке совпадает с полным перебором."""
        flock = Flock(500, 300, 150, rng=random.Random(42))
        radius = flock.settings.perception_radius
        grid = flock._build_grid()
        for boid in flock.boids:
            found = {id(other) for other, _, _ in
                     flock.neighbors(boid, grid)}
            expected = set()
            for other in flock.boids:
                if other is boid:
                    continue
                dx = wrap_delta(other.position.x - boid.position.x, 500)
                dy = wrap_delta(other.position.y - boid.position.y, 300)
                if dx * dx + dy * dy < radius * radius:
                    expected.add(id(other))
            self.assertEqual(found, expected)

    def test_step_keeps_boids_inside_and_speeds_valid(self):
        """После шагов бойды в мире, скорости в пределах."""
        flock = Flock(400, 300, 80, rng=random.Random(7))
        s = flock.settings
        for _ in range(50):
            flock.step()
        for boid in flock.boids:
            self.assertTrue(0 <= boid.position.x < 400)
            self.assertTrue(0 <= boid.position.y < 300)
            speed = boid.velocity.length()
            self.assertGreaterEqual(speed, s.min_speed - 1e-9)
            self.assertLessEqual(speed, s.max_speed + 1e-9)

    def test_alignment_orders_flock(self):
        """Со временем стая начинает лететь согласованно."""
        def order(flock):
            """Вернуть параметр порядка стаи.

            Это длина средней единичной скорости: 0 — все летят кто
            куда, 1 — все летят в одну сторону.
            """
            total = Vector2()
            for boid in flock.boids:
                total += boid.velocity.normalized()
            return total.length() / len(flock.boids)

        flock = Flock(300, 300, 60, rng=random.Random(3))
        before = order(flock)
        for _ in range(400):
            flock.step()
        self.assertGreater(order(flock), before)
        self.assertGreater(order(flock), 0.6)

    def test_set_count(self):
        """Количество бойдов меняется в обе стороны."""
        flock = Flock(300, 300, 20, rng=random.Random(0))
        flock.set_count(35)
        self.assertEqual(len(flock.boids), 35)
        flock.set_count(10)
        self.assertEqual(len(flock.boids), 10)


if __name__ == "__main__":
    unittest.main()
