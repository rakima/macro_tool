import numpy as np
import pytest

from app.models import Region
from app.ui.main_window import UiDependencyError
from app.ui.region_selector import Point, RegionSelectionError, crop_image_by_region, region_from_points


def test_region_from_points_handles_down_right_drag():
    assert region_from_points(Point(10, 20), Point(30, 50)) == Region(
        x=10,
        y=20,
        width=20,
        height=30,
    )


def test_region_from_points_applies_virtual_origin():
    assert region_from_points(Point(10, 20), Point(30, 50), origin=Point(-1920, 0)) == Region(
        x=-1910,
        y=20,
        width=20,
        height=30,
    )


def test_region_from_points_handles_up_left_drag():
    assert region_from_points(Point(30, 50), Point(10, 20)) == Region(
        x=10,
        y=20,
        width=20,
        height=30,
    )


def test_region_from_points_rejects_empty_region():
    with pytest.raises(RegionSelectionError, match="width and height"):
        region_from_points(Point(10, 20), Point(10, 20))


def test_crop_image_by_region_uses_virtual_origin():
    image = np.arange(5 * 6 * 3, dtype=np.uint8).reshape((5, 6, 3))

    cropped = crop_image_by_region(
        image,
        Region(x=-8, y=21, width=3, height=2),
        origin=Point(-10, 20),
    )

    np.testing.assert_array_equal(cropped, image[1:3, 2:5])


def test_crop_image_by_region_rejects_outside_region():
    image = np.zeros((5, 6, 3), dtype=np.uint8)

    with pytest.raises(RegionSelectionError, match="outside"):
        crop_image_by_region(image, Region(x=5, y=0, width=2, height=2))


def test_create_region_selector_raises_clear_error_without_pyside6(monkeypatch):
    import app.ui.region_selector as region_selector

    def fail_import():
        raise UiDependencyError("PySide6 is not installed")

    monkeypatch.setattr(region_selector, "import_qt_modules", fail_import)

    with pytest.raises(UiDependencyError, match="PySide6"):
        region_selector.create_region_selector(np.zeros((10, 10, 3), dtype=np.uint8))


def test_import_qt_modules_returns_required_names_when_pyside6_is_available():
    pytest.importorskip("PySide6", reason="PySide6 is not installed")

    from app.ui.region_selector import import_qt_modules

    qt = import_qt_modules()

    assert "QDialog" in qt
    assert "QPixmap" in qt
    assert "QScrollArea" in qt
