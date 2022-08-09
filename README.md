# KPI export from Loki

Collect data from Loki and send them to a NocoDB endpoint.

## Configuration

Expects a config file under `/opt/config.yaml`.

Example:

```yaml
---
- endpoint: "https://your-metrics-endpoint"
  type: metricCounts
  queries:
    metric1: '{app="myapp"} |= "some values"'
    metric2: '{app="myapp",someLabel="some label value"}"'
- endpoint: "https://your-other-metrics-endpoint"
  type: rowsFromLabels
  query: '{app="myapp",} |= "some query" | pattern "<_> some event took place. somevalue=<aLabelIWantToExtract> anothervalue=<anotherLabelIWantToExtract>"'
  labelMapping:
    aLabelIWantToExtract: columnNameInNocoDB
    anotherLabelIWantToExtract: anotherColumnNameInNocoDB
  timestampMapping: timestampColumnNameInNocoDB
```

### Config file structure

The yaml file should contain a list of objects. Different types of endpoints are supported.

#### `type: metricCounts`

This uses LogQL metrics queries to extract one or more metrics which are mapped to NocoDB columns. It appends a single row to the table.

Configuration:

- `endpoint` (required): the API endpoint for POSTing a single row to a NocoDB table
- `type` (required): `metricCounts`
- `queries` (required): a map of column names in your NocoDB table to queries used to fetch metrics values to store in those columns

#### `type: rowsFromLabels`

This uses LogQL log queries to extract rows which are mapped to NocoDB rows. It appends a row per log event.

Configuration:

- `endpoint` (required): the bulk API endpoint for POSTing multiple rows to a NocoDB table
- `type` (required): `rowsFromLabels`
- `query` (required): the query to load log events
- `labelMapping` (required): a mapping of Loki labels on the log event to column names in your NocoDB table
- `timestampMapping` (optional): if present, the timestamp of the log event will be written to the column named here
