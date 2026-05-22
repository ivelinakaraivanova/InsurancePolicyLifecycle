# Insurance Policy Lifecycle — Data Dictionary

Reference date for lifecycle logic: **2018-12-31**

---

## Raw / Bronze Layer

Both source CSVs share the same 16 columns. Bronze adds one audit column.

| Column              | Type (raw) | Description                                   |
|---------------------|------------|-----------------------------------------------|
| OBJECT_ID           | string     | Unique policy identifier                      |
| INSR_BEGIN          | string     | Policy start date (`dd-MMM-yy`)               |
| INSR_END            | string     | Policy end date (`dd-MMM-yy`)                 |
| INSR_TYPE           | integer    | Insurance product code (1201, 1202, 1204)     |
| PREMIUM             | decimal    | Annual premium amount                         |
| INSURED_VALUE       | decimal    | Declared vehicle value (0 = not recorded)     |
| CLAIM_PAID          | decimal    | Total claims paid; null = no claim            |
| MAKE                | string     | Vehicle manufacturer                          |
| TYPE_VEHICLE        | string     | Vehicle body type                             |
| CCM_TON             | decimal    | Engine capacity (cc) or tonnage               |
| SEATS_NUM           | integer    | Number of seats                               |
| CARRYING_CAPACITY   | decimal    | Maximum carrying weight                       |
| PROD_YEAR           | integer    | Vehicle production year                       |
| EFFECTIVE_YR        | string     | Regulatory effective year code (alphanumeric) |
| SEX                 | integer    | Policyholder sex (0=unknown, 1=male, 2=female)|
| USAGE               | string     | Vehicle usage category                        |
| bronze_processed_at | timestamp  | Timestamp when row was written to Bronze      |

---

## Silver Layer

Adds cleaned, derived, and normalised columns. All columns renamed to snake_case.

| Column               | Type      | Description                                              |
|----------------------|-----------|----------------------------------------------------------|
| *(all Bronze cols)*  | —         | Inherited and cleaned                                    |
| insr_begin           | date      | Parsed start date (DateType)                             |
| insr_end             | date      | Parsed end date (DateType)                               |
| insured_value        | decimal   | Null where original value was 0                          |
| claim_paid           | decimal   | 0.0 where null (no claim filed)                          |
| policy_duration_days | integer   | `insr_end − insr_begin` in days                          |
| vehicle_age          | integer   | `YEAR(insr_begin) − prod_year`                           |
| premium_segment      | string    | `low` (<756) / `medium` (<9641) / `high`                 |
| value_segment        | string    | `unknown` / `low` (<730k) / `medium` (<2M) / `high`      |
| silver_processed_at  | timestamp | Timestamp when row was written to Silver                 |

**Rows removed in Silver cleaning:**

- Corrupt rows: SEX not in {0, 1, 2}
- Null or invalid dates
- `insr_end < insr_begin`
- `PREMIUM ≤ 0` or null
- Exact duplicates on `(object_id, insr_begin, insr_end)`

Final row count: **800,076**

---

## Gold Layer

Adds lifecycle business logic columns.

| Column            | Type      | Description                                                         |
|-------------------|-----------|---------------------------------------------------------------------|
| lifecycle_status  | string    | `active` / `expired` / `future` relative to 2018-12-31             |
| is_active         | boolean   | True when `lifecycle_status = 'active'`                             |
| is_expired        | boolean   | True when `lifecycle_status = 'expired'`                            |
| renewal_candidate | boolean   | Expired AND `insr_end` within 90 days before reference date         |
| risk_score        | integer   | 0–3 composite: claim paid (>0) + null insured_value + vehicle age >15 |
| gold_processed_at | timestamp | Timestamp when row was written to Gold                              |

---

## PostgreSQL Star Schema (`insurance_db`)

### `dim_vehicle`

| Column            | Type    | Description                 |
|-------------------|---------|-----------------------------|
| vehicle_id        | integer | Surrogate PK                |
| make              | text    | Vehicle manufacturer        |
| type_vehicle      | text    | Body type                   |
| ccm_ton           | numeric | Engine capacity or tonnage  |
| seats_num         | integer | Number of seats             |
| carrying_capacity | numeric | Max carrying weight         |
| usage             | text    | Usage category              |

### `dim_insurance_type`

| Column            | Type    | Description                               |
|-------------------|---------|-------------------------------------------|
| insurance_type_id | integer | Surrogate PK                              |
| insr_type_code    | integer | Original code (1201, 1202, 1204)          |
| insr_type_name    | text    | `Third party` / `Comprehensive` / `Other` |

### `dim_date`

| Column      | Type     | Description                      |
|-------------|----------|----------------------------------|
| date_id     | integer  | YYYYMMDD surrogate PK            |
| full_date   | date     | Calendar date                    |
| year        | smallint | Year                             |
| quarter     | smallint | Quarter (1–4)                    |
| month       | smallint | Month (1–12)                     |
| month_name  | text     | e.g. `January`                   |
| day         | smallint | Day of month                     |
| day_of_week | smallint | 0=Sunday … 6=Saturday            |
| day_name    | text     | e.g. `Monday`                    |
| is_weekend  | boolean  | True for Saturday / Sunday       |

Covers **2011-01-01 → 2020-12-31**.

### `fact_policies`

| Column               | Type     | Description                            |
|----------------------|----------|----------------------------------------|
| fact_id              | bigint   | Surrogate PK                           |
| object_id            | bigint   | Source policy identifier               |
| vehicle_id           | integer  | FK → dim_vehicle                       |
| insurance_type_id    | integer  | FK → dim_insurance_type                |
| insr_begin_id        | integer  | FK → dim_date (policy start)           |
| insr_end_id          | integer  | FK → dim_date (policy end)             |
| prod_year            | smallint | Vehicle production year                |
| sex                  | smallint | 0=unknown / 1=male / 2=female          |
| insured_value        | numeric  | Declared vehicle value                 |
| premium              | numeric  | Annual premium                         |
| claim_paid           | numeric  | Claims paid amount                     |
| policy_duration_days | integer  | Duration in days                       |
| vehicle_age          | smallint | Age of vehicle at policy start         |
| premium_segment      | text     | low / medium / high                    |
| value_segment        | text     | unknown / low / medium / high          |
| lifecycle_status     | text     | active / expired / future              |
| is_active            | boolean  | —                                      |
| is_expired           | boolean  | —                                      |
| renewal_candidate    | boolean  | —                                      |
| risk_score           | smallint | 0–3 composite risk score               |
