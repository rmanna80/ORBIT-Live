🛰️ ORBIT-Live
Building satellite mission control from scratch — one concept, one bug, and one breakthrough at a time.
ORBIT-Live is my ongoing project to build a satellite-tracking and mission-control platform using Python, real orbital data, and the mathematics behind spacecraft motion.

I'm not starting this project as an aerospace engineer or an expert in orbital mechanics. I have a programming background, but much of the physics, mathematics, and space-specific software is new to me. The point of this project is to learn it by building it.

I'm writing the core pieces step by step, working through the equations, figuring out why the code works, debugging my mistakes, and documenting what I learn along the way. I'm also sharing the process through live coding—not just polished results, but the parts where I get stuck and have to work something out.
Current status: Early development. The focus right now is the Python backend, two-body orbital mechanics, and reading satellite Two-Line Element (TLE) data. The larger mission-control features below are goals, not claims about what is already finished.

🚀 What I'm trying to build
My long-term goal is to create a platform where I can:
- Track real satellites using publicly available orbital data.
- Predict where satellites will be over time.
- Visualize their orbits and ground tracks on a map or mission-control dashboard.
- Estimate passes over ground stations, including visibility and communication windows.
- Explore orbital anomalies by comparing predictions against updated information.
- Build toward a mission-control experience with telemetry, alerts, and understandable visualizations.
The goal isn't just to make something that looks like mission control. I want to understand and implement the calculations and software underneath it.
🧠 Why I'm building it this way
I could start with a library that gives me satellite positions immediately, but I want to understand what happens before a position appears on a screen.

That means starting with questions like:
- Why does a satellite stay in orbit instead of falling straight down?
- How do gravity and velocity determine the shape of an orbit?
- What do Kepler's laws actually tell us?
- How can a TLE encode a satellite's orbital information in just two lines?
- What's the difference between a simplified Keplerian orbit and a more realistic SGP4 prediction?
- How does a program turn orbital data into a satellite position and a ground-station pass?
I am deliberately building the foundational calculations myself for learning. As the project grows, I'll use established standards and libraries where accuracy, reliability, or validation makes that the right engineering choice. The aim is understanding—not reinventing every piece of aerospace software for production use.


📐 The math behind the project
A few of the ideas I'm implementing and studying:
Kepler's third law
The time a satellite takes to complete an orbit depends on the size of that orbit:
T = 2π × √(a³ / μ)
- T: orbital period (seconds)
- a: semi-major axis (kilometers)
- μ: Earth's gravitational parameter (km³/s²)
Vis-viva equation
The orbital speed at a given distance from Earth's center is:
v = √[μ × (2/r − 1/a)]
- v: speed (km/s)
- r: current distance from Earth's center (km)
- a: semi-major axis (km)
TLE data
TLEs contain parameters such as inclination, eccentricity, and mean motion. I'm learning how to parse their fixed-width text fields and use their values correctly.

Accuracy note: These two-body equations are useful for learning and approximate calculations. Accurate propagation of operational TLEs requires an appropriate model such as SGP4; directly treating TLE mean elements as exact Keplerian elements is not equivalent to SGP4.
💻 Tech stack
Using now
- Python
- Standard-library math and date/time tools
- TLE data and orbital-mechanics equations
- Git / GitHub for version control
Possible additions as the project develops
- SGP4 for TLE-based orbit propagation
- An API for satellite and ground-station data
- A web dashboard and mapping/visualization tools
- Automated tests and comparison against reference predictions
I'm keeping these choices flexible while I learn what each part of the system needs.





📝 Learning in public
I'm documenting the process as I go—including the small wins and the mistakes.

Some days that means implementing an orbital equation. Other days it's figuring out a Python import error, understanding an unfamiliar mathematical concept, or learning why a TLE parser needs careful validation.

My personal rules for this project are simple:
1. Understand it before moving on. I want to be able to explain the math and the code, not just run it.
2. Build incrementally. Start with small functions, test them, and connect them into a larger system.
3. Show the real process. Debugging, rewriting, and asking questions are part of engineering.
4. Validate the results. A program running without errors doesn't automatically mean its physics is correct.
5. Keep improving. Revisit early decisions as I learn more about software engineering and aerospace systems.
If you're also learning programming, interested in space, or just curious about how satellite software works, you're welcome to follow along.
🔭 Where I want to take ORBIT-Live
Eventually, I'd like ORBIT-Live to be a hands-on platform for exploring real satellite behavior—from ingesting orbital information to calculating predictions, displaying tracks, planning ground-station contacts, and identifying unusual changes.

For now, I'm starting with the fundamentals and building upward. The journey of learning how to engineer it is as important to me as the finished platform.
Built from scratch, learned in public, and improved one commit at a time. 🛰️
