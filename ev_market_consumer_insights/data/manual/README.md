# Tables typed in or built by hand

Some sources only exist as pictures or web pages, so I typed them in. Each one was checked
against itself before use, and the code repeats the checks every time it runs.

| File | Where it came from | How I checked it |
|---|---|---|
| `alliance_2025Q1_registrations_transcribed.csv` | Alliance for Automotive Innovation, *Get Connected* report for the first quarter of 2025, page 10. The state table is a picture, so I typed it in. | The plug-in hybrid, battery-electric and hydrogen shares add up to the electric total in every row. Each state's number also matches the 2026 report's number minus the year-over-year change it prints, within 0.01 points, for all 50 states, DC and the national row. |
| `alliance_2025Q1_vio_charging_transcribed.csv` | The same report, page 15 (charging ports and electric cars on the road). | Each state's charger types add up to its total, every column adds up exactly to the national row, and the state shares of the nation's electric cars add up to 100. |
| `fhwa_mv1_2023_transcribed.csv` | Federal Highway Administration, *Highway Statistics 2023*, state vehicle registration table (https://www.fhwa.dot.gov/policyinformation/statistics/2023/mv1.cfm), read from the web page. | Every state's vehicle types add up to its total, and every column adds up to the national total, within one vehicle. New York and three column totals are off by exactly one vehicle out of millions, either rounding in the original table or a one-digit slip. It doesn't change any share. |
| `policy_state.csv` | Two lists of special registration fees for electric cars, plus the Alliance report's list of states that adopted California's zero-emission car rule. | See `policy_sources.md`. |
| `event_calendar.csv` | One or two news or legal sources for each event. | The code checks that every event has a real date and a web link. |

Please don't edit these files without running the whole pipeline again.
