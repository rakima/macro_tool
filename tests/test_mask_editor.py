from pathlib import Path

from app.ui.mask_editor import default_masked_image_path


def test_default_masked_image_path_adds_masked_suffix():
    assert default_masked_image_path("image/button.png") == Path("image/button.masked.png")


def test_default_masked_image_path_keeps_existing_masked_name():
    assert default_masked_image_path("image/button.masked.png") == Path("image/button.masked.png")


def test_default_masked_image_path_normalizes_png_masked_name():
    assert default_masked_image_path("image/button.png.masked.png") == Path("image/button.masked.png")


def test_default_masked_image_path_replaces_source_extension():
    assert default_masked_image_path("image/button.jpg") == Path("image/button.masked.png")
