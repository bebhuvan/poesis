#!/usr/bin/env python3
"""Add metadata headers, speaker labels, section headers, and cold open labels to transcripts."""

import re
import os

# Episode metadata and section breakdowns
EPISODES = {
    "01_tom_sosnoff_transcript.txt": {
        "guest": "Tom Sosnoff",
        "host": "Bhuvan",
        "number": "01",
        "header": """================================================================================
IN THE MONEY — Episode 01
================================================================================

Guest:    Tom Sosnoff
Title:    Options, Contrarianism, and Building Financial Media
Recorded: Late October 2025

ABOUT THE GUEST
Tom Sosnoff is a legendary options trader and serial entrepreneur. He spent
nearly two decades as a floor trader in the OEX pit at the CBOE, where he was
one of the original traders of S&P 100 index options. In the late 1990s, he
founded Thinkorswim, an online options brokerage that reshaped retail trading
and was later acquired by TD Ameritrade for ~$700 million. He then built Tasty
Trade (now Tasty Live), the first digital financial streaming network, which
was acquired by IG Group for $1.1 billion in 2021. A pure contrarian at heart,
Tom's trading philosophy is grounded in statistics, the law of large numbers,
and probability-based decision-making. He is currently building Lost Dog, a
venture focused on worker equity and compensation transparency.

TOPICS COVERED
- From political science to the CBOE trading floor
- The early days of options trading and market making
- Active vs. passive investing philosophy
- Building Thinkorswim and the origins of retail options trading
- Creating Tasty Trade: financial media done differently
- Lost Dog and tackling worker inequity through data
- The value of university education in the age of AI
- Early misconceptions about markets and developing intuition
- Managing tail risk through position sizing
- Implied volatility as a core trading signal
- Views on trend following (from a contrarian's perspective)
- Diversification through non-correlated underlyings
- Scalping after 43 years: intuition without charts
- Zero-DTE options and their impact on US markets
- Indian market regulation and the Jane Street controversy
- AI as a trading tool vs. automated trading bots
- Financial content creation and competitive moats

================================================================================
TRANSCRIPT
================================================================================

""",
        "sections": {
            14: "\n--- INTRODUCTION ---\n",
            88: "\n--- FROM POLITICAL SCIENCE TO WALL STREET ---\n",
            156: "\n--- THE EARLY DAYS OF OPTIONS TRADING ---\n",
            229: "\n--- FLOOR TRADING: TAKING THE OTHER SIDE ---\n",
            269: "\n--- ACTIVE VS. PASSIVE INVESTING ---\n",
            379: "\n--- NAMING COMPANIES: THINKORSWIM, TASTY, LOST DOG ---\n",
            413: "\n--- FROM TRADING PIT TO BROKERAGE ---\n",
            477: "\n--- BUILDING TASTY TRADE: THE FIRST STREAMING NETWORK ---\n",
            599: "\n--- LOST DOG AND WORKER INEQUITY ---\n",
            668: "\n--- THE FUTURE OF FINANCIAL CONTENT ---\n",
            748: "\n--- UNIVERSITY EDUCATION IN THE AGE OF AI ---\n",
            817: "\n--- EARLY MISCONCEPTIONS ABOUT MARKETS ---\n",
            881: "\n--- MANAGING TAIL RISK AND POSITION SIZING ---\n",
            910: "\n--- SYSTEMATIC STRATEGIES AND IMPLIED VOLATILITY ---\n",
            973: "\n--- OPEN INTEREST AND OTHER INDICATORS ---\n",
            1013: "\n--- A CONTRARIAN'S VIEW ON TREND FOLLOWING ---\n",
            1058: "\n--- DIVERSIFICATION THROUGH STRATEGY AND PRODUCTS ---\n",
            1086: "\n--- 43 YEARS OF SCALPING ---\n",
            1147: "\n--- ANOMALIES AND CHANGING MARKETS ---\n",
            1184: "\n--- ADVICE FOR NEW TRADERS ---\n",
            1236: "\n--- AUTOMATION, APIs, AND TRADING BOTS ---\n",
            1352: "\n--- THE JANE STREET CONTROVERSY IN INDIA ---\n",
            1438: "\n--- ZERO-DTE OPTIONS AND WEEKLY EXPIRIES IN INDIA ---\n",
            1552: "\n--- CLOSING THOUGHTS ---\n",
        },
    },
    "02_tom_basso_transcript.txt": {
        "guest": "Tom Basso",
        "host": "Bhuvan",
        "number": "02",
        "header": """================================================================================
IN THE MONEY — Episode 02
================================================================================

Guest:    Tom Basso ("Mr. Serenity")
Title:    Systematic Trend Following, Self-Mastery, and Enjoying the Ride
Recorded: Late 2025

ABOUT THE GUEST
Tom Basso, known as "Mr. Serenity" — a name given by Jack Schwager in The New
Market Wizards — is one of the pioneers of systematic trend following. A
chemical engineer by training, he founded Trendstat Capital Management in the
early 1980s, one of the first systematic trend following firms in the US,
managing nearly $600 million at its peak. Tom is renowned for bringing an
engineer's precision to trading: designing systems that turn market data into
orders, emphasizing position sizing, volatility control, and diversification
long before these concepts became mainstream. His philosophy centers on
self-mastery over market prediction. After retiring from Trendstat in 2003, he
continues to trade independently, managing a fully automated futures portfolio
in under an hour a day. His motto: "Enjoy the ride."

TOPICS COVERED
- The meaning of "Mr. Serenity" and cultivating self-awareness
- From chemical engineering to markets: an unlikely path
- First mutual fund investments at age 12
- Hand-charting markets and the origins of point-and-figure bar
- The evolution from discretionary to systematic trading
- Commodities as diversification: why coffee doesn't care about the S&P
- Building trading systems from spreadsheets to automation
- Position sizing: risk, volatility, and margin as percent of equity
- Keltner bands, Bollinger bands, and volatility-adaptive indicators
- Filling the potholes: combining long-term and short-term strategies
- Law of large numbers and the psychology of single trades
- The Sharpe ratio is useless (and why comfort ratios matter more)
- COVID trading: 103% returns by just following the system
- Active vs. passive investing: the academic blind spot
- The Jane Street controversy in India
- AI in trading: useful for coding, dangerous for strategy
- Automation of execution: 100% automated, but human creativity matters
- Managing your own money vs. client money: potential stressors
- Advice for retail traders: build a business plan for your trading

================================================================================
TRANSCRIPT
================================================================================

""",
        "sections": {
            13: "\n--- INTRODUCTION ---\n",
            61: "\n--- THE MEANING OF MR. SERENITY ---\n",
            147: "\n--- SCHOOL DAYS AND THE PATH TO CHEMISTRY ---\n",
            186: "\n--- FROM MONSANTO TO MARKETS ---\n",
            225: "\n--- FROM CLARKSON TO MONSANTO ---\n",
            245: "\n--- FIRST ENCOUNTERS WITH THE MARKETS ---\n",
            313: "\n--- HAND-CHARTING AND THE BIRTH OF A SYSTEM ---\n",
            386: "\n--- BOOKS AND INFLUENCES: MARK DOUGLAS, VAN THARP ---\n",
            444: "\n--- THE EVOLUTION TOWARD TREND FOLLOWING ---\n",
            512: "\n--- COMMODITIES: THE DIVERSIFICATION ARGUMENT ---\n",
            613: "\n--- BUILDING CONVICTION IN SYSTEMATIC TRADING ---\n",
            705: "\n--- BACKTESTING IN THE PRE-COMPUTER ERA ---\n",
            822: "\n--- THE FIRST TRADING SYSTEM: PF BAR ---\n",
            888: "\n--- EDGE DECAY AND THE ACCELERATION OF MARKETS ---\n",
            1004: "\n--- ADAPTING PARAMETERS: VOLATILITY-ADAPTIVE INDICATORS ---\n",
            1086: "\n--- FILLING THE POTHOLES: MULTI-TIMEFRAME STRATEGIES ---\n",
            1188: "\n--- POSITION SIZING: RISK, VOLATILITY, AND MARGIN ---\n",
            1316: "\n--- LAW OF LARGE NUMBERS ---\n",
            1405: "\n--- BACKTESTING METRICS: MAR RATIO, COMFORT RATIO, AND SHARPE ---\n",
            1500: "\n--- DISCRETION VS. SYSTEM: THE COVID EXAMPLE ---\n",
            1583: "\n--- TAIL RISK AND THE DONCHIAN CHANNEL DURING COVID ---\n",
            1708: "\n--- EQUITY INDEXES AND THE TAX ADVANTAGE OF FUTURES ---\n",
            1766: "\n--- ACTIVE VS. PASSIVE: THE ACADEMIC BLIND SPOT ---\n",
            1889: "\n--- THE JANE STREET CONTROVERSY IN INDIA ---\n",
            1985: "\n--- AI AND AUTOMATION IN TRADING ---\n",
            2103: "\n--- SHOULD RETAIL TRADERS AUTOMATE? ---\n",
            2150: "\n--- MANAGING STRESS: POTENTIAL STRESSORS ---\n",
            2220: "\n--- KNOW THYSELF ---\n",
            2227: "\n--- WHAT KEEPS YOU GOING AFTER 50 YEARS ---\n",
            2273: "\n--- SOCIAL CONNECTIONS AND TRADING IDEAS ---\n",
            2291: "\n--- OPTIONS AS A PRODUCT ---\n",
            2317: "\n--- CLOSING THOUGHTS ---\n",
        },
    },
    "03_niels_kaastrup_transcript.txt": {
        "guest": "Niels Kaastrup-Larsen",
        "host": "Bhuvan",
        "number": "03",
        "header": """================================================================================
IN THE MONEY — Episode 03
================================================================================

Guest:    Niels Kaastrup-Larsen
Title:    CTAs, Trend Following Discipline, and the Art of Not Predicting
Recorded: Late 2025

ABOUT THE GUEST
Niels Kaastrup-Larsen is one of the most respected names in the systematic
trend following space, with over 30 years of experience across leading global
CTAs. He currently serves as the Managing Director for Europe at Dunn Capital
Management, one of the industry's oldest and most successful long-term trend
following programs (50+ years of track record). Niels is also the founder and
host of Top Traders Unplugged, a go-to podcast in the systematic investing
space known for candid, in-depth conversations with top managers and macro
thinkers. His work has made systematic trading and investing accessible to a
global audience.

TOPICS COVERED
- 2025 performance: a "tricky but not unusual" year for trend followers
- The April 2025 tariff shock and its impact on CTAs
- Historical drawdowns: context from the SocGen Trend Index
- Trend identification: breakouts vs. moving averages vs. time series momentum
- "Is trend following dead?" — the perennial question
- Market universe: from 50-100 to 200-300 markets (and back)
- Alternative markets: interest rate swaps, mainland China, orange juice
- Time frames: why medium-to-long-term works best
- Leverage in CTA portfolios: value at risk vs. notional
- Exits matter more than entries (and why)
- Why CTAs make more money on long-sided trades
- Drawdowns at market vs. portfolio level
- Evaluating strategies: returns, drawdowns, the serenity ratio
- Trading psychology: managing client expectations during drawdowns
- Bitcoin and new assets: how much data do you need?
- Market efficiency: the adaptive market hypothesis
- Crowding: amplifier on the way up, pain on the way out
- Machine learning vs. AI in trend following
- The AI bubble question
- BlackRock and Fidelity entering the trend following space

================================================================================
TRANSCRIPT
================================================================================

""",
        "sections": {
            15: "\n--- INTRODUCTION ---\n",
            39: "\n--- 2025: A TRICKY YEAR FOR TREND FOLLOWING ---\n",
            167: "\n--- THE APRIL 2025 TARIFF SHOCK ---\n",
            245: "\n--- HISTORICAL DRAWDOWNS IN CONTEXT ---\n",
            281: "\n--- TREND IDENTIFICATION: BREAKOUTS VS. MOVING AVERAGES ---\n",
            429: "\n--- MARKET UNIVERSE: HOW MANY ASSETS? ---\n",
            538: "\n--- ALTERNATIVE MARKETS ---\n",
            576: "\n--- TIME FRAMES AND TRADING SPEED ---\n",
            700: "\n--- LEVERAGE IN CTA PORTFOLIOS ---\n",
            892: "\n--- EXITS MATTER MORE THAN ENTRIES ---\n",
            1005: "\n--- POSITIVE DRIFT AND ONE-SIDED TRADING ---\n",
            1061: "\n--- ASYMMETRIC ENTRY AND EXIT RULES ---\n",
            1141: "\n--- DRAWDOWNS: MARKET LEVEL VS. PORTFOLIO LEVEL ---\n",
            1290: "\n--- EVALUATING TREND FOLLOWING STRATEGIES ---\n",
            1426: "\n--- TRADING PSYCHOLOGY AND MANAGING CLIENT EXPECTATIONS ---\n",
            1499: "\n--- NEW ASSETS WITH LIMITED HISTORY: BITCOIN ---\n",
            1564: "\n--- MARKET EFFICIENCY: THE ADAPTIVE MARKET HYPOTHESIS ---\n",
            1665: "\n--- CROWDING: AMPLIFIER OR RISK? ---\n",
            1690: "\n--- MACHINE LEARNING AND AI IN TREND FOLLOWING ---\n",
            1753: "\n--- THE AI BUBBLE QUESTION ---\n",
            1804: "\n--- CLOSING THOUGHTS ---\n",
        },
    },
    "04_robert_carver_transcript.txt": {
        "guest": "Robert Carver",
        "host": "Bhuvan",
        "number": "04",
        "header": """================================================================================
IN THE MONEY — Episode 04
================================================================================

Guest:    Robert Carver
Title:    Systematic Futures Trading, Robustness, and the Danger of Overfitting
Recorded: Late 2025

ABOUT THE GUEST
Robert Carver is an independent systematic futures trader, investor, writer,
research consultant, and visiting lecturer at Queen Mary University of London
where he teaches systematic trading at the master's level. He began his career
at Barclays trading exotic interest rate derivatives, but quickly realized that
discretionary, high-stress floor trading wasn't where good decision-making
thrived. In 2006, he joined AHL (Man Group), one of the world's largest
systematic hedge funds, where he built a systematic global macro strategy and
later managed the firm's entire fixed income portfolio — roughly 40% of the
risk of a $30 billion fund. Since 2013, he has traded independently, running a
fully automated futures portfolio across ~250 instruments based on systems he
personally designed. He is the author of several influential books on
systematic trading, including "Systematic Trading," "Leveraged Trading," and
"Advanced Futures Trading Strategies." His approach emphasizes simplicity,
robustness, and statistical rigor over optimization.

TOPICS COVERED
- From computer science dropout to accidental trader at Barclays
- Exotic interest rate derivatives: mentally challenging, not intellectually stimulating
- The transition from Barclays to AHL
- Managing your own money vs. a $30 billion fund
- Start simple: one market, one rule, then build
- 100 ways to identify trends — they all do the same thing
- The myth of finding the "right" trend system
- Why overfitting your entry/exit rules is dangerous
- Time frames: trends work between weeks and a year, then mean reversion
- Cost-awareness: S&P vs. milk futures
- 60% trend, 40% carry: portfolio composition
- Mean reversion strategies: long-term and short-term
- Max drawdown is a terrible performance metric
- Statistical significance and the evidence problem
- "Things were different after 2008" — why this framing is wrong
- Diversification: square root of N, correlation, and 250 instruments
- Overnight drift: real but too expensive to trade in isolation
- AI and LLMs in trading: an emphatic no for production code
- Tax arbitrage: stamp duty, spread bets, and India's STT
- Active vs. passive: costs, ETFization, and implications for trend following
- April 2025: correlation spikes and the limits of diversification

================================================================================
TRANSCRIPT
================================================================================

""",
        "sections": {
            17: "\n--- INTRODUCTION ---\n",
            73: "\n--- AN ACCIDENTAL PATH TO TRADING ---\n",
            138: "\n--- EXOTIC DERIVATIVES AT BARCLAYS ---\n",
            187: "\n--- DEVELOPING A BROADER MARKET UNDERSTANDING ---\n",
            272: "\n--- FROM BARCLAYS TO AHL ---\n",
            343: "\n--- MANAGING YOUR OWN MONEY VS. A FUND ---\n",
            474: "\n--- THE ECOSYSTEM: REPLACING OFFICE COLLEAGUES ---\n",
            534: "\n--- FIRST STRATEGY: START SIMPLE ---\n",
            644: "\n--- TREND IDENTIFICATION: 100 WAYS, ALL THE SAME ---\n",
            721: "\n--- TRENDS ON THE SHORT SIDE ---\n",
            797: "\n--- TRAILING STOPS AND THE DANGER OF OVERFITTING ---\n",
            844: "\n--- TIME FRAMES: WHERE TRENDS WORK ---\n",
            928: "\n--- THE FIRST SYSTEM: EWMA CROSSOVER ON S&P FUTURES ---\n",
            1049: "\n--- INTRADAY DATA AND THE DEAD ZONE ---\n",
            1135: "\n--- OVERNIGHT DRIFT ---\n",
            1192: "\n--- PORTFOLIO COMPOSITION: 60% TREND, 40% CARRY ---\n",
            1264: "\n--- MEAN REVERSION AND STAT-ARB ---\n",
            1323: "\n--- RISK MANAGEMENT VS. OPTIMIZATION ---\n",
            1387: "\n--- COMPARING BACKTEST TO LIVE PERFORMANCE ---\n",
            1474: "\n--- MAX DRAWDOWN IS A TERRIBLE METRIC ---\n",
            1590: "\n--- EVALUATING STRATEGY EFFECTIVENESS OVER TIME ---\n",
            1641: '\n--- "THINGS WERE DIFFERENT AFTER 2008" ---\n',
            1700: "\n--- NEW PRODUCTS WITH LIMITED HISTORY ---\n",
            1804: "\n--- BACKTESTING: OWN DATABASE, OWN CODE ---\n",
            1816: "\n--- AI AND LLMs IN TRADING: AN EMPHATIC NO ---\n",
            1865: "\n--- AI'S IMPACT ON AUTOMATED TRADING ---\n",
            1966: "\n--- TAX ARBITRAGE: OPTIONS VS. FUTURES ---\n",
            2041: "\n--- DIVERSIFICATION: THE SQUARE ROOT OF N ---\n",
            2220: "\n--- ACTIVE VS. PASSIVE ---\n",
            2291: "\n--- APRIL 2025 AND CORRELATION IN CRISES ---\n",
            2398: "\n--- ADVICE FOR BEGINNERS ---\n",
            2429: "\n--- CLOSING THOUGHTS AND UPCOMING BOOK ---\n",
        },
    },
}


def add_structure(filename, config):
    """Add metadata header, cold open label, and section headers."""
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    with open(filepath, 'r') as f:
        lines = f.readlines()

    sections = config.get("sections", {})

    # Find where the cold open ends (where the intro starts with host greeting)
    cold_open_end = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if ("Thank you so much" in stripped or
            "thank you so much" in stripped) and i < 20:
            cold_open_end = i
            break
        if "Niels, thank you" in stripped and i < 20:
            cold_open_end = i
            break
        if "Rob, thank you" in stripped and i < 20:
            cold_open_end = i
            break

    # Build the new content
    output_lines = []

    # Add header
    output_lines.append(config["header"])

    # Add cold open label
    if cold_open_end > 0:
        output_lines.append("[COLD OPEN — Key moments from this conversation]\n\n")
        for i in range(cold_open_end):
            line = lines[i]
            stripped = line.strip()
            if stripped.startswith(">>"):
                stripped = stripped[2:].strip()
            if stripped:
                output_lines.append(f"  \"{stripped}\"\n")
        output_lines.append("\n")

    # Process main transcript with section headers
    # Keep >> as speaker-change markers but clean them up visually
    for i in range(cold_open_end, len(lines)):
        line = lines[i]
        stripped = line.strip()
        line_num = i + 1  # 1-indexed

        # Check if we need a section header before this line
        if line_num in sections:
            output_lines.append(sections[line_num] + "\n")

        # Clean up >> markers into a cleaner visual indicator
        if stripped.startswith(">>"):
            content = stripped[2:].strip()
            if content:
                output_lines.append(f"\n>> {content}\n")
            # else: empty >> line, skip
        elif stripped.startswith("[") and stripped.endswith("]"):
            # Stage directions like [music], [laughter]
            output_lines.append(f"\n{stripped}\n\n")
        elif stripped:
            output_lines.append(f"{stripped}\n")
        else:
            output_lines.append("\n")

    with open(filepath, 'w') as f:
        f.write(''.join(output_lines))

    print(f"Structured: {filename}")


if __name__ == "__main__":
    for filename, config in EPISODES.items():
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if os.path.exists(filepath):
            add_structure(filename, config)
        else:
            print(f"File not found: {filepath}")
