# Electric cars across 50 states and DC, 2025 to mid-2026

*By Sam Hakim · Project f(Y002) on [hakimx.com](https://hakimx.com/five-state-auto.html)*

How did electric car buying change across every state when the federal tax credit ended? Which
states buy more electric cars, and why? Do people who search for electric cars actually buy them?
And do electric car owners complain about different things than owners of similar gas cars?

This repository has the data preparation, the analysis, and the write-up. Everything on the
project page comes from files this code produces. The page itself doesn't calculate anything.

## What I found

- **The end of the federal tax credit drove everything.** Electric cars were 9.5% of new
  registrations in spring 2025, jumped to 12.6% as buyers rushed to beat the September 30, 2025
  deadline, then fell to 6.5%. By spring 2026 the share was 7.9%. In the typical state, the
  electric share was cut about in half in a single quarter.
- **Michigan fell the hardest.** Its electric share went from 12.5% to 3.8% in one quarter, the
  biggest drop of any state. Before the credit ended, Michigan bought far more electric cars than
  its income and truck-heavy market would predict. Afterward, most of that extra was gone.
- **Income and trucks explain most of the differences between states.** Richer states buy more
  electric cars, and truck-heavy states buy fewer. Apartments, renters, special registration fees
  and gas prices didn't show a clear link once income was accounted for.
- **Interest and buying go together.** States rank almost the same on Google searches for electric
  cars as they do on actual registrations. Only Maine and Oklahoma show a lasting gap.
- **Complaints depend on the model.** The Chevrolet Equinox EV drew a smaller share of electrical
  complaints than the gas Equinox. The Hyundai Ioniq 5 drew far more than the gas Tucson, which
  lines up with a known recall on one of its charging parts.

The full story, including how I chose the five electric models for the search data, what each
measure means, and what this means for car companies and researchers, is in
[`docs/methodology.md`](docs/methodology.md).

## How it started

Three short, anonymous conversations in Metro Detroit gave me the ideas to test: repair worries,
charging costs, no place to charge at an apartment, cold winters, state policy, too few public
chargers, and truck-heavy markets. The cleaned notes are in [`docs/interviews.md`](docs/interviews.md).

## What's in here

```
stage_1_data/       prepares each data source (every script starts with a plain description)
stage_2_analysis/   the analysis, run in number order
data/manual/        tables I typed in or built by hand, with their sources and checks
data/clean/         the prepared tables
outputs/tables/     results you can open in Excel
outputs/site_data/  the numbers the website reads
tests/              checks that run on small made-up data
docs/               the methodology and the interview notes
run_all.py          runs everything in order and stops at the first problem
```

## Run it yourself

You'll need Python 3.10 or newer and the free `pdftotext` tool (part of Poppler).

1. Install the packages: `pip install -r requirements.txt`
2. Put the source files in `data/raw/`:

| Folder | File | Where to get it |
|---|---|---|
| `data/raw/alliance/` | `Get_Connected_EV_Quarterly_Report_2025_Q1.pdf` through `..._2026_Q2.pdf` (six files) | Alliance for Automotive Innovation, *Get Connected* quarterly reports |
| `data/raw/gas/` | `MasterGas.csv` | `git clone --depth 1 https://github.com/jgreathouse9/AAAGas`, then copy `Prices/MasterGas.csv` |
| `data/raw/census/` | `NST-EST2025-ALLDATA.csv` | Census Bureau state population estimates, 2025 release |
| `data/raw/census/` | `ACSDT1Y2024.B19013.csv`, `ACSDP1Y2024.DP04.csv` | data.census.gov, tables B19013 (income) and DP04 (housing), 2024 one-year estimates. Set the geography to "All States" before downloading the CSV. |
| `data/raw/trends/` | `trends_<group>_<period>_states.csv`, `trends_<group>_national_monthly.csv`, and `related_queries/` | Google Trends (settings in the methodology) |
| `data/raw/nhtsa/` | `COMPLAINTS_RECEIVED_2025-2026.zip` | National Highway Traffic Safety Administration complaint downloads |

3. Run `python run_all.py`
4. Run the checks: `python -m pytest tests/`

I don't redistribute the Alliance reports or the gas price file. Please download your own copies
and follow their terms.

## Privacy

The complaint file contains owners' cities, vehicle identification numbers and dealer details. The code never
reads those columns. Complaint text is used only to flag certain words in memory. Nothing personal
is saved or published, only totals and percentages. The interviews are anonymous.

## What this is not

It describes patterns. It doesn't prove causes, forecast sales, or describe any individual buyer.

## License

Code and documentation: MIT License (see `LICENSE`). The source data keeps its own terms.
