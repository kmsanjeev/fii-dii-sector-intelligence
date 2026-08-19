# Engine extension architecture

`POST /api/muhurta/recommend` and `POST /api/muhurta/search` remain the sole
public Muhurta routes. The new activity IDs are resolved internally to the
predecessor T1 rule and machine-contract artifacts, checked against their
expected hashes, adapted to the existing declarative predicate shape, and
then evaluated by RX1.

The flow is:

`request -> canonical T1 artifact/hash guard -> P032 facts -> factor adapter ->
declarative IN predicate -> categorical result or abstention -> source trace /
caution / consultation`.

Window search selects only the Nakshatra transition dependency for the two T1
activities and uses the existing exact boundary segmentation and semantic
merge behavior. Business and Education continue to use their existing Tithi,
Karana and Nakshatra transition set.
