"""Точка входа: запуск симуляции стаи «Бойды»."""

from src.app import App


def main() -> None:
    """Создать приложение и запустить главный цикл."""
    App().run()


if __name__ == "__main__":
    main()
