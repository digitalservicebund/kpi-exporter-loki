Collect kpis from Loki and send them to a metrics endpoint.

Requires a config in this form:

```yaml
---
endpoint: "https://your-metrics-endpoint"
queries:
  metric1: '{app="myapp"} |= "some values"'
  metric2: '{app="myapp",someLabel="some label value"}"'
```
