from uuid import uuid4
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.interview_planner import (
    InterviewPlanner,
    normalize_difficulty,
    ALLOWED_TRANSITIONS,
)
from app.schemas.interview_state import InterviewState


def test_normalize_difficulty():
    assert normalize_difficulty("easy") == "Junior"
    assert normalize_difficulty("medium") == "Mid"
    assert normalize_difficulty("hard") == "Senior"
    assert normalize_difficulty("Junior") == "Junior"
    assert normalize_difficulty("Senior") == "Senior"
    assert normalize_difficulty("unknown") == "Mid"
    assert normalize_difficulty(None) == "Mid"


def test_compute_next_difficulty_promotion():
    planner = InterviewPlanner(session=MagicMock())

    # High score (>= 8.0) should promote from Junior to Mid
    state_junior = InterviewState(
        interview_id=uuid4(),
        current_difficulty="Junior",
        skills_to_test=["Python"],
        skills_tested=[],
        recent_performance=[8.5, 9.0],
    )
    assert planner._compute_next_difficulty(state_junior) == "Mid"

    # High score should promote from Mid to Senior
    state_mid = InterviewState(
        interview_id=uuid4(),
        current_difficulty="Mid",
        skills_to_test=["Python"],
        skills_tested=[],
        recent_performance=[8.0],
    )
    assert planner._compute_next_difficulty(state_mid) == "Senior"

    # High score should promote from Senior to Principal
    state_senior = InterviewState(
        interview_id=uuid4(),
        current_difficulty="Senior",
        skills_to_test=["Python"],
        skills_tested=[],
        recent_performance=[9.5],
    )
    assert planner._compute_next_difficulty(state_senior) == "Principal"

    # Principal stays Principal
    state_principal = InterviewState(
        interview_id=uuid4(),
        current_difficulty="Principal",
        skills_to_test=["Python"],
        skills_tested=[],
        recent_performance=[10.0],
    )
    assert planner._compute_next_difficulty(state_principal) == "Principal"


def test_compute_next_difficulty_demotion():
    planner = InterviewPlanner(session=MagicMock())

    # Low score (< 5.0) should demote from Principal to Senior
    state_principal = InterviewState(
        interview_id=uuid4(),
        current_difficulty="Principal",
        skills_to_test=["Python"],
        skills_tested=[],
        recent_performance=[4.0, 3.5],
    )
    assert planner._compute_next_difficulty(state_principal) == "Senior"

    # Low score should demote from Senior to Mid
    state_senior = InterviewState(
        interview_id=uuid4(),
        current_difficulty="Senior",
        skills_to_test=["Python"],
        skills_tested=[],
        recent_performance=[4.5],
    )
    assert planner._compute_next_difficulty(state_senior) == "Mid"

    # Low score should demote from Mid to Junior
    state_mid = InterviewState(
        interview_id=uuid4(),
        current_difficulty="Mid",
        skills_to_test=["Python"],
        skills_tested=[],
        recent_performance=[2.0],
    )
    assert planner._compute_next_difficulty(state_mid) == "Junior"

    # Junior stays Junior
    state_junior = InterviewState(
        interview_id=uuid4(),
        current_difficulty="Junior",
        skills_to_test=["Python"],
        skills_tested=[],
        recent_performance=[1.0],
    )
    assert planner._compute_next_difficulty(state_junior) == "Junior"


def test_compute_next_difficulty_unchanged():
    planner = InterviewPlanner(session=MagicMock())

    # Average score between 5.0 and 7.9 keeps current difficulty
    state_mid = InterviewState(
        interview_id=uuid4(),
        current_difficulty="Mid",
        skills_to_test=["Python"],
        skills_tested=[],
        recent_performance=[6.5, 7.0],
    )
    assert planner._compute_next_difficulty(state_mid) == "Mid"
