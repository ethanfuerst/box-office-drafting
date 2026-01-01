MODEL (
  name cleaned.box_office_mojo_dump,
  kind FULL
);

with int_ as (
  select
      title
      , revenue::BIGINT as revenue
      , domestic_rev::BIGINT as domestic_rev
      , foreign_rev::BIGINT as foreign_rev
      , loaded_date
      , release_year
      , published_timestamp_utc
  from raw.box_office_mojo_dump
)

select
    title
    , if(revenue = 0, domestic_rev + foreign_rev, revenue) as revenue
    , domestic_rev
    , foreign_rev
    , loaded_date
    , release_year
    , published_timestamp_utc
from int_
