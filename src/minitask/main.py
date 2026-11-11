"""MiniTask application entry point."""


def main() -> None:
    """Start the Kivy application."""
    from minitask.ui.app import MiniTaskApp

    MiniTaskApp().run()


if __name__ == "__main__":
    main()
