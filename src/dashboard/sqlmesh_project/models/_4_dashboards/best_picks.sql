MODEL (
  name dashboards.best_picks,
  kind FULL
);

with drafted_movies as (
    select
        title
        , drafted_by
        , overall_pick as draft_order_rank
        , revenue
        , scored_revenue
    from combined.base_query
    where drafted_by is not null
)

, all_released_movies as (
    select
        title
        , row_number() over (
            order by
                scored_revenue desc
                , title asc
        ) as revenue_order_rank
    from combined.base_query
)

, best_picks_calc as (
    select
        drafted_movies.title
        , drafted_movies.drafted_by
        , drafted_movies.draft_order_rank as overall_pick
        , all_released_movies.revenue_order_rank
        , (drafted_movies.draft_order_rank - all_released_movies.revenue_order_rank) as gap
        , drafted_movies.scored_revenue
    from drafted_movies
    inner join all_released_movies
        on drafted_movies.title = all_released_movies.title
    where (drafted_movies.draft_order_rank - all_released_movies.revenue_order_rank) > 0
        and drafted_movies.scored_revenue > 0
)

select
    row_number() over (
        order by
            gap desc
            , overall_pick asc
    ) as rank
    , title
    , drafted_by
    , overall_pick
    , gap as positions_gained
    , scored_revenue as actual_revenue
from best_picks_calc
order by 1 asc
