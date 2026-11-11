"""Small helpers for predictable Kivy label alignment."""

from kivy.uix.label import Label


def align_label(label: Label, *, halign: str = "left", valign: str = "middle") -> Label:
    label.halign = halign
    label.valign = valign
    label.text_size = label.size
    label.bind(size=lambda widget, size: setattr(widget, "text_size", size))
    return label
