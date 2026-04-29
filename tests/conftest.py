import sys
from unittest.mock import MagicMock

# Global mock for customtkinter - provides stubs for widget classes
mock_ctk = MagicMock()


# Create callable mocks that return MagicMock instances (not specs)
def make_mock_class():
    return lambda *args, **kwargs: MagicMock()


mock_ctk.CTkFont = make_mock_class()
mock_ctk.CTkFrame = make_mock_class()
mock_ctk.CTkLabel = make_mock_class()
mock_ctk.CTkButton = make_mock_class()
mock_ctk.CTkTextbox = make_mock_class()
mock_ctk.CTkScrollableFrame = make_mock_class()
mock_ctk.CTkSlider = make_mock_class()
mock_ctk.CTkRadioButton = make_mock_class()
mock_ctk.CTkCheckBox = make_mock_class()
mock_ctk.StringVar = make_mock_class()
mock_ctk.BooleanVar = make_mock_class()

# Create mock CTkTabview with required methods
mock_tabview = MagicMock()
mock_tabview.add = MagicMock(return_value=None)
mock_tabview.tab = MagicMock(return_value=MagicMock())
mock_tabview.pack = MagicMock()
mock_ctk.CTkTabview = lambda *args, **kwargs: mock_tabview


# CTk class that can be instantiated and subclassed with proper tkinter methods
class _MockCTk:
    def __init__(self, *args, **kwargs):
        pass

    def title(self, *args, **kwargs):
        pass

    def geometry(self, *args, **kwargs):
        pass

    def minsize(self, *args, **kwargs):
        pass

    def after(self, *args, **kwargs):
        pass

    def pack(self, *args, **kwargs):
        pass


mock_ctk.CTk = _MockCTk
mock_ctk.set_appearance_mode = MagicMock()
mock_ctk.set_default_color_theme = MagicMock()

sys.modules["customtkinter"] = mock_ctk
