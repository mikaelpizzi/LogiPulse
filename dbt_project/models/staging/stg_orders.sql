with source_data as (
    select *
    from {{ source('raw_logipulse', 'raw_orders') }}
),
deduped as (
    select
        *,
        row_number() over (
            partition by order_id
            order by created_at desc
        ) as row_num
    from source_data
    where order_id is not null
)

select
    order_id,
    user_id,
    driver_id,
    status,
    amount,
    zone,
    category,
    cast(created_at as timestamp) as created_at,
    estimated_delivery_minutes,
    actual_delivery_minutes
from deduped
where row_num = 1
