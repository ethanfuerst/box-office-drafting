MODEL (
  name cleaned.movie_multiplier_overrides,
  kind FULL
);

select
    value as movie
    , try_cast(multiplier as double) as multiplier
from raw.multipliers_and_exclusions
where type = 'movie'
