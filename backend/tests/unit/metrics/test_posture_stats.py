from posture_detector.metrics.posture_stats import PostureStatisticsTracker
from posture_detector.classification import GOOD_POSTURE, MILD_SLOUCH, SEVERE_SLOUCH

def test_posture_stats_duration_accumulation():
    tracker = PostureStatisticsTracker()
    tracker.update(GOOD_POSTURE, 10.0)
    tracker.update(GOOD_POSTURE, 15.0)
    
    assert tracker.posture_durations[GOOD_POSTURE] == 5.0
    assert tracker.posture_counts[GOOD_POSTURE] == 1

def test_posture_stats_label_transitions():
    tracker = PostureStatisticsTracker()
    tracker.update(GOOD_POSTURE, 10.0)
    tracker.update(MILD_SLOUCH, 15.0)
    tracker.update(SEVERE_SLOUCH, 25.0)
    
    assert tracker.posture_durations[GOOD_POSTURE] == 5.0
    assert tracker.posture_durations[MILD_SLOUCH] == 10.0
    assert tracker.posture_counts[GOOD_POSTURE] == 1
    assert tracker.posture_counts[MILD_SLOUCH] == 1
    assert tracker.posture_counts[SEVERE_SLOUCH] == 1

def test_posture_stats_finalize():
    tracker = PostureStatisticsTracker()
    tracker.update(GOOD_POSTURE, 10.0)
    tracker.finalize(15.0)
    
    assert tracker.posture_durations[GOOD_POSTURE] == 5.0
    summary = tracker.build_daily_summary()
    assert summary["total_tracked_seconds"] == 5.0
    assert summary["good_posture_seconds"] == 5.0
