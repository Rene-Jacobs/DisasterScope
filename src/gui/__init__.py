"""
GUI components for the Disaster Impact Analysis System.

This module provides a graphical user interface for the application
built with Tkinter, allowing users to:
- Configure search parameters for disaster analysis
- Monitor analysis progress in real-time with detailed logging
- View and export results to Excel format
- Manage API credentials and application settings

The GUI provides an intuitive interface for non-technical users while
maintaining all the functionality of the command-line interface.

Classes:
    DisasterAnalyzerApp: Main application window and controller
    RedirectText: Utility class for redirecting console output to GUI

Functions:
    main: Entry point for launching the GUI application

Example:
    To launch the GUI application:

    >>> from src.gui import main
    >>> main()

    Or run directly:

    $ python -m src.gui.gui_app
"""

# Standard library imports
from typing import Optional, TYPE_CHECKING

# Type checking imports (only imported during type checking)
if TYPE_CHECKING:
    import tkinter as tk

# Local imports
from .gui_app import DisasterAnalyzerApp, RedirectText

# Module metadata
__version__ = "1.0.0"
__author__ = "Disaster Impact Analysis Team"

# Application constants
APP_TITLE = "Disaster Impact Analyzer"
DEFAULT_WINDOW_SIZE = "900x700"
MIN_WINDOW_SIZE = (900, 700)


def main(root: Optional["tk.Tk"] = None) -> None:
    """
    Launch the GUI application.

    This function initializes and runs the main GUI application window.
    It can be called with an existing Tkinter root window or will create
    a new one if none is provided.

    Args:
        root: Optional existing Tkinter root window. If None, creates new window.

    Example:
        >>> from src.gui import main
        >>> main()  # Launches the application
    """
    # Import here to avoid Tkinter dependency issues
    import tkinter as tk

    if root is None:
        root = tk.Tk()
        root.withdraw()  # Hide the window initially

    try:
        # Initialize and configure the application
        app = DisasterAnalyzerApp(root)

        # Configure window properties
        root.title(APP_TITLE)
        root.geometry(DEFAULT_WINDOW_SIZE)
        root.minsize(*MIN_WINDOW_SIZE)

        # Center the window on screen
        root.update_idletasks()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = root.winfo_width()
        window_height = root.winfo_height()

        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        root.geometry(f"+{x}+{y}")

        # Show the window and start the main loop
        root.deiconify()
        root.mainloop()

    except Exception as e:
        import sys

        print(f"Error launching GUI application: {e}", file=sys.stderr)
        if root:
            try:
                root.destroy()
            except:
                pass
        raise


def create_app_instance(root: "tk.Tk") -> DisasterAnalyzerApp:
    """
    Create a new DisasterAnalyzerApp instance.

    This function provides a factory method for creating the main
    application instance with proper error handling.

    Args:
        root: Tkinter root window

    Returns:
        DisasterAnalyzerApp: Configured application instance

    Raises:
        RuntimeError: If application cannot be initialized
    """
    try:
        return DisasterAnalyzerApp(root)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize application: {e}")


# Export the main application class and utility functions
__all__ = [
    # Main classes
    "DisasterAnalyzerApp",
    "RedirectText",
    # Functions
    "main",
    "create_app_instance",
    # Constants
    "APP_TITLE",
    "DEFAULT_WINDOW_SIZE",
    "MIN_WINDOW_SIZE",
    # Metadata
    "__version__",
    "__author__",
]
