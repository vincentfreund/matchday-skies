# ✈️⚽ Matchday Skies

**How Bayern home games shape air traffic and delays at Munich Airport, and how to tell match delays apart from everything else.**

> 🔗 **[Try the live demo](https://vincentfreund.github.io/matchday-skies/)**  ·  Built for the London Aerospace Hackathon, 12–13 December 2026

<!-- Replace with a GIF of the demo: record ~10 s of the map playing, save as docs/demo.gif -->
<!-- ![Matchday Skies demo](docs/demo.gif) -->

> ⚠️ **Prototype status:** all data in this repo is **simulated**. The pipeline is ready to take real data; we'll plug that in at the hackathon.

---

## The problem

Up to 75,000 fans come to the Allianz Arena for a home game. On Champions League nights, away fans arrive on charter flights, business jets fill the aprons and departures pile up right before the night curfew. Airlines and the airport plan for the busy days they know about, but match effects are hard to separate from **other causes** such as fog, thunderstorms, Oktoberfest or a big trade fair.

## What it does

| Feature | What you can do |
|---|---|
| 🗺️ **Live traffic map** | Compare a normal Saturday, a Bundesliga game and a Champions League night. Scrub through the day and watch arrivals, departures, business jets and the police helicopter over the stadium. |
| 📈 **Hourly profile** | See movements per hour against a normal day, with the match window marked. |
| 🔮 **Delay predictor** | Describe a matchday (competition, kickoff, away fans, weather, events) and get an estimated arrival delay. |
| 🧭 **"Other causes" check** | Splits the delay into *normal baseline*, *match effect* and *other causes*, and tells you whether the football is really to blame. |

## How it works

```
 flight data ─┐
 (OpenSky)    │
 weather ─────┼──► model/build_demo_data.py ──► data/demo_data.js ──► index.html
 (DWD)        │     • hourly traffic profiles      (JSON)              (static page,
 match + event┘     • delay regression                                  GitHub Pages)
 calendar
```

- **`model/build_demo_data.py`**: builds the traffic profiles and fits the delay model (linear regression, `numpy`). It currently uses `simulate_days()` and `hourly_profiles()`. **Replace those two functions with real data loaders** and everything else keeps working.
- **`data/demo_data.js`**: generated output, loaded by the page. Don't edit by hand.
- **`index.html`**: the whole front end in one file with no build step and no dependencies.

## Run it locally

```bash
git clone https://github.com/vincentfreund/matchday-skies.git
cd matchday-skies
pip install -r requirements.txt
python model/build_demo_data.py     # regenerates data/demo_data.js
open index.html                     # or just double-click it
```

## Publish the demo (GitHub Pages)

1. Push this repo to GitHub.
2. Go to **Settings → Pages → Build and deployment**.
3. Set **Source: Deploy from a branch**, **Branch: `main`**, **Folder: `/ (root)`**, then **Save**.
4. After about a minute the demo is live at `https://vincentfreund.github.io/matchday-skies/`. Put that link at the top of this README.

## Roadmap (hackathon weekend)

- [ ] Real arrivals and departures for MUC from the OpenSky Network
- [ ] Real Bayern fixture list + DWD weather + Oktoberfest and Messe calendars
- [ ] Train the delay model on real days, report out-of-sample error
- [ ] **Flight disruption agent:** warns airlines and passengers before a high-risk matchday window
- [ ] Extend to other stadium cities (London: Wembley ↔ Heathrow / Luton / City)

## Data sources (planned)

| Source | Use |
|---|---|
| [OpenSky Network](https://opensky-network.org/) | ADS-B flight tracks (historical access needs approval) |
| [DWD Open Data](https://opendata.dwd.de/) | Weather observations for Munich |
| Bundesliga / UEFA fixture lists | Match dates and kickoff times |
| Oktoberfest, Messe München, school-holiday calendars | "Other causes" features |

## Team

- **Vincent R. Freund**: idea, business case, analysis
- **[Teammate name]**: data engineering, model, aerospace background

## License

MIT. See [LICENSE](LICENSE).
