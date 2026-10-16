# 🚀 LinkedIn Post: Full Project Explainer

*A clear, engaging project breakdown that explains what you built, how it works, and why it matters.*

---

Recently, I did a little research on football transfer market prediction... and built a full project around it. ⚽📊

Here is what **The Football Transfer Market Prediction Engine** is and how it works:

### ❓ The Problem:
When an elite club sells a talismanic player or coach (e.g. Kane, Bellingham, Klopp), they face an existential crisis:
1. **The Tactical Void:** How much will team points (PPG), pressing, and goal creation drop?
2. **The Regulatory Trap:** UEFA's 70% Squad Cost Rule and Premier League PSR (£105M loss caps) mean clubs can no longer panic-buy big names without risking points deductions.

Traditional scouting only looks at headline fees and past goals. I wanted to build an end-to-end mathematical and computational solution.

---

### ⚙️ How the Project Works (4 Key Pillars):

1️⃣ **Machine Learning Shock Regressors (CatBoost + LightGBM)**
• Trained on **1.89 Million match appearances** and **176,000 manager records** (2004–2026).
• Predicts the exact post-departure points-per-game decline ($\Delta\text{PPG}$) with real-time inference latency under 15ms.
• Key Discovery: A player's minutes played (% reliance) is **2.5x more predictive** of sporting decline than their transfer fee!

2️⃣ **Role-Adaptive Vector Similarity & 2D Pitch Lineup**
• Maps players across 20 tactical metrics (progressive passes, carries, defensive recoveries, aerial duels).
• Features an interactive 2D pitch that visualizes the tactical void slot and automatically fits drop-in candidate replacements.

3️⃣ **UEFA FSR & PL PSR Amortization Calculator**
• Models European accounting standards (IAS 38 5-year straight-line amortization vs. immediate disposal gains).
• Discovers the **"Arbitrage Gold Zone"**: signing players who deliver **90%+ of the star's tactical output** at a **40% to 75% fee discount**, unlocking tens of millions in Year-1 regulatory breathing room.

4️⃣ **10,000-Run Monte Carlo Tournament Simulator**
• Runs 10,000 full-season tournament permutations to predict title odds, Champions League qualification probability, and revenue preservation (up to +€73.7M).

---

💻 **Try the Live Interactive Dashboard:**
👉 https://readuanulfaridfahim.github.io/football-transfers-ffp/

📁 **GitHub Repository & Full Architecture:**
👉 https://github.com/ReaduanulFaridFahim/football-transfers-ffp

*(P.S. Check out the 4 screenshots below to see the 2D Pitch Lineup, ML Simulator, and FFP Audit in action! 📸)*

I’d love to hear your thoughts! What's the biggest flaw in modern football recruitment? Let’s discuss in the comments! 👇🔥

#SportsAnalytics #FootballAnalytics #DataScience #MachineLearning #Python #AI #FinancialFairPlay #PremierLeague #FootballTransfers #FullStackDataScience #OpenSource
