import pytest

from travel_agent import tools


def test_flights_are_deterministic_and_sorted():
    a = tools.search_flights("London", "Lisbon", "2027-05-14", 2)
    b = tools.search_flights("London", "Lisbon", "2027-05-14", 2)
    assert a == b
    assert len(a) == 3
    assert [f.price_per_person for f in a] == sorted(f.price_per_person for f in a)
    assert a[0].destination == "LIS"


def test_hotels_compute_nights_and_totals():
    hotels = tools.search_hotels("Paris", "2027-05-14", "2027-05-18", 2)
    assert {h.nights for h in hotels} == {4}
    assert all(h.total_price == h.price_per_night * 4 for h in hotels)


def test_hotels_without_dates():
    hotels = tools.search_hotels("Lisbon", nights=2, travelers=2)
    assert {h.nights for h in hotels} == {2}
    assert all(h.check_in == "" and h.city == "Lisbon" for h in hotels)
    assert hotels == tools.search_hotels("Lisbon", nights=2, travelers=2)


def test_hotels_need_dates_or_nights():
    with pytest.raises(ValueError, match="nights"):
        tools.search_hotels("Lisbon")


def test_hotels_reject_bad_range():
    with pytest.raises(ValueError):
        tools.search_hotels("Paris", "2027-05-18", "2027-05-14")


def test_attractions_put_interests_first():
    items = tools.get_attractions("Tokyo", ["food"])
    n_food = sum(a.category == "food" for a in items)
    assert all(a.category == "food" for a in items[:n_food])


def test_unknown_city_gets_generic_data():
    items = tools.get_attractions("Reykjavik")
    assert any("Reykjavik" in a.name for a in items)


def test_weather_one_entry_per_day():
    days = tools.get_weather("Lisbon", "2027-05-14", "2027-05-18")
    assert [d.date for d in days] == [f"2027-05-{n}" for n in range(14, 19)]
    assert all(d.condition in {"sunny", "cloudy", "rain"} for d in days)


def test_bad_date_has_helpful_message():
    with pytest.raises(ValueError, match="ISO date"):
        tools.get_weather("Lisbon", "May 14", "2027-05-18")
