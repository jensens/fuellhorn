"""UI-Test spezifische Konfiguration.

NiceGUI Testing Plugin wird nur hier geladen, nicht für Unit Tests.
"""

pytest_plugins = ["nicegui.testing.plugin"]
