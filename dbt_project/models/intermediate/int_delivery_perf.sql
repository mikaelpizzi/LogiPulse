with staging_orders as (
    select *
    from {{ ref('stg_orders') }}
)

select
    order_id,
    user_id,
    driver_id,
    status,
    amount,
    zone,
    category,
    created_at,
    estimated_delivery_minutes,
    actual_delivery_minutes,
    actual_delivery_minutes - estimated_delivery_minutes as delay_minutes,
    case
        when actual_delivery_minutes - estimated_delivery_minutes > 15 then true
        else false
    end as is_severely_delayed
from staging_orders
where status = 'DELIVERED'
  and actual_delivery_minutes is not null
