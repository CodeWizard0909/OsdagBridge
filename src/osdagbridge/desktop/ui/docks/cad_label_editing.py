"""
Double-click editing of dimension labels on the hand-painted 2D CAD views.

The views paint their labels themselves in paintEvent, so there are no label widgets
to click. Instead each view records the rectangle of every editable label while it
paints, and a double-click inside one of those rectangles opens a small line edit on
top of it. Read-only labels (overhang, overall width, bracing spacing) are simply
never registered, so they cannot be edited.
"""
from PySide6.QtCore import Qt, QLocale, Signal
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QLineEdit


class _LabelEditor(QLineEdit):
    """Line edit that reports Esc instead of ignoring it."""

    cancelled = Signal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancelled.emit()
            return
        super().keyPressEvent(event)


class EditableCadLabels:
    """Mixin for the CAD QWidgets. The host class declares `label_value_edited = Signal(str, str)`.

    In paintEvent the host calls `_begin_editable_labels()` first, then
    `_register_editable_label(key, rect, value)` right after drawing each editable label.
    Enter or clicking away emits label_value_edited(key, text); Esc cancels. Validating
    the value and writing it to the input dictionary is the receiver's job.
    """

    # Off by default: the Additional Inputs dialog reuses CrossSectionCADWidget as a preview.
    labels_editable = False

    def _begin_editable_labels(self):
        self._editable_labels = []

    def _register_editable_label(self, key: str, rect, value: float):
        self._editable_labels.append((rect, key, value))

    def editable_label_at(self, pos):
        """(key, rect, value) of the editable label under pos, or None."""
        for rect, key, value in getattr(self, "_editable_labels", []):
            if rect.contains(pos):
                return key, rect, value
        return None

    def mouseDoubleClickEvent(self, event):
        hit = self.editable_label_at(event.position()) if self.labels_editable else None
        if hit is None:
            super().mouseDoubleClickEvent(event)
            return
        self._open_label_editor(*hit)

    def _open_label_editor(self, key: str, rect, value: float):
        self._close_label_editor(commit=False)

        editor = _LabelEditor(self)
        validator = QDoubleValidator(0.0, 1e6, 3, editor)
        validator.setNotation(QDoubleValidator.StandardNotation)
        validator.setLocale(QLocale.c())  # always '.' as decimal point, like the input dock
        editor.setValidator(validator)
        editor.setText(f"{value:g}")

        geom = rect.toRect()
        geom.setWidth(max(geom.width(), 90))
        editor.setGeometry(geom)
        editor.editingFinished.connect(lambda: self._close_label_editor(commit=True))
        editor.cancelled.connect(lambda: self._close_label_editor(commit=False))

        self._label_editor = (editor, key)
        editor.show()
        editor.selectAll()
        editor.setFocus()

    def _close_label_editor(self, commit: bool):
        state = getattr(self, "_label_editor", None)
        if state is None:
            return
        # Clear first: hiding the editor drops focus, which fires editingFinished again.
        self._label_editor = None
        editor, key = state
        text = editor.text().strip()
        editor.hide()
        editor.deleteLater()
        if commit and text:
            self.label_value_edited.emit(key, text)
