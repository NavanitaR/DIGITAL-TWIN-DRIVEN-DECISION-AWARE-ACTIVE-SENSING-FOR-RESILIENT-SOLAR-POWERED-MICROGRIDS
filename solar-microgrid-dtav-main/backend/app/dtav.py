"""Discrete Bayesian EVSI approximation over uncertain solar power.

Actions are safe service bundles. Cost is normalized unmet service + overload.
Quadrature states represent uncertainty, not three arbitrary trigger thresholds.
"""

import numpy as np

ACTIONS = np.array([0.0, 1.0, 4.0, 6.0])


def losses(power):
    return (6 - ACTIONS)[None, :] + 12 * np.maximum(
        0, ACTIONS[None, :] + 0.5 - power[:, None]
    )


def decision_value(mean, sigma, measurement_sigma=0.15, cost=0.08):
    sigma = max(0.001, sigma)
    z = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    weights = np.exp(-z * z / 2)
    weights /= weights.sum()
    states = np.maximum(0, mean + sigma * z)
    prior = losses(states)
    risks = weights @ prior
    action = int(np.argmin(risks))
    # Observation likelihood determines posterior action after each possible result.
    outcomes = states.copy()
    likelihood = np.exp(
        -0.5 * ((outcomes[:, None] - states[None, :]) / measurement_sigma) ** 2
    )
    posterior = likelihood * weights[None, :]
    probability = posterior.sum(axis=1)
    posterior /= probability[:, None]
    probability /= probability.sum()
    expected = float(probability @ np.min(posterior @ prior, axis=1))
    evsi = max(0, float(risks[action]) - expected)
    posterior_actions = np.argmin(posterior @ prior, axis=1)
    useful = len(set(posterior_actions.tolist())) > 1
    return dict(
        action=float(ACTIONS[action]),
        evsi=evsi,
        cost=cost,
        request=bool(useful and evsi > cost),
        sigma=sigma,
        candidate_actions=ACTIONS.tolist(),
        expected_loss=float(risks[action]),
        measurement="solar_available_w",
    )


class Sensing:
    def __init__(self, strategy="dtav"):
        self.strategy = strategy
        self.last = -100.0
        self.last_tx = -100.0
        self.mean = 0.0
        self.reports = 0
        self.requests = 0
        self.total = 0
        self.decision = {}

    def step(self, t, truth, available=True):
        age = t - self.last
        sigma = 0.2 + 0.12 * max(0, age)
        self.decision = decision_value(self.mean, sigma)
        report = self.strategy == "periodic" and t - self.last_tx >= 30
        if self.strategy == "continuous":
            report = True
        if self.strategy == "event":
            report = (
                abs(truth - self.mean) > 1 and t - self.last_tx >= 1
            ) or t - self.last_tx >= 60
        if self.strategy == "dtav":
            report = (
                self.decision["request"] and t - self.last_tx >= 2
            ) or t - self.last_tx >= 60
        if report:
            self.last_tx = t
            self.reports += 1
            if available:
                self.mean = truth
                self.last = t
            if self.strategy == "dtav" and self.decision["request"]:
                self.requests += 1
        self.total += 1
        return report, dict(
            self.decision,
            estimate=self.mean,
            age_s=max(0, t - self.last),
            reports=self.reports,
            requests=self.requests,
            communication_savings=1 - self.reports / self.total,
            strategy=self.strategy,
            model_error_w=abs(truth - self.mean),
            action_after=decision_value(
                self.mean, 0.2 if available and report else sigma
            )["action"],
            delivered=bool(available and report),
        )
