# Business Impact

## Cost Assumptions

Two dollar values drive the analysis below. Both are illustrative business assumptions, not researched figures, and neither is derived from PaySim, whose amount values are simulator units, not real currency.

- Average loss per missed fraud: $500 per fraudulent transaction that goes uncaught.
- Average friction cost per false positive: $5 per legitimate transaction blocked or flagged, covering support handling and the churn risk of inconveniencing a genuine customer.

## Net Value at the Cost-Minimizing Threshold

At a score threshold of 0.55, the model catches 1,645 of 1,654 fraud transactions in the test split while flagging 2,937 legitimate transactions as false positives. Prevented fraud value is $822,500. Friction cost is $14,685. Net value is $807,815.

The natural comparison point is not screening at all. At a threshold of 1.00, nothing is ever flagged. Every fraud transaction goes uncaught, prevented fraud value is $0, friction cost is $0, and net value is $0. Against that true no-screening baseline, the cost-minimizing threshold delivers the full $807,815 in net value.

A second, separate comparison point is worth stating plainly, since it is easy to confuse with the true no-screening baseline: flagging every single transaction, at a threshold of 0.00. This is the opposite extreme from not screening at all. It catches all 1,654 fraud transactions, for a prevented fraud value of $827,000, but flags 121,926 legitimate transactions along with them, for a friction cost of $609,630. Net value at this threshold is $217,370, positive, but far below what the cost-minimizing threshold delivers. Flagging everything is not the same decision as flagging nothing, and the two produce very different net value.

The cost-minimizing threshold of 0.55 outperforms the flag-everything threshold by $590,445 in net value, and outperforms the true no-screening baseline by the full $807,815.

## Conclusion

Under these two stated cost assumptions, scoring transactions and reviewing only the ones above the cost-minimizing threshold is worth substantially more than either extreme: doing nothing, or reviewing every transaction indiscriminately. The dollar figures here move directly with the two assumptions above. A different average fraud loss or a different average friction cost changes every number in this section, though not the direction of the conclusion: a threshold set well above zero and well below one captures most of the achievable value.

## Risk-Weighted Exposure

Beyond the fraud probability itself, each transaction also receives an expected dollar exposure figure, the fraud probability multiplied by the transaction amount. This is useful for prioritizing review by financial impact rather than fraud likelihood alone, since two transactions with the same fraud probability can represent very different dollar risk. The same figure is accumulated per account, giving a running exposure total across an account's scored transactions. This aggregation is described further, along with its dataset limitations, elsewhere in this report set.
