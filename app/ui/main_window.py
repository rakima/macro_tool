"""Main window."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from dataclasses import replace

from app.models import RuleSet
from app.rule_operations import (
    add_rule,
    duplicate_rule,
    make_image_path_relative,
    make_rule_set_image_paths_relative,
    move_rule,
    reorder_rules,
    remove_rule,
    replace_rule,
)
from app.runner import MacroRunner, RuleRunResult, RunnerCycleResult
from app.storage import RuleStorageError, save_rules
from app.system import is_windows_admin


class UiDependencyError(RuntimeError):
    """Raised when GUI dependencies are unavailable."""


def rectangles_overlap(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
) -> bool:
    """Return whether two x/y/width/height rectangles overlap."""
    first_x, first_y, first_width, first_height = first
    second_x, second_y, second_width, second_height = second

    return (
        first_x < second_x + second_width
        and first_x + first_width > second_x
        and first_y < second_y + second_height
        and first_y + first_height > second_y
    )


def is_check_area_position(x: int, check_area_width: int = 28) -> bool:
    """Return whether a list click x-position is inside the checkbox area."""
    return x <= check_area_width


def format_score_percent(score: float) -> str:
    """Format an OpenCV match score as a percentage."""
    return f"{score * 100:.1f}%"


def format_rule_test_result(result: RuleRunResult | None, confidence: float) -> list[str]:
    """Format the latest test detection result for the rule summary panel."""
    if result is None:
        return ["Last Test: not run"]

    confidence_text = format_score_percent(confidence)
    if result.error:
        return [
            "Last Test: error",
            f"Error: {result.error}",
        ]

    if result.matched and result.match is not None:
        score_text = format_score_percent(result.match.score)
        return [
            f"Last Test: matched ({score_text} >= {confidence_text})",
            f"Match: x={result.match.x}, y={result.match.y}, center=({result.match.center_x}, {result.match.center_y})",
        ]

    if result.score is not None:
        score_text = format_score_percent(result.score)
        return [f"Last Test: below threshold ({score_text} < {confidence_text})"]

    return ["Last Test: not matched"]


def import_qt_widgets():
    try:
        from PySide6.QtWidgets import (  # type: ignore[import-not-found]
            QDialog,
            QFrame,
            QHBoxLayout,
            QLabel,
            QListWidget,
            QListWidgetItem,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QPlainTextEdit,
            QSizePolicy,
            QSplitter,
            QVBoxLayout,
            QWidget,
        )
        from PySide6.QtCore import QTimer, Qt  # type: ignore[import-not-found]
    except ImportError as error:
        raise UiDependencyError("PySide6 is not installed") from error

    return {
        "QDialog": QDialog,
        "QFrame": QFrame,
        "QHBoxLayout": QHBoxLayout,
        "QLabel": QLabel,
        "QListWidget": QListWidget,
        "QListWidgetItem": QListWidgetItem,
        "QMainWindow": QMainWindow,
        "QMessageBox": QMessageBox,
        "QPushButton": QPushButton,
        "QPlainTextEdit": QPlainTextEdit,
        "QSizePolicy": QSizePolicy,
        "QSplitter": QSplitter,
        "QTimer": QTimer,
        "QVBoxLayout": QVBoxLayout,
        "QWidget": QWidget,
        "Qt": Qt,
    }


def create_main_window(rule_set: RuleSet, rules_path: str | Path | None = None):
    """Create the main window.

    PySide6 is imported lazily so the core package remains testable in
    environments where GUI dependencies are not installed yet.
    """
    qt = import_qt_widgets()
    Qt = qt["Qt"]
    QDialog = qt["QDialog"]
    QFrame = qt["QFrame"]
    QHBoxLayout = qt["QHBoxLayout"]
    QLabel = qt["QLabel"]
    QListWidget = qt["QListWidget"]
    QListWidgetItem = qt["QListWidgetItem"]
    QMainWindow = qt["QMainWindow"]
    QMessageBox = qt["QMessageBox"]
    QPushButton = qt["QPushButton"]
    QPlainTextEdit = qt["QPlainTextEdit"]
    QSizePolicy = qt["QSizePolicy"]
    QSplitter = qt["QSplitter"]
    QTimer = qt["QTimer"]
    QVBoxLayout = qt["QVBoxLayout"]
    QWidget = qt["QWidget"]

    class RuleListWidget(QListWidget):
        def __init__(self) -> None:
            super().__init__()
            self.on_reordered = None

        def mouseDoubleClickEvent(self, event) -> None:
            position = event.position().toPoint()
            if self.itemAt(position) is not None and is_check_area_position(position.x()):
                event.accept()
                return

            super().mouseDoubleClickEvent(event)

        def dropEvent(self, event) -> None:
            before_order = self.rule_order()
            super().dropEvent(event)
            after_order = self.rule_order()
            if after_order != before_order and callable(self.on_reordered):
                self.on_reordered(after_order)

        def rule_order(self) -> list[int]:
            return [self.item(row).data(Qt.UserRole) for row in range(self.count())]

    class MainWindow(QMainWindow):
        def __init__(self, rules: RuleSet, path: str | Path | None = None) -> None:
            super().__init__()
            self.rule_set = rules
            self.rules_path = Path(path) if path is not None else None
            self.runner = None
            self.screenshot_provider = None
            self.is_running = False
            self.is_tick_running = False
            self.is_loading_rules = False
            self.last_rule_log_states = {}
            self.last_test_results = {}
            self.setWindowTitle("Macro Tool")
            self.resize(980, 680)
            self._build_ui()
            self.run_timer = QTimer(self)
            self.run_timer.setInterval(500)
            self.run_timer.timeout.connect(self._run_loop_tick)
            self._load_rules()
            self.append_log(f"Loaded {len(self.rule_set.rules)} rule(s).")
            self._append_environment_hints()

        def _build_ui(self) -> None:
            root = QWidget()
            root_layout = QVBoxLayout(root)
            root_layout.setContentsMargins(12, 12, 12, 12)
            root_layout.setSpacing(10)

            toolbar = QHBoxLayout()
            toolbar.setSpacing(8)
            self.status_label = QLabel("Stopped")
            self.status_label.setObjectName("statusLabel")
            toolbar.addWidget(self.status_label)
            toolbar.addStretch(1)

            self.test_button = QPushButton("Test Detection")
            self.start_button = QPushButton("Start")
            self.stop_button = QPushButton("Stop")
            self.stop_button.setEnabled(False)
            self.test_button.clicked.connect(self._run_test_detection)
            self.start_button.clicked.connect(self._start_running)
            self.stop_button.clicked.connect(self._stop_running)
            toolbar.addWidget(self.test_button)
            toolbar.addWidget(self.start_button)
            toolbar.addWidget(self.stop_button)
            root_layout.addLayout(toolbar)

            splitter = QSplitter(Qt.Horizontal)
            splitter.setChildrenCollapsible(False)
            root_layout.addWidget(splitter, 1)

            left_panel = QFrame()
            left_layout = QVBoxLayout(left_panel)
            left_layout.setContentsMargins(0, 0, 8, 0)
            left_layout.setSpacing(8)
            left_layout.addWidget(QLabel("Rules"))

            self.rule_list = RuleListWidget()
            self.rule_list.setMinimumWidth(280)
            self.rule_list.currentRowChanged.connect(self._show_rule_summary)
            self.rule_list.itemChanged.connect(self._on_rule_item_changed)
            self.rule_list.itemDoubleClicked.connect(self._open_rule_item_editor)
            self.rule_list.on_reordered = self._on_rule_list_reordered
            self.rule_list.setDragDropMode(QListWidget.InternalMove)
            self.rule_list.setDefaultDropAction(Qt.MoveAction)
            self.rule_list.setDropIndicatorShown(True)
            left_layout.addWidget(self.rule_list, 1)

            rule_buttons = QHBoxLayout()
            self.add_button = QPushButton("Add")
            self.edit_button = QPushButton("Edit")
            self.duplicate_button = QPushButton("Duplicate")
            self.delete_button = QPushButton("Delete")
            self.edit_button.setEnabled(False)
            self.duplicate_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.add_button.clicked.connect(self._open_new_rule_editor)
            self.edit_button.clicked.connect(self._open_selected_rule_editor)
            self.duplicate_button.clicked.connect(self._duplicate_selected_rule)
            self.delete_button.clicked.connect(self._delete_selected_rule)
            rule_buttons.addWidget(self.add_button)
            rule_buttons.addWidget(self.edit_button)
            rule_buttons.addWidget(self.duplicate_button)
            rule_buttons.addWidget(self.delete_button)
            left_layout.addLayout(rule_buttons)

            move_buttons = QHBoxLayout()
            self.move_up_button = QPushButton("Up")
            self.move_down_button = QPushButton("Down")
            self.move_up_button.setEnabled(False)
            self.move_down_button.setEnabled(False)
            self.move_up_button.clicked.connect(self._move_selected_rule_up)
            self.move_down_button.clicked.connect(self._move_selected_rule_down)
            move_buttons.addWidget(self.move_up_button)
            move_buttons.addWidget(self.move_down_button)
            left_layout.addLayout(move_buttons)
            splitter.addWidget(left_panel)

            right_panel = QWidget()
            right_layout = QVBoxLayout(right_panel)
            right_layout.setContentsMargins(8, 0, 0, 0)
            right_layout.setSpacing(8)
            right_layout.addWidget(QLabel("Selected Rule"))

            self.summary_label = QLabel("No rule selected.")
            self.summary_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.summary_label.setWordWrap(True)
            self.summary_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            right_layout.addWidget(self.summary_label, 1)
            splitter.addWidget(right_panel)
            splitter.setSizes([360, 620])

            root_layout.addWidget(QLabel("Log"))
            self.log_view = QPlainTextEdit()
            self.log_view.setReadOnly(True)
            self.log_view.setMaximumBlockCount(500)
            root_layout.addWidget(self.log_view, 0)

            self.setCentralWidget(root)

        def _load_rules(self) -> None:
            self.is_loading_rules = True
            self.rule_list.clear()
            for index, rule in enumerate(self.rule_set.rules):
                item = QListWidgetItem(rule.name)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled)
                item.setData(Qt.UserRole, index)
                item.setCheckState(Qt.Checked if rule.enabled else Qt.Unchecked)
                self.rule_list.addItem(item)
            self.is_loading_rules = False

            if self.rule_set.rules:
                self.rule_list.setCurrentRow(0)

        def _show_rule_summary(self, row: int) -> None:
            self._update_rule_buttons(row)
            if row < 0:
                self.summary_label.setText("No rule selected.")
                return

            rule = self.rule_set.rules[row]
            region = rule.region
            offset = rule.action.offset
            test_result_lines = format_rule_test_result(
                self.last_test_results.get(rule.name),
                rule.confidence,
            )
            self.summary_label.setText(
                "\n".join(
                    [
                        f"Name: {rule.name}",
                        f"Enabled: {rule.enabled}",
                        f"Image: {rule.image}",
                        f"Region: x={region.x}, y={region.y}, width={region.width}, height={region.height}",
                        f"Confidence: {rule.confidence}",
                        f"Action: {rule.action.type} / {rule.action.button}",
                        f"Offset: x={offset.x}, y={offset.y}",
                        f"Cooldown: {rule.cooldown}s",
                        "",
                        *test_result_lines,
                    ]
                )
            )

        def append_log(self, message: str) -> None:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_view.appendPlainText(f"[{timestamp}] {message}")

        def _append_environment_hints(self) -> None:
            if is_windows_admin():
                self.append_log("Running with administrator privileges.")
            else:
                self.append_log(
                    "Running without administrator privileges. "
                    "If clicks do not affect an elevated target app, run this tool with the same privilege level."
                )

        def _open_new_rule_editor(self) -> None:
            if self.is_running:
                return
            self._open_rule_editor(None, None)

        def _open_selected_rule_editor(self) -> None:
            if self.is_running:
                return
            row = self.rule_list.currentRow()
            if row < 0:
                return
            self._open_rule_editor(self.rule_set.rules[row], row)

        def _open_rule_item_editor(self, item) -> None:
            if self.is_running:
                return
            row = self.rule_list.row(item)
            if row < 0:
                return
            self._open_rule_editor(self.rule_set.rules[row], row)

        def _open_rule_editor(self, rule, index) -> None:
            from app.ui.rule_editor import create_rule_editor

            base_dir = self.rules_path.parent if self.rules_path is not None else None
            dialog = create_rule_editor(rule, parent=self, base_dir=base_dir)
            if dialog.exec() != QDialog.Accepted:
                return

            try:
                edited_rule = dialog.rule()
                if self.rules_path is not None:
                    edited_rule = make_image_path_relative(edited_rule, self.rules_path.parent)
                if index is None:
                    self.rule_set = add_rule(self.rule_set, edited_rule)
                    selected_row = len(self.rule_set.rules) - 1
                else:
                    self.rule_set = replace_rule(self.rule_set, index, edited_rule)
                    selected_row = index
                self._save_rules()
            except Exception as error:
                QMessageBox.warning(self, "Could not save rule", str(error))
                self.append_log(f"Rule save failed: {error}")
                return

            self.last_test_results = {}
            self._load_rules()
            self.rule_list.setCurrentRow(selected_row)
            self.append_log(f"Saved rule: {edited_rule.name}")

        def _duplicate_selected_rule(self) -> None:
            if self.is_running:
                return
            row = self.rule_list.currentRow()
            if row < 0:
                return

            try:
                self.rule_set = duplicate_rule(self.rule_set, row)
                self._save_rules()
            except Exception as error:
                QMessageBox.warning(self, "Could not duplicate rule", str(error))
                self.append_log(f"Rule duplicate failed: {error}")
                return

            duplicated_rule = self.rule_set.rules[row + 1]
            self._load_rules()
            self.rule_list.setCurrentRow(row + 1)
            self.append_log(f"Duplicated rule: {duplicated_rule.name}")

        def _delete_selected_rule(self) -> None:
            if self.is_running:
                return
            row = self.rule_list.currentRow()
            if row < 0:
                return

            rule = self.rule_set.rules[row]
            answer = QMessageBox.question(
                self,
                "Delete rule",
                f"Delete rule '{rule.name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

            try:
                self.rule_set = remove_rule(self.rule_set, row)
                self._save_rules()
            except Exception as error:
                QMessageBox.warning(self, "Could not delete rule", str(error))
                self.append_log(f"Rule delete failed: {error}")
                return

            self.last_test_results = {}
            self._load_rules()
            if self.rule_set.rules:
                self.rule_list.setCurrentRow(min(row, len(self.rule_set.rules) - 1))
            else:
                self._show_rule_summary(-1)
            self.append_log(f"Deleted rule: {rule.name}")

        def _move_selected_rule_up(self) -> None:
            self._move_selected_rule(-1)

        def _move_selected_rule_down(self) -> None:
            self._move_selected_rule(1)

        def _move_selected_rule(self, direction: int) -> None:
            if self.is_running:
                return
            row = self.rule_list.currentRow()
            target_row = row + direction
            if row < 0 or target_row < 0 or target_row >= len(self.rule_set.rules):
                return

            rule_name = self.rule_set.rules[row].name
            try:
                self.rule_set = move_rule(self.rule_set, row, target_row)
                self._save_rules()
            except Exception as error:
                QMessageBox.warning(self, "Could not move rule", str(error))
                self.append_log(f"Rule move failed: {error}")
                return

            self._load_rules()
            self.rule_list.setCurrentRow(target_row)
            self.append_log(f"Moved rule: {rule_name}")

        def _on_rule_list_reordered(self, order: list[int]) -> None:
            if self.is_loading_rules:
                return
            if self.is_running:
                self._load_rules()
                return

            current_item = self.rule_list.currentItem()
            selected_original_index = current_item.data(Qt.UserRole) if current_item is not None else None
            try:
                self.rule_set = reorder_rules(self.rule_set, order)
                self._save_rules()
            except Exception as error:
                QMessageBox.warning(self, "Could not reorder rules", str(error))
                self.append_log(f"Rule reorder failed: {error}")
                self._load_rules()
                return

            selected_row = order.index(selected_original_index) if selected_original_index in order else 0
            self._load_rules()
            self.rule_list.setCurrentRow(selected_row)
            self.append_log("Reordered rules.")

        def _on_rule_item_changed(self, item) -> None:
            if self.is_loading_rules:
                return
            row = self.rule_list.row(item)
            if row < 0:
                return

            rule = self.rule_set.rules[row]
            enabled = item.checkState() == Qt.Checked
            if rule.enabled == enabled:
                return
            if self.is_running:
                self.is_loading_rules = True
                item.setCheckState(Qt.Checked if rule.enabled else Qt.Unchecked)
                self.is_loading_rules = False
                return

            updated_rule = replace(rule, enabled=enabled)
            try:
                self.rule_set = replace_rule(self.rule_set, row, updated_rule)
                self._save_rules()
            except Exception as error:
                QMessageBox.warning(self, "Could not update rule", str(error))
                self.append_log(f"Rule update failed: {error}")
                return

            self.rule_list.setCurrentRow(row)
            self.append_log(f"{'Enabled' if updated_rule.enabled else 'Disabled'} rule: {updated_rule.name}")

        def _save_rules(self) -> None:
            if self.rules_path is None:
                return

            try:
                save_rules(
                    self.rules_path,
                    make_rule_set_image_paths_relative(self.rule_set, self.rules_path.parent),
                )
            except RuleStorageError:
                raise

        def _run_test_detection(self) -> None:
            if self.is_running:
                return
            from app.detector import TemplateDetector
            from app.screenshot import PyAutoGuiScreenshotProvider

            base_dir = self.rules_path.parent if self.rules_path is not None else Path(".")
            runner = MacroRunner(
                rules=self.rule_set.rules,
                detector=TemplateDetector(base_dir=base_dir),
            )

            self.append_log("Test detection started.")
            result = runner.capture_and_test_once(PyAutoGuiScreenshotProvider())
            self._append_test_detection_result(result)

        def _append_test_detection_result(self, result: RunnerCycleResult) -> None:
            if not result.results:
                self.append_log("No enabled rules to test.")
                return

            matched_count = sum(1 for item in result.results if item.matched)
            error_count = sum(1 for item in result.results if item.error)
            not_matched_count = len(result.results) - matched_count - error_count

            for item in result.results:
                self.last_test_results[item.rule_name] = item
                if item.error:
                    self.append_log(f"[{item.rule_name}] error: {item.error}")
                elif item.matched and item.match is not None:
                    self.append_log(
                        f"[{item.rule_name}] matched score={item.match.score:.3f} "
                        f"({item.match.score * 100:.1f}%) "
                        f"at x={item.match.x}, y={item.match.y} "
                        f"center=({item.match.center_x}, {item.match.center_y})"
                    )
                elif item.score is not None:
                    self.append_log(
                        f"[{item.rule_name}] not matched best_score={item.score:.3f} "
                        f"({item.score * 100:.1f}%)"
                    )
                else:
                    self.append_log(f"[{item.rule_name}] not matched")

            self.append_log(
                "Test detection completed: "
                f"matched={matched_count}, not_matched={not_matched_count}, errors={error_count}"
            )
            self._show_rule_summary(self.rule_list.currentRow())

        def _start_running(self) -> None:
            enabled_rules = [rule for rule in self.rule_set.rules if rule.enabled]
            if not enabled_rules:
                self.append_log("No enabled rules to run.")
                return
            if not self._confirm_self_region_overlap(enabled_rules):
                return

            from app.detector import TemplateDetector
            from app.screenshot import PyAutoGuiScreenshotProvider

            base_dir = self.rules_path.parent if self.rules_path is not None else Path(".")
            self.runner = MacroRunner(
                rules=self.rule_set.rules,
                detector=TemplateDetector(base_dir=base_dir),
            )
            self.screenshot_provider = PyAutoGuiScreenshotProvider()
            self.last_rule_log_states = {}
            self._set_running_state(True)
            self.append_log(
                f"Macro started. enabled_rules={len(enabled_rules)}, interval={self.run_timer.interval()}ms"
            )
            self.run_timer.start()

        def _confirm_self_region_overlap(self, enabled_rules) -> bool:
            own_region = self._window_screen_region()
            overlapping_rules = []
            for rule in enabled_rules:
                rule_region = (
                    rule.region.x,
                    rule.region.y,
                    rule.region.width,
                    rule.region.height,
                )
                if rectangles_overlap(own_region, rule_region):
                    overlapping_rules.append(rule.name)

            if not overlapping_rules:
                return True

            names = ", ".join(overlapping_rules[:5])
            if len(overlapping_rules) > 5:
                names += f", and {len(overlapping_rules) - 5} more"

            answer = QMessageBox.question(
                self,
                "Search region overlaps Macro Tool",
                "One or more enabled rules search inside the Macro Tool window. "
                "This can make the tool click its own controls.\n\n"
                f"Rules: {names}\n\n"
                "Start anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                self.append_log("Macro start canceled: rule region overlaps Macro Tool window.")
                return False
            return True

        def _window_screen_region(self) -> tuple[int, int, int, int]:
            geometry = self.frameGeometry()
            return (
                geometry.x(),
                geometry.y(),
                geometry.width(),
                geometry.height(),
            )

        def _stop_running(self) -> None:
            if not self.is_running:
                return

            self.run_timer.stop()
            self.runner = None
            self.screenshot_provider = None
            self.is_tick_running = False
            self.last_rule_log_states = {}
            self._set_running_state(False)
            self.append_log("Macro stopped.")

        def _set_running_state(self, running: bool) -> None:
            self.is_running = running
            self.status_label.setText("Running" if running else "Stopped")
            self.start_button.setEnabled(not running)
            self.stop_button.setEnabled(running)
            self.test_button.setEnabled(not running)
            self.add_button.setEnabled(not running)
            self.rule_list.setDragDropMode(QListWidget.NoDragDrop if running else QListWidget.InternalMove)
            self._update_rule_buttons(self.rule_list.currentRow())

        def _update_rule_buttons(self, row: int) -> None:
            selected = row >= 0
            can_edit = selected and not self.is_running
            self.edit_button.setEnabled(can_edit)
            self.duplicate_button.setEnabled(can_edit)
            self.delete_button.setEnabled(can_edit)
            self.move_up_button.setEnabled(can_edit and row > 0)
            self.move_down_button.setEnabled(can_edit and row < len(self.rule_set.rules) - 1)

        def _run_loop_tick(self) -> None:
            if (
                not self.is_running
                or self.is_tick_running
                or self.runner is None
                or self.screenshot_provider is None
            ):
                return

            self.is_tick_running = True
            try:
                result = self.runner.capture_and_run_once(self.screenshot_provider)
                self._append_run_result(result)
            finally:
                self.is_tick_running = False

        def _append_run_result(self, result: RunnerCycleResult) -> None:
            for item in result.results:
                state = self._run_result_state(item)
                if item.error:
                    self._append_state_change_log(item.rule_name, state, f"[{item.rule_name}] error: {item.error}")
                elif item.triggered and item.click_target is not None and item.match is not None:
                    self.append_log(
                        f"[{item.rule_name}] clicked x={item.click_target.x}, y={item.click_target.y} "
                        f"match=({item.match.x}, {item.match.y}) "
                        f"score={item.match.score:.3f}"
                    )
                    self.last_rule_log_states[item.rule_name] = state
                elif item.skipped_cooldown:
                    self._append_state_change_log(item.rule_name, state, f"[{item.rule_name}] cooldown")
                else:
                    self._append_state_change_log(item.rule_name, state, f"[{item.rule_name}] not matched")

        def _run_result_state(self, item) -> str:
            if item.error:
                return f"error:{item.error}"
            if item.triggered:
                return "triggered"
            if item.skipped_cooldown:
                return "cooldown"
            if item.matched:
                return "matched"
            return "not_matched"

        def _append_state_change_log(self, rule_name: str, state: str, message: str) -> None:
            if self.last_rule_log_states.get(rule_name) == state:
                return

            self.last_rule_log_states[rule_name] = state
            self.append_log(message)

        def closeEvent(self, event) -> None:
            if self.is_running:
                self._stop_running()
            super().closeEvent(event)

    return MainWindow(rule_set, rules_path)
