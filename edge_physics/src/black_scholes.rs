// edge_physics/src/black_scholes.rs
// High-performance Black-Scholes Greeks calculator in Rust

use std::f64::consts::PI;

/// Greeks for an option
#[derive(Debug, Clone, Copy)]
pub struct Greeks {
    pub delta: f64,
    pub gamma: f64,
    pub theta: f64,
    pub vega: f64,
    pub rho: f64,
}

/// Black-Scholes calculator for options Greeks
pub struct BlackScholesCalculator {
    spot: f64,
    risk_free_rate: f64,
}

impl BlackScholesCalculator {
    /// Create a new calculator
    pub fn new(spot: f64, risk_free_rate: f64) -> Self {
        BlackScholesCalculator {
            spot,
            risk_free_rate,
        }
    }

    /// Standard normal CDF (approximation)
    fn normal_cdf(x: f64) -> f64 {
        0.5 * (1.0 + (x / (1.0 + 0.2316419 * x.abs())).tanh())
    }

    /// Standard normal PDF
    fn normal_pdf(x: f64) -> f64 {
        (-0.5 * x * x).exp() / (2.0 * PI).sqrt()
    }

    /// Calculate d1 from Black-Scholes
    fn d1(&self, strike: f64, ttm_years: f64, volatility: f64) -> f64 {
        if ttm_years <= 0.0 || volatility <= 0.0 {
            return 0.0;
        }
        let numerator = (self.spot / strike).ln()
            + (self.risk_free_rate + 0.5 * volatility * volatility) * ttm_years;
        let denominator = volatility * ttm_years.sqrt();
        numerator / denominator
    }

    /// Calculate d2 from Black-Scholes
    fn d2(&self, strike: f64, ttm_years: f64, volatility: f64) -> f64 {
        let d1 = self.d1(strike, ttm_years, volatility);
        d1 - volatility * ttm_years.sqrt()
    }

    /// Calculate Greeks for a call option
    pub fn call_greeks(
        &self,
        strike: f64,
        ttm_days: i32,
        volatility: f64,
    ) -> Greeks {
        let ttm_years = ttm_days as f64 / 365.25;

        if ttm_years <= 0.0 || volatility <= 0.0 {
            return Greeks {
                delta: 0.0,
                gamma: 0.0,
                theta: 0.0,
                vega: 0.0,
                rho: 0.0,
            };
        }

        let d1 = self.d1(strike, ttm_years, volatility);
        let d2 = self.d2(strike, ttm_years, volatility);

        let n_d1 = Self::normal_cdf(d1);
        let n_prime_d1 = Self::normal_pdf(d1);
        let n_d2 = Self::normal_cdf(d2);

        let delta = n_d1;
        let gamma = n_prime_d1 / (self.spot * volatility * ttm_years.sqrt());
        let vega = self.spot * n_prime_d1 * ttm_years.sqrt() / 100.0; // Per 1% IV
        let theta = (-self.spot * n_prime_d1 * volatility / (2.0 * ttm_years.sqrt())
            - self.risk_free_rate * strike * (-self.risk_free_rate * ttm_years).exp() * n_d2)
            / 365.25; // Per day
        let rho = strike * ttm_years * (-self.risk_free_rate * ttm_years).exp() * n_d2 / 100.0;

        Greeks {
            delta,
            gamma,
            theta,
            vega,
            rho,
        }
    }

    /// Calculate Greeks for a put option
    pub fn put_greeks(
        &self,
        strike: f64,
        ttm_days: i32,
        volatility: f64,
    ) -> Greeks {
        let ttm_years = ttm_days as f64 / 365.25;

        if ttm_years <= 0.0 || volatility <= 0.0 {
            return Greeks {
                delta: 0.0,
                gamma: 0.0,
                theta: 0.0,
                vega: 0.0,
                rho: 0.0,
            };
        }

        let d1 = self.d1(strike, ttm_years, volatility);
        let d2 = self.d2(strike, ttm_years, volatility);

        let n_d1 = Self::normal_cdf(d1);
        let n_prime_d1 = Self::normal_pdf(d1);
        let n_d2 = Self::normal_cdf(d2);

        // Put Greeks: Call Greeks ± adjustments
        let delta = n_d1 - 1.0; // Put delta is negative
        let gamma = n_prime_d1 / (self.spot * volatility * ttm_years.sqrt());
        let vega = self.spot * n_prime_d1 * ttm_years.sqrt() / 100.0;
        let theta = (-self.spot * n_prime_d1 * volatility / (2.0 * ttm_years.sqrt())
            + self.risk_free_rate * strike * (-self.risk_free_rate * ttm_years).exp() * (1.0 - n_d2))
            / 365.25;
        let rho =
            -strike * ttm_years * (-self.risk_free_rate * ttm_years).exp() * (1.0 - n_d2) / 100.0;

        Greeks {
            delta,
            gamma,
            theta,
            vega,
            rho,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_call_greeks() {
        let calc = BlackScholesCalculator::new(100.0, 0.045);
        let greeks = calc.call_greeks(100.0, 30, 0.25);
        
        // For ATM call with 30 DTE and 25% IV, delta should be ~0.56
        assert!((greeks.delta - 0.56).abs() < 0.05);
        assert!(greeks.gamma > 0.0);
        assert!(greeks.vega > 0.0);
    }

    #[test]
    fn test_put_greeks() {
        let calc = BlackScholesCalculator::new(100.0, 0.045);
        let greeks = calc.put_greeks(100.0, 30, 0.25);
        
        // For ATM put with 30 DTE and 25% IV, delta should be ~-0.44
        assert!((greeks.delta + 0.44).abs() < 0.05);
        assert!(greeks.gamma > 0.0);
        assert!(greeks.vega > 0.0);
    }
}
