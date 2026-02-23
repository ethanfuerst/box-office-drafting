MODEL (
  name dashboards.draftee_dashboard,
  kind FULL
);

select
    d.name as draftee_name
    , d.round
    , d.overall_pick
    , d.movie
    , if(bq.title is not null, bq.first_seen_date, null) as first_seen_date
    , if(bq.title is not null, bq.still_in_theaters, null) as still_in_theaters
    , if(bq.title is not null, bq.revenue, null) as revenue
    , coalesce(
        bq.multiplier
        , coalesce(rmo.multiplier, 1) * coalesce(mmo.multiplier, 1)
    ) as multiplier
    , if(bq.title is not null, bq.scored_revenue, null) as scored_revenue
    , if(bq.title is not null, bq.better_pick_title, null) as better_pick
    , if(
        bq.title is not null and bq.better_pick_scored_revenue != 0
        , bq.better_pick_scored_revenue
        , null
    ) as better_pick_scored_revenue
from cleaned.drafter as d
left join combined.base_query as bq
    on d.movie = bq.title
left join cleaned.round_multiplier_overrides as rmo
    on d.round = rmo.round
left join cleaned.movie_multiplier_overrides as mmo
    on d.movie = mmo.movie
order by d.name, d.round, d.overall_pick
