// edge_physics/src/lib.rs
// PyO3 bridge exposing Rust physics engine to Python

mod black_scholes;
mod repair_engine;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::black_scholes::{BlackScholesCalculator, Greeks};
use crate::repair_engine::{Position, RepairEngine, RepairPlan};

/// Python wrapper for Greeks
#[pyclass]
#[derive(Clone, Copy)]
pub struct GreeksWrapper {
    #[pyo3(get)]
    pub delta: f64,
    #[pyo3(get)]
    pub gamma: f64,
    #[pyo3(get)]
    pub theta: f64,
    #[pyo3(get)]
    pub vega: f64,
    #[pyo3(get)]
    pub rho: f64,
}

impl From<Greeks> for GreeksWrapper {
    fn from(greeks: Greeks) -> Self {
        GreeksWrapper {
            delta: greeks.delta,
            gamma: greeks.gamma,
            theta: greeks.theta,
            vega: greeks.vega,
            rho: greeks.rho,
        }
    }
}

#[pymethods]
impl GreeksWrapper {
    fn __repr__(&self) -> String {
        format!(
            "Greeks(delta={:.4}, gamma={:.6}, theta={:.4}, vega={:.4}, rho={:.4})",
            self.delta, self.gamma, self.theta, self.vega, self.rho
        )
    }

    fn to_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item("delta", self.delta)?;
        dict.set_item("gamma", self.gamma)?;
        dict.set_item("theta", self.theta)?;
        dict.set_item("vega", self.vega)?;
        dict.set_item("rho", self.rho)?;
        Ok(dict.into())
    }
}

/// Python wrapper for Black-Scholes calculator
#[pyclass]
pub struct BlackScholesCalc {
    calc: BlackScholesCalculator,
}

#[pymethods]
impl BlackScholesCalc {
    #[new]
    fn new(spot: f64, risk_free_rate: f64) -> Self {
        BlackScholesCalc {
            calc: BlackScholesCalculator::new(spot, risk_free_rate),
        }
    }

    /// Calculate Greeks for a call option
    fn call_greeks(&self, strike: f64, ttm_days: i32, volatility: f64) -> GreeksWrapper {
        self.calc.call_greeks(strike, ttm_days, volatility).into()
    }

    /// Calculate Greeks for a put option
    fn put_greeks(&self, strike: f64, ttm_days: i32, volatility: f64) -> GreeksWrapper {
        self.calc.put_greeks(strike, ttm_days, volatility).into()
    }
}

/// Python wrapper for RepairPlan
#[pyclass]
#[derive(Clone)]
pub struct RepairPlanWrapper {
    #[pyo3(get)]
    pub position_id: String,
    #[pyo3(get)]
    pub ticker: String,
    #[pyo3(get)]
    pub repair_type: String,
    #[pyo3(get)]
    pub delta_drift_pct: f64,
    #[pyo3(get)]
    pub repair_credit: f64,
    #[pyo3(get)]
    pub new_max_loss: f64,
    #[pyo3(get)]
    pub priority: String,
    #[pyo3(get)]
    pub confidence_boost: f64,
}

impl From<RepairPlan> for RepairPlanWrapper {
    fn from(plan: RepairPlan) -> Self {
        RepairPlanWrapper {
            position_id: plan.position_id,
            ticker: plan.ticker,
            repair_type: plan.repair_type,
            delta_drift_pct: plan.delta_drift_pct,
            repair_credit: plan.repair_credit,
            new_max_loss: plan.new_max_loss,
            priority: plan.priority,
            confidence_boost: plan.confidence_boost,
        }
    }
}

#[pymethods]
impl RepairPlanWrapper {
    fn __repr__(&self) -> String {
        format!(
            "RepairPlan(position_id={}, ticker={}, repair_type={}, priority={})",
            self.position_id, self.ticker, self.repair_type, self.priority
        )
    }

    fn to_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item("position_id", &self.position_id)?;
        dict.set_item("ticker", &self.ticker)?;
        dict.set_item("repair_type", &self.repair_type)?;
        dict.set_item("delta_drift_pct", self.delta_drift_pct)?;
        dict.set_item("repair_credit", self.repair_credit)?;
        dict.set_item("new_max_loss", self.new_max_loss)?;
        dict.set_item("priority", &self.priority)?;
        dict.set_item("confidence_boost", self.confidence_boost)?;
        Ok(dict.into())
    }
}

/// Python wrapper for Repair Engine
#[pyclass]
pub struct RepairEngineWrapper {
    engine: RepairEngine,
}

#[pymethods]
impl RepairEngineWrapper {
    #[new]
    fn new() -> Self {
        RepairEngineWrapper {
            engine: RepairEngine::new(),
        }
    }

    /// Analyze a single position for repair needs
    fn analyze_position(
        &self,
        position_id: String,
        ticker: String,
        strategy_type: String,
        current_delta: f64,
        current_gamma: f64,
        current_theta: f64,
        current_vega: f64,
        current_price: f64,
        max_loss: f64,
        unrealized_pnl: f64,
        days_to_expiration: i32,
        account_equity: f64,
    ) -> Option<RepairPlanWrapper> {
        let position = Position {
            id: position_id,
            ticker,
            strategy_type,
            current_delta,
            current_gamma,
            current_theta,
            current_vega,
            current_price,
            max_loss,
            unrealized_pnl,
            days_to_expiration,
        };

        self.engine
            .analyze_position(&position, account_equity)
            .map(|plan| plan.into())
    }

    /// Find optimal hedge strikes for delta neutralization
    fn find_hedge_strikes(
        &self,
        position_id: String,
        ticker: String,
        strategy_type: String,
        current_delta: f64,
        current_gamma: f64,
        current_theta: f64,
        current_vega: f64,
        current_price: f64,
        max_loss: f64,
        unrealized_pnl: f64,
        days_to_expiration: i32,
        underlying_price: f64,
        iv: f64,
    ) -> (f64, f64) {
        let position = Position {
            id: position_id,
            ticker,
            strategy_type,
            current_delta,
            current_gamma,
            current_theta,
            current_vega,
            current_price,
            max_loss,
            unrealized_pnl,
            days_to_expiration,
        };

        self.engine.find_hedge_strikes(&position, underlying_price, iv)
    }
}

/// Main module entry point
#[pymodule]
fn edge_physics(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<GreeksWrapper>()?;
    m.add_class::<BlackScholesCalc>()?;
    m.add_class::<RepairPlanWrapper>()?;
    m.add_class::<RepairEngineWrapper>()?;

    // Add version info
    m.add("__version__", "0.1.0")?;
    m.add("__author__", "RichesReach Engineering")?;

    Ok(())
}
