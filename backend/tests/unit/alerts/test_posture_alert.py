from posture_detector.alerts.posture_alert import update_posture_alert, update_break_reminder
from posture_detector.classification import GOOD_POSTURE, MILD_SLOUCH, SEVERE_SLOUCH

def test_update_posture_alert_reset():
    start_time, warning, msg = update_posture_alert(GOOD_POSTURE, 10.0, 25.0)
    assert start_time is None
    assert warning is False
    assert msg is None

def test_update_posture_alert_start():
    start_time, warning, msg = update_posture_alert(MILD_SLOUCH, None, 10.0)
    assert start_time == 10.0
    assert warning is False

def test_update_posture_alert_trigger():
    start_time, warning, msg = update_posture_alert(SEVERE_SLOUCH, 10.0, 25.0, alert_delay_seconds=10.0)
    assert start_time == 10.0
    assert warning is True
    assert msg is not None

def test_update_break_reminder_trigger():
    start_time, show_break, msg = update_break_reminder(GOOD_POSTURE, 10.0, 3000.0, break_delay_seconds=2700.0)
    assert start_time == 10.0
    assert show_break is True
    assert msg is not None

def test_update_break_reminder_reset():
    start_time, show_break, msg = update_break_reminder("No pose detected", 10.0, 3000.0)
    assert start_time is None
    assert show_break is False
