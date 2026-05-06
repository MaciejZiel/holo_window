from holowindow.config.settings import RenderSettings
from holowindow.rendering.projection import off_axis_frustum_corners, physical_eye_pose_units


def test_physical_eye_pose_scales_screen_to_scene_units():
    settings = RenderSettings(
        virtual_screen_height=6.5,
        physical_screen_width_m=0.344,
        physical_screen_height_m=0.194,
        nominal_eye_distance_m=0.55,
    )

    eye = physical_eye_pose_units(head_x=0.0, head_y=0.0, head_z=0.0, parallax=1.0, settings=settings)

    assert eye.screen_height == 6.5
    assert eye.screen_width == settings.physical_screen_width_m * (6.5 / settings.physical_screen_height_m)
    assert eye.x == 0.0
    assert eye.z == 0.0


def test_off_axis_corners_shift_opposite_to_eye_position():
    settings = RenderSettings()
    eye = physical_eye_pose_units(head_x=0.5, head_y=-0.25, head_z=0.0, parallax=1.0, settings=settings)

    ul, ur, ll, lr = off_axis_frustum_corners(eye)

    assert ul[0] < 0.0
    assert ur[0] > 0.0
    assert ul[2] > ll[2]
    assert ur[1] == eye.distance
    assert lr[1] == eye.distance
