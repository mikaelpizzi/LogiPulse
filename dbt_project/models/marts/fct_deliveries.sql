with delivery_performance as (
    select *
    from {{ ref('int_delivery_perf') }}
)

select
    order_id,
    user_id,
    driver_id,
    amount,
    zone,
    category,
    created_at,
    delay_minutes,
    is_severely_delayed
from delivery_performance
