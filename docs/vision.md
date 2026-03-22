# Vision

> This document describes the long-term platform vision. For current status, see `live_status_summary.md` and `go_live_phases.md`.

## Project Name
`options_algo_v2`

## Vision Statement
`options_algo_v2` is a production-oriented options signal, qualification, and monitoring platform designed to map market regime, underlying directional state, implied volatility conditions, liquidity quality, and portfolio constraints into tradable defined-risk options structures.

The long-term vision is to build a system that is:

- systematic
- reproducible
- explainable
- risk-aware
- execution-conscious
- incrementally automatable

The system is not intended to be a generic “options scanner.” It is intended to become a disciplined decision engine that helps answer:

> Given the current market regime, underlying setup, volatility state, and chain quality, should a trade be placed, and if so, what is the best defined-risk structure to express that view?

## Why This Exists
Most weak options systems fail because they do one or more of the following:

- treat all bullish or bearish views the same
- ignore implied volatility context
- ignore execution quality and liquidity
- ignore event risk
- optimize entries while neglecting lifecycle management
- overcomplicate with ML before establishing a deterministic baseline

`options_algo_v2` is being built to avoid those failure modes.

## Core Principles

### 1. Structure selection matters
The same directional thesis should not always be expressed with the same options structure.

### 2. No-trade is a valid outcome
The system should reject mediocre or untradeable setups rather than force expression.

### 3. Risk and execution quality are first-class
A good chart setup with poor chain quality is not a good trade.

### 4. Determinism before sophistication
A clean rule-based baseline comes before ML, adaptive ranking, or automation.

### 5. Research and production must remain separable
The platform should support iteration without destabilizing production logic.

## Long-Term Platform Goals
Over time, the platform should support:

- nightly and scheduled intraday signal generation
- deterministic strategy qualification
- contract-aware options structure selection
- paper trading and lifecycle monitoring
- realistic backtesting and simulation
- structured trade outcome logging
- portfolio and exposure governance
- eventual semi-automated execution
- later-stage ML/meta-label ranking overlays

## Near-Term Goal
The near-term goal is much narrower:

> Build a deterministic MVP that scans a fixed universe of liquid US equities and ETFs, classifies regime and directional setup, selects one of four defined-risk vertical spreads when conditions are favorable, rejects low-quality setups, and tracks paper position lifecycle with explicit rules.

## What the MVP Is Not
The MVP is not intended to be:

- a full high-frequency system
- an unattended live trading bot
- a multi-strategy volatility arbitrage platform
- a discretionary overlay platform
- a broker-execution-first system

It is a disciplined first production foundation.

## Intended Operating Model
The system should initially operate through:

- nightly signal generation
- pre-market qualification
- scheduled intraday execution/monitoring windows
- paper-trade lifecycle management
- structured logging and auditability

## Data Philosophy
The system depends on professional-grade data alignment.

Primary intended data roles:

- **Databento** for underlying market data and market context
- **Polygon** for options chain, Greeks, IV, and contract qualification
- **IBKR** for execution, fill state, and held-position reconciliation

## Success Definition
The project is successful if it can reliably do the following:

1. generate deterministic high-quality candidate signals
2. reject low-quality or untradeable setups
3. map directional setups to the appropriate defined-risk vertical spread
4. manage positions with explicit lifecycle rules
5. support realistic backtesting and paper trading
6. produce a dataset and architecture that can later support careful ML overlays

## Build Philosophy
The system will be built in phases:

1. deterministic rules and invariant tests
2. candidate generation engine
3. options structure construction
4. paper lifecycle management
5. simulation and analytics
6. only later ML and execution automation

This sequence is deliberate. The goal is not to build a flashy system quickly; the goal is to build a trustworthy system correctly.
