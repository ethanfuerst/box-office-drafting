MODEL (
  name cleaned.box_office_mojo_dump,
  kind FULL
);

select
    title
    , revenue
    , domestic_rev
    , foreign_rev
    , loaded_date
    , release_year
    , published_timestamp_utc
from raw.box_office_mojo_dump
