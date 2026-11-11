# CLPS Lunar Mission Browser — archived challenge text

**Challenge slug:** `clps-lunar-mission-browser`  
**Event:** 2026 NASA Space Apps Challenge  
**Difficulty:** Advanced, Intermediate  
**Subjects:** Human Exploration, Moon, Software, Space Exploration  
**Archived:** 2026-11-11 (full statement pasted by owner from Space Apps UI; Resources tab empty at time of copy).

## Summary

Missions to the Moon’s south pole face extreme lighting and communication constraints, and planning them takes careful coordination between science and engineering teams. Tools for determining Sun and Earth positions at candidate landing sites exist, but their complicated interfaces make it difficult to evaluate critical information with efficiency. **Your challenge is to** create an intuitive tool or application that lets mission planners, educators, and the public compare landing sites and dates quickly, visualizing Sun and Earth positions relative to the horizon to assess power generation potential and direct-to-Earth communication windows.

## Background

NASA’s Commercial Lunar Payload Services (CLPS) program and other lunar missions depend on careful selection of landing sites and dates that balance the needs of both science and engineering teams. One of the most significant challenges in this process is understanding the local lighting and communication environment at a potential landing site. The position of the Sun determines power availability for solar arrays and thermal conditions for equipment, while the position of Earth determines whether direct communication is possible without relay satellites.

This challenge is particularly acute at the Moon's south pole, where many future missions are planned due to the presence of water ice and other scientifically valuable resources. The south pole's geometry creates extreme variations in solar illumination and Earth visibility across different lunar days and seasons. Small changes in landing location or date can dramatically affect both power generation potential and communication windows, making rapid site evaluation critical.

In practice, mission development rarely proceeds on a fixed timeline. Hardware development challenges, launch delays, or other factors often force mission planners to reconsider their original landing date and location. When this happens, engineers need to quickly evaluate alternative sites in the same region, or alternative dates at the same site, to understand how these changes impact mission feasibility. A tool that enables rapid, intuitive comparison of multiple scenarios would accelerate this decision-making process and help teams identify viable alternatives when constraints shift.

Tools that provide this information — such as NASA's Quickmap, Moon Trek, and the JPL Horizons System — are built for detailed analysis and are often difficult for non-specialists to use effectively for rapid scenario comparison. Evaluating each site-date combination means navigating multiple interfaces and interpreting raw data. This leaves a gap between the technical data available and the accessible tools needed to support agile mission planning. An intuitive interface that translates complex ephemeris and topographic data into clear, comparable visualizations could help bridge that gap.

## Objectives

Your challenge is to create a tool or application that enables rapid evaluation of lunar landing site options. Your solution may include:

- **Interactive site selection and comparison:** curated sites (Apollo, CLPS, commercial, international) and/or custom coordinates; side-by-side or sequential comparison.
- **Date and time flexibility:** landing dates/times; explore changes across lunar days or seasons when schedule shifts.
- **Sun and Earth position visualization:** positions relative to the **horizon** on a chosen date; time to sunset/Earthset.
- **Power and communication assessment:** solar elevation, duration of sunlight, Earth visibility windows.
- **Multiple visualization approaches:** 2D maps, 3D surface, other representations.
- **Temporal dynamics:** animations/timelines over a lunar day or multiple days.
- **Accessibility across skill levels:** planners, educators, public.

Creative format allowed (web, mobile, game, etc.) as long as rapid site evaluation is clear and efficient.

## Potential Considerations

### Technical approach

- Ephemeris: JPL Horizons or pre-computed datasets.
- Topography: LRO LOLA for surface viz and horizon.
- No atmosphere → horizon from local terrain + spherical edge from site.
- Solar elevation prominent for power.

### User experience

- Rapid scenario comparison; clear time to sunset/Earthset; show why small location/date changes matter.

### Data and accuracy

- Topography affects horizon and visibility; Earth's libration; Moon's orbital variations; south pole slopes and crater shadows.

### Engagement and impact

- Coordinate science/engineering; respond to schedule changes; education.

**Resources (official tab):** empty when archived; statement says more resources may be added before hackathon. Supplement with Horizons, Moon Trek, Quickmap, LOLA/PGDA per engineering judgement until NASA publishes links.

## Official URL

https://www.spaceappschallenge.org/2026/challenges/clps-lunar-mission-browser/
