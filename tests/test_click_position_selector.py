from app.models import Offset
from app.ui.click_position_selector import (
    clamp_image_point,
    image_point_from_offset,
    offset_from_image_point,
)


def test_offset_from_image_point_uses_image_center_as_origin():
    offset = offset_from_image_point(image_width=20, image_height=10, point_x=14, point_y=3)

    assert offset == Offset(x=4, y=-2)


def test_image_point_from_offset_uses_image_center_as_origin():
    point = image_point_from_offset(image_width=20, image_height=10, offset=Offset(x=4, y=-2))

    assert point == (14, 3)


def test_clamp_image_point_keeps_point_inside_image():
    assert clamp_image_point(image_width=20, image_height=10, point_x=-5, point_y=30) == (0, 9)
