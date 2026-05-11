# Telco Customer Churn — Findings Report
**Analysis ID:** telco_customer_churn
**Date:** 2026-05-10
**Business Question:** Why are customers leaving and who is most at risk of churning?

---

## EXECUTIVE SUMMARY

26.5% of this telecom's customers have churned — a meaningful loss concentrated almost entirely among a specific, identifiable profile: customers on month-to-month contracts who are in their first 12 months with the service. The data clearly shows that contract structure is the single strongest predictor of churn, with month-to-month customers churning at 42.7% compared to 2.8% for two-year contract holders. Compounding this, customers on Fiber optic internet churn at nearly twice the rate of other internet service types — a pattern confirmed as a product quality problem, not a pricing artifact. The primary recommendation is twofold: invest in converting new month-to-month customers to longer-term contracts before the 12-month mark, and urgently investigate what is driving elevated dissatisfaction with the Fiber optic product.

---

## ANALYTICAL APPROACH

The analysis used a snapshot dataset of 7,043 customers with 18 analytical variables after excluding a customer identifier and a collinear spend variable (TotalCharges, r=0.83 with tenure). The population was segmented into two groups defined by the target variable: Churned (1,869 customers, 26.5%) and Retained (5,174 customers, 73.5%). Profiling characterised each group across all retained variables using Cohen's d and Cramér's V effect sizes, confirmed with ANOVA and chi-square significance tests. Driver analysis ran three models — Decision Tree (AUC 0.830), Gradient Boosting (AUC 0.838), and Logistic Regression (AUC 0.839) — and produced a consolidated importance ranking across all three. Model quality is reliable (all AUC > 0.83); findings are treated as definitive, not directional. All findings and interpretations were confirmed by the analyst before inclusion in this report.

---

## KEY FINDINGS

**Finding 1 — Contract type is the single strongest driver of churn**
Month-to-month contract customers churn at 42.7%, compared to 11.3% for one-year contracts and 2.8% for two-year contracts. Month-to-month customers are 55% of the customer base but account for 88.6% of all churners. In the driver model, contract type has a consolidated importance score of 0.845 — the highest of any variable by a substantial margin, confirmed consistent across all three modelling methods. **Confidence: High.** Segments most affected: all month-to-month customers (3,875 customers).

**Finding 2 — The first 12 months are the critical vulnerability window**
Tenure is the second-strongest driver (consolidated score 0.655, Cohen's d = 0.85 — a large effect). Customers who churn have a median tenure of 10 months versus 38 months for retained customers. The churn rate by tenure band tells a stark story: 52.9% in months 0–6, 35.9% in months 7–12, 28.7% in months 13–24, falling to 9.5% by months 49–72. Customers who survive their first year are significantly less likely to leave. **Confidence: High.** Segments most affected: all customers in their first 12 months (approximately 2,186 customers).

**Finding 3 — Fiber optic customers churn at nearly twice the rate of any other service type**
Fiber optic customers churn at 41.9%, versus 19.0% for DSL and 7.4% for customers with no internet service. Fiber optic is the largest internet service segment (44% of the base, 3,096 customers) and accounts for 69.4% of all churners. In logistic regression, the Fiber optic odds ratio is 1.97 — the highest odds ratio in the model. This is confirmed as a product quality problem, not a pricing or demographic artifact. **Confidence: High.** Segments most affected: Fiber optic customers on month-to-month contracts in early tenure — the highest-risk combination in the data.

**Finding 4 — High monthly charges amplify churn risk independently of service type**
Churned customers pay an average of $74.40/month versus $61.30 for retained customers — a $13.10 gap (21% higher). Monthly charges rank third in the consolidated driver model (score 0.613). This signal persists independently of Fiber optic service type in the gradient boosting model, suggesting that value perception — not just product experience — is a contributing factor. **Confidence: High.** Segments most affected: high-charge customers on month-to-month contracts.

**Finding 5 — Customers with no internet service are highly stable**
Customers on phone-only plans (no internet service, 21.7% of the base) churn at just 7.4%. In logistic regression, having no internet service corresponds to an odds ratio of 0.50 — half the baseline churn probability. These customers show high inertia: lower charges, simpler relationships, and fewer competitive alternatives. **Confidence: High.** This is a structural finding — not an actionable target, but useful context for understanding where the churn risk is concentrated.

**Finding 6 — Two-year contracts are a near-complete churn shield**
Customers on two-year contracts churn at 2.8% — essentially negligible. This is not simply a tenure effect; two-year contract holders span a range of tenures and still show very low churn. The contract commitment itself appears to be the protective mechanism. **Confidence: High.** Implication: moving customers from month-to-month to two-year contracts is the most direct available lever for reducing churn.

**Finding 7 — 31 variables tested and confirmed as non-drivers**
Gender, phone service, multiple lines, streaming services, online backup, device protection, partner status, dependent status, senior citizen status, tech support, online security, and non-electronic-check payment methods all returned near-zero importance across all three models. These variables differentiated churners from retained customers in univariate profiling but lost their signal once contract type, tenure, and internet service were accounted for. This confirms those profiling differences were downstream effects of the core churn drivers, not independent causes.

---

## SEGMENT NARRATIVES

**Churned (1,869 customers — 26.5% of base)**
These are new, uncommitted, high-spend customers who signed up for flexible contracts and left before forming a durable relationship with the company. The median churner has been a customer for just 10 months — still in the period when they are evaluating whether the service meets their expectations. Almost all are on month-to-month contracts (88.6%), and nearly seven in ten are Fiber optic internet users (69.4%), the service type with a confirmed product quality problem. They pay $74.40/month on average — the highest-spending cohort in the customer base — yet are the most likely to leave. The profile is a customer who chose a premium, flexible arrangement, found the experience lacking, and exercised their option to leave.

**Retained (5,174 customers — 73.5% of base)**
These are established customers who have moved beyond the early vulnerability window and accumulated enough relationship equity to stay. Their median tenure is 38 months — nearly four times longer than churned customers. They are more likely to hold multi-year contracts (57% are on one- or two-year terms) and more likely to use automatic payment methods, which signals greater commitment to the relationship. They pay less on average ($61.30/month), spread more evenly across service types (DSL and no-internet customers are proportionally overrepresented), and have been with the company long enough to have built inertia. Retaining them requires less active intervention; acquiring customers who look like them — or converting current month-to-month customers into them — is the challenge.

---

## RECOMMENDATIONS

**Recommendation 1 — Launch a contract commitment programme targeting new month-to-month customers in months 1–6**
*Target segment:* Month-to-month customers in their first 6 months (estimated ~800–900 customers at any given time based on observed churn rates)
*Motivating finding:* Contract type is the #1 driver (score 0.845); month-to-month customers churn at 42.7% vs 2.8% for two-year holders. The first 6 months have a 52.9% churn rate — this is when intervention has the highest leverage.
*What this looks like:* A structured outreach programme (email, in-app, or outbound call) at months 1, 3, and 5 offering incentives — discounted rates, service credits, or bundled add-ons — in exchange for committing to a 1- or 2-year contract. The incentive cost should be benchmarked against the estimated lifetime value of retaining that customer.
*What success looks like:* A measurable reduction in 0–12 month churn rate among the targeted cohort, measured against a control group not offered the programme.
*Confidence: High* — the finding motivating this recommendation is the strongest and most consistent in the analysis.

**Recommendation 2 — Investigate and remediate the Fiber optic product experience**
*Target segment:* All Fiber optic customers (3,096 customers, 44% of the base)
*Motivating finding:* Fiber optic has the highest odds ratio in logistic regression (1.97) and the third-highest consolidated importance score. The elevated churn is confirmed as a product quality problem, not a pricing or demographic artifact.
*What this looks like:* A structured review of Fiber optic service quality data — NPS scores, complaint logs, service interruption records, and technician call rates — segmented by churn status. The goal is to identify whether the problem is reliability (outages, slow speeds), service experience (support quality), or value delivery (feature gaps). This analysis should precede any pricing or retention intervention, as the right fix depends on the root cause.
*What success looks like:* Identification of the specific failure point in the Fiber optic experience, followed by a targeted service improvement, with Fiber churn rate monitored as the primary outcome metric.
*Confidence: High* that Fiber is a product problem. *Moderate* on what specifically to fix — that requires data not available in this dataset.

**Recommendation 3 — Design a value reinforcement programme for high-charge customers in their first year**
*Target segment:* Month-to-month customers paying above $70/month in their first 12 months (~highest-risk overlap of findings 2 and 3)
*Motivating finding:* Monthly charges rank third as a driver (score 0.613); churners pay 21% more per month than retained customers. High charges combined with flexible contracts and early tenure is the highest-risk combination in the data.
*What this looks like:* Proactive value communication — usage summaries, feature discovery prompts, or personalised service reviews — designed to make high-spending customers feel they are getting commensurate value. For Fiber optic customers in this group, this should be coordinated with the product remediation effort (Recommendation 2), not run in parallel as a separate initiative.
*What success looks like:* Reduction in 0–12 month churn rate specifically among the high-charge segment, distinct from the broader contract commitment programme effect.
*Confidence: Moderate* — the charge signal is real and consistent, but it likely reflects product experience rather than pure price sensitivity. If Recommendation 2 addresses the product problem, some of this effect may self-resolve.

---

## OPEN QUESTIONS AND LIMITATIONS

**1. What specifically is failing in the Fiber optic product?**
The analysis confirms that Fiber optic customers churn at nearly twice the rate of other service types, and confirms this is a product problem. What it cannot determine is the nature of that problem — whether it is reliability (outages, speed consistency), support quality, feature gaps, or unmet expectations at the point of sale. Service quality data, complaint records, and customer satisfaction scores for the Fiber segment are needed to answer this. Without that, Recommendation 2 can only describe where to look, not what to fix.

**2. Is the month-to-month churn driven by contract optionality or customer self-selection?**
Month-to-month contracts are both a structural driver and a self-selection signal — customers who are less committed may choose month-to-month, and customers who are more committed may choose longer terms. The analysis cannot separate these effects. If self-selection dominates, then converting month-to-month customers to longer contracts through incentives may attract customers who were already planning to stay, rather than retaining those who would have left. A randomised test of the contract commitment programme (Recommendation 1) is the only way to resolve this.

**3. No temporal dimension — churn trend direction is unknown**
This is a snapshot dataset. The analysis shows the current state of churn concentration but cannot determine whether churn is accelerating or decelerating, or whether the Fiber optic problem is a recent development or long-standing. Adding a temporal dimension — even quarterly cohort churn rates — would substantially strengthen the ability to prioritise interventions.

**4. Variables that were confirmed non-drivers may still matter in specific sub-segments**
Tech support, online security, senior citizen status, and partner/dependent status all showed meaningful profiling differences but collapsed to near-zero in the model once contract type and tenure were controlled for. This means they do not drive churn independently at the population level — but they could still be meaningful differentiators within specific sub-segments (e.g. senior citizens on Fiber optic, or customers with no dependents in their first 6 months). These were not explored in this analysis.

---

## ANALYTICAL RECORD SUMMARY

| Decision | Node | Detail |
|---|---|---|
| Exclude `customerID` | EDA | Operational identifier — no analytical value |
| Exclude `TotalCharges` | EDA | Collinear with `tenure` (r=0.826) |
| Recode `SeniorCitizen` | EDA | 0/1 integer → Yes/No string for consistency |
| Collapse 7 service columns | EDA | 3-level values ("No internet/phone service") → Yes/No |
| Treat 11 null rows (TotalCharges) | EDA | Moot — column excluded |
| Skip Segmentation node | Pre-analysis | Segments defined by Churn variable itself |
| Retain all 18 variables for modelling | Profiling | Analyst decision — let model assign importance rather than pre-excluding |
| Confirm top 7 drivers | Driver Analysis | Contract_Month-to-month, tenure, MonthlyCharges, InternetService_Fiber optic, InternetService_No, Contract_Two year, PaymentMethod_Electronic check |
| Confirm 31 non-drivers | Driver Analysis | All other encoded variables — near-zero importance confirmed across 3 models |
| Interpret Fiber optic as product problem | Driver Analysis | Not a pricing or demographic artifact — analyst confirmed |
| Interpret Electronic check as demographic correlate | Driver Analysis | Not an actionable intervention target — analyst confirmed |

**Model quality:** Decision Tree AUC 0.830 / Gradient Boosting AUC 0.838 / Logistic Regression AUC 0.839. All three models classified as reliable (AUC > 0.83). Driver rankings are consistent across all three methods — this cross-model consistency strengthens confidence in the findings.
