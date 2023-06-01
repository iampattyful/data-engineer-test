# SQL and Data Modeling

Dataset: NYC Taxi Trips dataset
(https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page)

This dataset contains the pickup and drop off dates, times, and locations for each trip, fare
amounts, rate types, payment types, and driver-reported passenger counts.

1. Write a SQL query to create a partitioned table on the pickup_date column. Assume
   the underlying database supports partitioning.

- Using data from `green_tripdata_2023-03.parquet`

```
CREATE PARTITION FUNCTION daily_partition (datetime)
AS RANGE RIGHT FOR VALUES (
  '2023-03-02', '2023-03-03', '2023-03-04',
  '2023-03-05', '2023-03-06', '2023-03-07',
  '2023-03-08', '2023-03-09', '2023-03-10',
  '2023-03-11', '2023-03-12', '2023-03-13',
  '2023-03-14', '2023-03-15', '2023-03-16',
  '2023-03-17', '2023-03-18', '2023-03-19',
  '2023-03-20', '2023-03-21', '2023-03-22',
  '2023-03-23', '2023-03-24', '2023-03-25',
  '2023-03-26', '2023-03-27', '2023-03-28',
  '2023-03-29', '2023-03-30', '2023-03-31'
);
```

2. Write a SQL query using the window function to calculate the daily average number
   of trips and total revenue, then rank the dates based on total revenue.

```
SELECT
  date_trunc('day', lpep_pickup_datetime) AS pickup_date,
  COUNT(*) AS trip_count,
  AVG(COUNT(*)) OVER (ORDER BY date_trunc('day', lpep_pickup_datetime) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS avg_daily_trip_count,
  SUM(total_amount) AS total_daily_revenue,
  RANK() OVER (ORDER BY SUM(total_amount) DESC) AS revenue_rank
FROM green_tripdata_2023-03
GROUP BY pickup_date
ORDER BY revenue_rank;
```
