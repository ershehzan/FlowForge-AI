"""
Unit tests for JsonParser and operation-aware job shop scheduling.
"""
import json
import pytest
from agents.factory.json_parser import JsonParser
from agents.scheduler import Scheduler
from agents.resilience.metrics import calculate_all_metrics
from agents.resilience.score import calculate_resilience_score


SAMPLE_JSON = {
    "machines": [
        {"machine_id": 0, "unavailable_periods": []},
        {"machine_id": 1, "unavailable_periods": [[7, 12]]},
        {"machine_id": 2, "unavailable_periods": []}
    ],
    "jobs": [
        {
            "job_id": 0,
            "due_date": 15,
            "priority": 2,
            "operations": [
                {"machine_id": 0, "processing_time": 3},
                {"machine_id": 1, "processing_time": 2},
                {"machine_id": 2, "processing_time": 2}
            ]
        },
        {
            "job_id": 1,
            "due_date": 20,
            "priority": 3,
            "operations": [
                {"machine_id": 0, "processing_time": 2},
                {"machine_id": 2, "processing_time": 1},
                {"machine_id": 1, "processing_time": 4}
            ]
        },
        {
            "job_id": 2,
            "due_date": 25,
            "priority": 2,
            "operations": [
                {"machine_id": 1, "processing_time": 4},
                {"machine_id": 0, "processing_time": 3}
            ]
        },
        {
            "job_id": 3,
            "due_date": 30,
            "priority": 1,
            "operations": [
                {"machine_id": 2, "processing_time": 8},
                {"machine_id": 0, "processing_time": 5}
            ]
        },
        {
            "job_id": 4,
            "due_date": 10,
            "priority": 2,
            "operations": [
                {"machine_id": 1, "processing_time": 2},
                {"machine_id": 2, "processing_time": 2}
            ]
        }
    ]
}


def test_json_parser_basic():
    parser = JsonParser()
    raw = json.dumps(SAMPLE_JSON).encode("utf-8")
    result = parser.parse(raw, filename="test_factory.json")

    assert result["success"] is True
    assert len(result["machines"]) == 3
    assert "M0" in result["machines"]
    assert "M1" in result["machines"]
    assert "M2" in result["machines"]
    assert result["machines"]["M1"]["unavailable_periods"] == [[7, 12]]
    assert len(result["jobs"]) == 5
    assert len(result["disruptions"]) == 1
    assert result["disruptions"][0]["machine_id"] == "M1"
    assert result["disruptions"][0]["time_window"] == [7, 12]


def test_operation_aware_scheduler_and_unavailable_period_avoidance():
    parser = JsonParser()
    parsed = parser.parse(json.dumps(SAMPLE_JSON), filename="test.json")

    machines = list(parsed["machines"].keys())
    scheduler = Scheduler(machines)
    unavail_map = {m_id: m.get("unavailable_periods", []) for m_id, m in parsed["machines"].items()}

    schedule = scheduler.ga_schedule(parsed["jobs"], machine_unavail=unavail_map)
    assert len(schedule) == 12

    # Check that M1 never processes an operation during [7, 12]
    for assignment in schedule:
        if assignment["machine"] == "M1":
            start = assignment["start"]
            end = start + assignment["duration"]
            assert not (start < 12 and end > 7), f"Operation {assignment['job_id']} overlapped downtime on M1: [{start}, {end}]"


def test_json_resilience_and_metrics():
    parser = JsonParser()
    parsed = parser.parse(json.dumps(SAMPLE_JSON))
    machines = list(parsed["machines"].keys())
    scheduler = Scheduler(machines)
    unavail_map = {m_id: m.get("unavailable_periods", []) for m_id, m in parsed["machines"].items()}
    schedule = scheduler.ga_schedule(parsed["jobs"], machine_unavail=unavail_map)
    energy_map = {m: 8.0 for m in machines}

    metrics = calculate_all_metrics(schedule, machines, energy_map)
    assert metrics["makespan"] > 0
    assert metrics["total_jobs"] == 12

    score = calculate_resilience_score(schedule, machines, energy_map, len(machines), len(machines))
    assert 0 <= score["score"] <= 100
