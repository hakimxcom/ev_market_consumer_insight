# Where the policy table comes from

| Column | Source | Notes |
|---|---|---|
| `has_ev_fee_in_window` | American Road and Transportation Builders Association, *State Electric Vehicle Fees, September 2025* (https://transportationinvestment.org/wp-content/uploads/2025/09/State_Electric_Vehicle_Fees_Sept_2025.pdf), checked against the National Conference of State Legislatures list below | 1 means the state charged a special yearly registration fee for electric cars in September 2025. That's 41 states. Both lists leave out the same places: Alaska, Arizona, Connecticut, DC, Florida, Maine, Massachusetts, Nevada and New York. New Mexico only appears on the second list, with a fee that starts in 2027, so it counts as 0 here. |
| `ev_fee_bev_artba_sep2025` | The September 2025 list | Fee for a regular passenger car (the lowest tier when fees depend on weight). Blank for Virginia, whose fee is defined as 85% of what a gas car pays in gas tax. |
| `ev_fee_bev_ncsl_jul2026` | National Conference of State Legislatures, *Special Registration Fees for Electric and Hybrid Vehicles*, updated July 7, 2026 (https://www.ncsl.org/transportation/special-registration-fees-for-electric-and-hybrid-vehicles) | Used only as a cross-check. Many fees rise with inflation or changed later, so several amounts differ from the 2025 list. The `note` column flags each one. |
| `acc2_adopted_2025q1` | Alliance for Automotive Innovation, first quarter 2025 report, footnote marking states that adopted California's zero-emission car rule (known as Advanced Clean Cars II) | 12 states. Congress voted to overturn the federal approval for that rule, and the President signed it on June 12, 2025 (see `event_calendar.csv`). So this column marks a state's policy climate, not a rule that was enforced the whole time. |

The two fee lists were read from their web pages with an automated reader and compared with each
other. Where they disagree, the `note` column says so. The analysis uses only the yes or no column,
because both lists agree on it for every state.

State rebates and tax credits for buyers are not included. They changed state by state and month by
month in 2025 and 2026, and I didn't find one reliable, dated source covering all of them.
