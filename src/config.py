"""Общие настройки приложения: размеры окна, цвета, частота кадров."""

# Размер области симуляции в пикселях.
CANVAS_WIDTH = 900
CANVAS_HEIGHT = 640

# Целевая частота кадров и соответствующая задержка для root.after().
FPS = 60
FRAME_DELAY_MS = 1000 // FPS

# Начальное количество бойдов и допустимый диапазон.
DEFAULT_BOID_COUNT = 120
MIN_BOID_COUNT = 10
MAX_BOID_COUNT = 300

# Сколько бойдов добавляет один щелчок мыши.
BOIDS_PER_CLICK = 5

# Размер треугольника, изображающего бойда.
BOID_SIZE = 6

# Цветовая схема.
BACKGROUND_COLOR = "#0f1420"
TEXT_COLOR = "#d8dee9"
MUTED_TEXT_COLOR = "#7b8496"
PERCEPTION_COLOR = "#4c566a"
SEPARATION_COLOR = "#bf616a"
HIGHLIGHT_COLOR = "#ffffff"

# Подписи сил для интерфейса.
FORCE_TITLES = {
    "separation": "Разделение",
    "alignment": "Выравнивание",
    "cohesion": "Сплочение",
}

# Клавиши включения и выключения сил.
FORCE_KEYS = {
    "separation": "1",
    "alignment": "2",
    "cohesion": "3",
}
