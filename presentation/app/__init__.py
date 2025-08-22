"""Application package for HobbyPicker."""

# Re-export the GUI launcher so consumers can simply ``from presentation.app
# import start_app`` without needing to know the internal module layout.
from .gui import start_app

__all__ = ["start_app"]
