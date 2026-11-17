# Technical decisions

## 1) Why a clean customer base before segmentation?

The project starts with a customer-level base table because most downstream work (RFM, LTV, and persona recommendations) needs a single record per customer. We aggregate transactions to unique customer IDs, compute lifetime revenue, recency, and repeat purchase flags, and then keep those metrics in a stable dataset. This simplifies both modelling and explanation in interviews: the data science and marketing logic sit on the same source of truth.

Limitations: this approach is intentionally simple. If the dataset has more granular product or shipping logic, we would need to include these dimensions later to improve profitability or cohort analysis.

## 2) Why simulated media spend is acceptable for the first version

The Olist dataset does not contain channel-level marketing investment, so the project uses a fixed-seed synthetic spend table to create a credible planning layer. The values are not real media data; they are assumptions for CAC, ROAS, and payback analysis. This is acceptable for a portfolio project because the goal is to show decision-making logic, not to claim causal attribution from an unavailable source.

Limitations: the spend and order relationships are not observationally grounded. They are scenario assumptions designed to make the funnel and allocation model readable and testable.

## 3) Why business KPI logic is deliberately simple and explainable

The first version uses direct formulas for revenue, average order value, repeat purchase rate, CAC, ROAS, and payback. We keep the calculations transparent and easy to validate in unit tests, instead of introducing complex attribution or channel-mix optimization too early. This matches a beginner-friendly portfolio project while still making the underlying business logic understandable.

Limitations: this is a heuristic model, not a full financial BI layer. Gross margin, retention, and channel incrementality would require richer data and more advanced attribution methods.

## 4) Why K-means after RFM instead of a more complex clustering model

The project uses RFM as the feature layer and K-means as the clustering step because the goal is interpretability. RFM is a familiar marketing lens and K-means is easy to explain in interviews: we describe what each cluster means in terms of recency, frequency, and monetary value. We also evaluate K with elbow and silhouette to keep the choice grounded rather than arbitrary.

Limitations: K-means assumes spherical clusters and is sensitive to scaling and outliers. If the portfolio later needs richer customer behavior patterns, a more advanced clustering approach or a mixed-feature model could be considered.

## 5) Why the default LTV model is simple and explainable instead of a full BG/NBD + Gamma-Gamma implementation

The first data-science version favors a transparent frequency-based LTV estimator because the business question is segment value, not a perfect probabilistic engine. It converts observed purchase behavior into a directional estimate of annualized repeat value, which is easier to explain and validate in a portfolio project. It also keeps our segment-level value reporting aligned with the earlier, simpler marketing KPI layer.

Limitations: this is not a causal or predictive survival model in the statistical sense. A full BG/NBD + Gamma-Gamma approach would offer richer customer lifetime modeling, but it would also require more assumptions and a deeper explanation of calibration and retention modeling.

## 6) Why the GTM brief generator uses a fallback plus API path

The project supports both a local fallback and an Anthropic API flow. The fallback is intentionally deterministic and business-safe, so the app can still be demoed without an API key. When the key is available, we call the model to generate a richer brief on top of the same segment logic. This hybrid design is especially useful for a portfolio project because it keeps the product usable even in environments with restricted external access.

Limitations: the LLM output is still a planning artifact, not a source of truth. It should be reviewed by a marketer or PM before execution, especially for brand-sensitive messaging and channel recommendations.

## 7) Why the budget simulator is heuristic and explicitly framed as a scenario model

The reallocation feature uses a simple model that mixes channel efficiency and segment affinity to estimate the impact of moving X% of spend between channels. The idea is to make the logic easy to explain in interviews and test in code, while keeping assumptions visible. It is intentionally not marketed as an optimization engine or causal estimate.

Limitations: this simulator does not account for cross-channel effects, diminishing returns beyond the first allocation step, or true incrementality measurement. It is best treated as a directional planning aid, not a financial forecast for execution.
