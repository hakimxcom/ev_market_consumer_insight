# How I did this study

*Sam Hakim, October 2026*

This is the long version. The short version is in the [README](../README.md). I tried to write
it so that someone who has never taken a statistics class can follow the reasoning, and someone
who has can check it.

## Executive summary

I wanted to know how electric car buying changed across all 50 states and Washington, DC between
January 2025 and June 2026, and why some states buy far more electric cars than others. That
window matters because the federal tax credit for electric cars ended on September 30, 2025.

What I found, in plain terms:

1. **The tax credit's end was the story.** Electric vehicles were 9.5% of new car registrations
   in the spring of 2025. Buyers rushed in before the deadline and pushed that to 12.6% in the
   summer quarter. Then it fell to 6.5% in the fall. By spring 2026 it had climbed back to 7.9%.
   In the typical state, the electric share was cut roughly in half from one quarter to the next.
2. **Michigan fell harder than any other state.** Its electric share dropped from 12.5% to 3.8%
   in one quarter, a loss of about 70%. Before the credit ended, Michigan bought more electric
   cars than its income and its love of trucks would predict. After the credit ended, most of
   that extra disappeared.
3. **Income and trucks explain most of the gap between states.** Richer states buy more electric
   cars. States where trucks and SUVs make up more of the vehicles on the road buy fewer. Things
   I expected to matter, like how many people rent or live in apartments, and whether a state
   charges electric car owners a special registration fee, did not show a clear link once income
   was taken into account.
4. **Interest and buying mostly move together.** States that search Google for electric cars the
   most are, almost always, the states that buy them the most. Only Maine and Oklahoma showed a
   lasting gap where people searched a lot more than they bought.
5. **Complaints depend on the car, not on being electric.** I compared owner complaints for three
   electric cars against the gas car from the same company that is closest in size. Chevrolet's
   Equinox EV drew a smaller share of electrical complaints than the gas Equinox. Hyundai's
   Ioniq 5 drew many more than the gas Tucson, and that lines up with a known safety recall on
   one of its charging parts.

## Why I did it

I started with three short conversations with people in Metro Detroit (more on that below). They
gave me reasons people hesitate on electric cars: repair costs, charging costs, nowhere to plug in
at an apartment, cold winters, a state's politics, and not enough chargers on the road. I wanted
to see which of those reasons show up in public data, and which don't.

I also wanted the work to be useful to two kinds of readers. A car company wants to know where
demand is, what moves it, and what owners complain about. A researcher wants to know whether the
evidence holds up and how to repeat it.

## The questions

1. How did the electric share of new car registrations move in every state from early 2025 to
   mid-2026, including the end of the federal tax credit?
2. Which state traits go along with higher or lower electric car buying?
3. Where does interest in electric cars (people searching for them) run ahead of or behind actual
   buying, and which models and buying paths (new, used, lease) does that interest point to?
4. What do electric car owners complain about, compared with owners of similar gas cars?

## What kind of study this is

It starts with a few conversations to come up with ideas, then uses public data to test them.
It describes patterns. It does **not** prove that one thing caused another. When I say two things
"go together", that is all I mean.

## The interviews

I talked with three people in Metro Detroit in October 2026. Each conversation was short, informal
and anonymous. Everyone agreed out loud to take part and could skip any question.

- a small-business owner
- an electric car owner who lives in a condominium
- someone who had just bought a gas pickup truck and did not choose an electric one

This is a small group I could reach easily, so it says nothing about how common any opinion is.
I used it only to decide what to look for. The cleaned notes are in
[`interviews.md`](interviews.md).

What they raised, and what I turned it into:

| What I heard | What I tested | What I measured |
|---|---|---|
| Electrical repairs are complicated and expensive, few local mechanics can do them, so owners end up at dealers | Electric owners complain more about electrical problems and dealers than owners of similar gas cars | Federal safety complaint records |
| Public charging costs much more than charging at home (the owners guessed $30–40 versus $10–15) | Higher electricity prices go with less electric car buying | Not tested in this version: the electricity price file is still to be added |
| You can't install a charger in a condo or apartment | States with more renters and apartments buy fewer electric cars | Census housing data |
| Cold weather drains the battery | Colder states buy fewer electric cars | Not tested (reasons under "Limits") |
| The oil industry still has a lot of influence | States with less electric-friendly policies buy fewer electric cars | Special registration fees and a state's adoption of California's zero-emission car rule. I measured policies, not anyone's motives. |
| Range is short and chargers aren't everywhere yet | States with fewer public chargers buy fewer electric cars | Public charging ports per 10,000 residents |
| (The truck buyer) | States where trucks are more common buy fewer electric cars | Truck and SUV share of registered vehicles. This one was my idea, not his. |

One thing the first two people said stuck with me. They worry about electrical problems "in any
car, gas or electric." So I tested repair worries as a *difference* between electric and gas cars,
not as a fear that only applies to electric cars.

## Where the data comes from

All of it is public. Nothing was made up or filled in. When a number was missing, I left it
missing.

| Source | What I used | How detailed |
|---|---|---|
| Alliance for Automotive Innovation, *Get Connected* quarterly reports, first quarter 2025 to second quarter 2026 | Electric share of new car registrations (battery-electric, plug-in hybrid, hydrogen); public charging ports; electric cars on the road per 10,000 residents | Every state, every quarter |
| Daily state gas prices collected from AAA by a public GitHub project (jgreathouse9/AAAGas) | Average price of regular gas | Every state, every day, averaged by quarter |
| U.S. Census Bureau | Population (2024 and 2025 estimates); median household income; share of households that rent; share of homes in buildings with five or more units (2024 survey) | Every state |
| Federal Highway Administration, *Highway Statistics 2023*, table of state vehicle registrations | Cars versus trucks registered in each state | Every state |
| American Road and Transportation Builders Association (September 2025) and National Conference of State Legislatures (July 2026) | Which states charge electric car owners a special yearly registration fee | Every state |
| Alliance for Automotive Innovation, first quarter 2025 report | Which 12 states had adopted California's zero-emission car rule | Every state |
| National Highway Traffic Safety Administration complaint database | Owner complaints filed January 2025 to June 2026: car model, year, the part involved, state | Each complaint |
| Google Trends | How much people in each state searched for electric cars, specific models, leasing and used cars, compared with related searches | Every state, by quarter and for the whole period; national by month |

A few notes on these:

- **The first-quarter 2025 tables were pictures, not text,** so I typed them in by hand. I then
  checked every number two ways: the parts had to add up to the totals, and each state had to
  match what the next year's report says the change was. All 51 rows matched.
- **The Alliance reports give hybrid shares only for the whole country,** never by state. So
  regular hybrids are not part of the state analysis.
- **The registration numbers count new cars only.** Used car purchases don't show up, which is
  why I added a separate check on used cars (see below).
- **The complaint file includes names, addresses, vehicle identification numbers and dealer details.** My code
  never reads those columns. I read the complaint text only to flag certain words, and I publish
  only totals and percentages.
- **The truck numbers count SUVs and vans as trucks,** and states don't all sort vehicles the same
  way. So this measures "truck and SUV culture", not pickups alone.
- **The two fee lists agree on which states charge a fee** but not always on the dollar amount,
  because many fees rise with inflation. I used the simple yes or no.

## How I picked the five electric models for the search data

Google lets you compare only five search terms at a time, so I had to choose. I picked the
Tesla Model Y, Tesla Model 3, Chevrolet Equinox EV, Hyundai Ioniq 5 and Ford Mustang Mach-E.
Here is why.

1. **They were the top sellers.** These five were the best-selling electric models in Cox
   Automotive and Kelley Blue Book sales reports for January to September 2025 and for the first
   half of 2026, and they stayed in the top five across both periods. That means they cover a
   large share of what people actually buy.
2. **People search for models, not for general terms.** Before choosing, I looked at the searches
   Google lists as related to "electric vehicle." People type a model name, often with "used",
   "for sale" or a year (searches for "used model y" grew about 40%). General searches like
   "electric car price" or "electric car lease" were too rare to measure state by state, so I
   dropped them.
3. **They give a fair spread of companies.** Two are Tesla, two are Detroit companies (General
   Motors and Ford), and one is Korean (Hyundai). That lets me ask whether Michigan leans toward
   Detroit brands.
4. **Each one has a gas twin.** The Equinox EV can be compared with the gas Equinox, the Ioniq 5
   with the Tucson, and the Mach-E with the Escape. Those pairs are what made the complaint
   comparison possible.

I added "Used car" as the sixth term in that comparison so the model searches could be read
against everyday car shopping.

Two warnings came out of this. First, Google's groupings for the Equinox EV and the Mach-E also
pick up searches for the gas Equinox and the gas Mustang (plain "mustang" is the top related
search for the Mach-E). So I call those numbers "model-family interest." Second, the Equinox EV
numbers are very small (1 to 6 across states), so small differences mean nothing.

For leasing I compared Toyota, Chevy, Ford, Hyundai, Tesla and Honda, because people search
by brand: "toyota lease" came up about twice as often as "electric car lease." For used cars I compared
"Used car", "used tesla" and "used electric cars." The last one was zero everywhere, so I dropped it.

## What I measured

**The main thing I was trying to explain (the outcome)**

- **Electric share of new registrations:** of all new cars and light trucks registered in a state
  in a quarter, the percent that were battery-electric, plug-in hybrid or hydrogen. I report
  changes in *percentage points* (from 5% to 7% is +2 points).

**Other outcomes**

- **Growth in electric cars on the road:** the change in electric cars per 10,000 residents from
  early 2025 to mid-2026. I used it for the used car check.
- **Complaint topics:** the percent of complaints about each car that involve the electrical
  system, the engine or motor and drivetrain, driver-assist features, brakes, and so on.

**The things I compared it against (the explanations)**

| Measure | How it's calculated | Idea it tests |
|---|---|---|
| Median household income | Census figure for 2024 | Can people afford electric cars? |
| Apartment share | Percent of homes in buildings with 5 or more units | Can people charge at home? |
| Renter share | Percent of households that rent | Can people install a charger? |
| Truck and SUV share | Trucks divided by cars plus trucks | Truck-heavy markets |
| Special electric car fee | Yes or no | Policy climate |
| California's zero-emission rule | Yes or no, as of early 2025 | Policy climate |
| Public chargers per 10,000 people | Charging ports divided by population, times 10,000 | Charging access |
| Average gas price | Average of the daily prices recorded in the quarter | Fuel cost pressure |
| Search interest | Searches for "Electric vehicle" divided by searches for "Electric vehicle" plus "Car dealership" | Interest in electric cars |

On the search measure: in a Google comparison, each state's numbers add up to 100, so they show
how searching is split between the terms. I divided electric car searches by electric car plus
car dealership searches. Think of it as "of the people shopping for a car, how many are looking at
electric ones." I did it this way because the "Hybrid vehicle" search term collapsed in every
state at once in the second half of 2025 and then came back. That looks like a change on Google's
side, not a real change in people's interest, and dividing by dealership searches keeps that glitch
out of the electric measure. I also checked a second version, and the two ranked states almost
identically.

## How I analyzed it

I kept every step simple enough to explain.

1. **Describing what happened.** National and state trends, quarter by quarter, with the dates of
   key events (the tax credit law, the deadline, new cheaper models).
2. **Comparing states.** I lined up all 51 states and asked which traits go along with a higher
   average electric share, holding the others steady. I used only four or five traits at a time,
   because with 51 states you can't ask much more without fooling yourself. I put all traits on
   the same scale, so each result reads as "how many points of electric share go with a typical
   difference in this trait." I re-ran it without California and DC to make sure two places weren't
   driving the result.
3. **Following each state over time.** I asked whether a state's electric share rose in quarters
   when its gas prices (or its search interest) rose *more than the national average.* This setup
   cancels out everything that is fixed about a state and everything that hit the whole country at
   once. That's also why it can't measure the tax credit itself: the credit hit everyone at the
   same time.
4. **Grouping states into segments.** I looked for the main patterns underneath ten state traits,
   then grouped states with similar patterns. I checked the grouping with a second method; the two
   agreed only moderately, so states near the edges could reasonably fall into a neighboring group.
5. **Interest versus buying.** I ranked every state on search interest and on electric share and
   looked at the difference. I flagged a state only if the gap was at least 10 places under both
   search measures *and* over the whole period, so a one-quarter blip doesn't count.
6. **The used car check.** If a state's electric car count grows faster than its new sales would
   explain, something else is adding electric cars: used purchases, people moving in with their
   cars, or company fleets being re-registered. I flagged the states furthest above the line. This
   is a signal, not a count of used sales.
7. **Complaints.** For each pair (Equinox EV and Equinox, Ioniq 5 and Tucson, Mach-E and Escape),
   I compared the share of complaints about each part of the car, using the same model years on
   both sides. I tested each difference with a standard test for comparing two percentages and
   adjusted for running many tests at once. Complaints that mention words like "dealer" or
   "mechanic" are flagged by a word search; I'm checking those by hand on a random sample of 120
   before publishing any of them.

## Results

**The tax credit cliff.** National electric share by quarter: 9.63%, 9.46%, 12.60%, 6.52%, 6.26%,
7.88%. Between spring 2025 and spring 2026 it fell in 41 states and DC. The biggest drops were
Colorado (−9.9 points), DC (−5.7), Michigan (−5.2) and New Jersey (−4.9). From the summer to the
fall quarter of 2025, the typical state lost 49% of its electric share. Richer or poorer,
truck-heavy or not, almost every state fell by a similar proportion.

**Michigan.** 7.9%, 10.1%, 12.5%, then 3.8%, 3.8% and 4.9%. Its drop from summer to fall 2025
(−69.5%) was the largest in the country. Based on its income, housing, truck share and fees,
Michigan "should" have averaged about 4.6% before the credit ended; it averaged 10.2%. After the
credit ended it should have been about 2.9% and it was 4.2%. So Michigan's extra electric buying
mostly depended on the credit. In searches, Michigan leans toward Detroit brands more than any other
state: 63% of its searches across the five models were for the Equinox EV or Mach-E families,
against 36% in the typical state, and it had the lowest Tesla share. Its lease searches also lean
Detroit (Ford 41%, Chevy 27%, Toyota 14%).

**What goes with electric buying across states.** For a typical difference between states:

- higher income goes with about **+2.2 points** of electric share
- a higher truck and SUV share goes with about **−1.7 points**
- apartments, renters and special fees show no clear link once income is included
- California's zero-emission rule goes with about +1.2 points, right on the edge of being a real
  pattern
- more public chargers line up strongly with more electric buying (the simple correlation is
  0.69), but not once income is included. Chargers also tend to be built where electric cars
  already are, so the arrow can point both ways.

Together with housing and fees, these traits explain about 60% of the differences between states,
and almost all of that comes from income and trucks.

**Within each state over time,** quarters with bigger gas price jumps did not bring higher electric
share, and search interest moved with electric share only weakly. Searching one quarter did not
predict buying the next quarter. Six quarters dominated by one national shock is too short to see
much more.

**Interest versus buying.** State rankings on search interest and on electric share agreed closely
(a rank correlation of 0.80 to 0.91 in every quarter, where 1 would mean identical order). Maine and
Oklahoma were the only states with a lasting gap of more interest than buying. Michigan did not have
one. My first version of this project said it did, but that came from a search measure thrown off by
Michigan's low hybrid searches. Indiana looked unusual in spring 2026, but the Alliance report
explains that a jump in fleet registrations (from 128 to 3,080 cars) caused it. Nationally, search
interest dropped about 25% after the credit ended, then rose to its highest point in June 2026, well
before buying fully recovered.

**Used cars.** New electric sales explain about 81% of the growth in electric cars on the road. The
states where electric cars on the road grew most beyond that were Florida, Utah, Maryland, Delaware,
Nevada and Rhode Island.

**Segments.** Two main patterns run underneath the state traits. One I call *electric readiness*
(searches, electric share, gas prices, chargers, the zero-emission rule, income). The other is
*urban density* (renters and apartments). The states fall into three groups:

| Segment | States | Typical income | Truck and SUV share | Chargers per 10,000 | Average electric share |
|---|---|---|---|---|---|
| Urban cores | DC, New York | $97,000 | 56% | 13.3 | 11.8% |
| Electric-ready | 24 states, including California, Colorado, Washington, Florida and Michigan | $88,000 | 65% | 8.9 | 9.5% |
| Truck-first | 25 states, mostly in the South, the Plains and the Midwest | $73,000 | 69% | 3.9 | 3.9% |

Michigan's closest matches are Delaware, Pennsylvania, New Hampshire, New Mexico and Arizona.

**Complaints.** 1,293 complaints about the three electric models and 1,254 about their gas twins.

| Pair | Electrical system complaints, electric versus gas | Engine, motor and drivetrain complaints, electric versus gas |
|---|---|---|
| Equinox EV versus Equinox | 10% versus 28% | 4% versus 33% |
| Ioniq 5 versus Tucson | 79% versus 17% | 40% versus 28% |
| Mach-E versus Escape | 46% versus 23% | 21% versus 49% |

The pairs disagree with each other, so there is no single "electric car" answer. The Ioniq 5 result
lines up with federal safety recall 24V-868 (November 2024): a charging control part in 2022 to 2024
Ioniq 5s "may become damaged and stop charging the 12-volt battery," which can cause a loss of power
while driving.

## Conclusion

The end of the federal credit shaped this period more than anything about the states themselves.
It pulled buying forward into the summer of 2025 and then cut it roughly in half everywhere.
Beneath that shock, the lasting differences between states come down mostly to two things: how much
money households have, and how much the local market is built around trucks and SUVs. Several
popular explanations, including apartments, special fees and gas prices, did not hold up at the state
level.

Michigan is the most interesting case. It bought more electric cars than its profile suggests while
the credit lasted, then fell the furthest when it ended. Its interest leans heavily toward the
hometown brands. And the hometown brand's electric model, the Equinox EV, drew fewer electrical
complaints than its gas twin. The worry about electric repairs is real, but whether it's justified
depends on the specific car.

## What this means for the car industry

- **Plan state by state.** The same national message lands very differently in a state where
  electric cars are 1 in 5 new sales and one where they are 1 in 50.
- **Treat incentives as a cliff, not a slope.** When a credit ends on a known date, buyers move
  their purchase forward. Expect a spike before the deadline and a hole after it, and plan inventory
  and pricing around both.
- **Watch the hometown market.** Michigan's electric buying was unusually dependent on the credit.
  Without it, Detroit brands need another reason for local buyers to choose electric.
- **Use complaint data model by model.** A recall on one charging part can make one electric model
  look much worse than gas, while another electric model looks better. Publishing that difference,
  or fixing its cause, is a direct way to answer buyers' repair worries.
- **Search data is a cheap early warning.** Interest rebounded well before registrations did. A
  company can watch it every week for free.

## What this means for research

- **Search data can stand in for interest,** at least at the state level. It ranked states almost
  the same way as registrations, which supports using it where sales data is missing or late.
- **Be careful with search topics.** Google's groupings can mix an electric model with its gas
  namesake, and a single term can collapse for reasons that have nothing to do with people. Ratios
  between two terms protect against the second problem.
- **Matched gas twins are a simple, fair way to compare complaints.** Comparing all electric cars
  with all gas cars mixes brands, ages and price levels. Comparing within a company and size class
  removes most of that.
- **Policy shocks that hit everyone at once can't be measured by comparing quarters within states.**
  You need a group that wasn't affected, or a longer series.

## Limits

- **Survivorship.** Complaints come only from owners who filed one, not from shoppers who walked
  away from electric cars. Registrations count new cars only. People who never search for electric
  cars only appear through broader searches like leasing and used cars.
- **Other factors.** Gas prices move for their own reasons, and registrations also reflect state
  rebates, dealer stock, which models were available, company fleets and financing.
- **State averages don't describe people.** A state pattern says nothing about any single buyer.
- **Cold weather was not tested.** The cold quarters (fall 2025 and winter 2026) are the same
  quarters the credit ended, I only have one cycle of seasons, and warm states differ from cold ones
  in many other ways. I'd need more years to do it fairly.
- **Electricity prices were not tested yet.** That file still needs to be added.
- **State rebates are not included.** They changed state by state and month by month, and I didn't
  find one reliable dated source for all of them.
- **A few recalls drive some complaint counts.** Honda's Prologue, the Polestar 2 and the Fisker
  Ocean have unusually many complaints, which also affects state complaint rates.
- **Chinese electric cars** were essentially absent from the U.S. market in 2025 and 2026 (high
  tariffs and new rules on connected-car software), so they play no role here.
- **The interviews** are three people I could reach easily. They gave me ideas to test, nothing more.

## Rules I followed with the data

- Every row has one state and one quarter, and no duplicates.
- I never filled in a missing day, month or value.
- If two tables don't line up when joined, the code stops instead of quietly dropping rows.
- Parts must add up to totals (within rounding), or the code stops.
- Every missing value is listed in `data/clean/audit_missing.csv`.
- The tests in `tests/` use small made-up data, never the real files.
- Every script starts with a plain description of what it does, what it reads and what it writes.

## How to repeat this project

You need Python 3.10 or newer, and the free `pdftotext` tool (part of the Poppler package).

1. Download this repository.
2. Install the Python packages: `pip install -r requirements.txt`
3. Put the source files in `data/raw/`. The README lists each file, where to get it, and the
   folder it goes in. I don't redistribute the Alliance reports or the gas price file, so you
   need to download your own copies.
4. Run everything: `python run_all.py`. It runs the data preparation (`stage_1_data/`) and then
   the analysis (`stage_2_analysis/`) in order, and stops at the first problem.
5. Run the checks: `python -m pytest tests/`
6. Results land in `outputs/tables/` (spreadsheets you can open in Excel) and
   `outputs/site_data/` (the numbers my website reads).

If you pull fresh Google Trends data, expect small differences: Google samples searches, so the same
request can give slightly different numbers on different days. I pulled mine in October 2026 (the
related-search lists on October 25).
