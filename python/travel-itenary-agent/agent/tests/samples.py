"""Sample data shared by the builder tests and the golden files."""

from travel_agent.a2ui.surfaces.itinerary import Activity, Day, Itinerary, Stop


def thailand() -> Itinerary:
    A = Activity
    days = [
        Day(day=1, location="Bangkok", title="Arrival & riverside", activities=[
            A(slot="Afternoon", kind="travel", title="Arrive and check in", description="Settle in near the river.", est_cost_usd=0),
            A(slot="Evening", kind="food", title="Yaowarat street food", description="Chinatown's best night market bites.", est_cost_usd=20)]),
        Day(day=2, location="Bangkok", title="Temples & palaces", activities=[
            A(slot="Morning", kind="culture", title="Grand Palace & Wat Pho", description="Go early to beat the heat.", est_cost_usd=25),
            A(slot="Afternoon", kind="landmarks", title="Wat Arun by ferry", description="Cross the river for the porcelain spires.", est_cost_usd=5),
            A(slot="Evening", kind="nightlife", title="Rooftop bar", description="Sunset drinks over the skyline.", est_cost_usd=30)]),
        Day(day=3, location="Chiang Mai", title="Into the north", activities=[
            A(slot="Morning", kind="travel", title="Fly to Chiang Mai", description="A short domestic hop.", est_cost_usd=45),
            A(slot="Evening", kind="food", title="Night Bazaar", description="Khao soi and crafts.", est_cost_usd=15)]),
    ]
    return Itinerary(
        destination="Thailand",
        title="Thailand: Temples, Mountains & Islands",
        summary="Bangkok's energy, Chiang Mai's calm, then island time.",
        nights=7, travelers=2,
        stops=[Stop(city="Bangkok", nights=2), Stop(city="Chiang Mai", nights=2), Stop(city="Phuket", nights=3)],
        days=days,
        tips=["Dress modestly for temples.", "Grab/Bolt are the easiest way around cities."],
        est_budget_per_person_usd=1400,
    )
