# Retraining-trigger evidence

Capture the actual threshold logic and monitoring output. Explain that the rule is:

~~~text
PSI >= 0.20 OR drift RMSE > 8.0
~~~

The action is a queued/recommended retraining workflow, not an automatic production deployment.
