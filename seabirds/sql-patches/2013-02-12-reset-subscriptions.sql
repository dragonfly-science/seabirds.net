--Reset the subscriptions to ensure that all people who were subscribed in an adhoc way are now subscribed to anything


begin;
insert into profile_userprofile_subscriptions (userprofile_id, listing_id) 
    select id as userprofile_id, 
    1 as listing_id 
    from profile_userprofile 
    where id not in (
        select userprofile_id 
        from profile_userprofile_subscriptions 
        where listing_id=1) 
        and is_valid_seabirder 
        and user_id in (
            select id 
            from auth_user 
            where is_active
        ) 
    order by id
;

insert into profile_userprofile_subscriptions (userprofile_id, listing_id) 
    select id as userprofile_id, 
    2 as listing_id 
    from profile_userprofile 
    where id not in (
        select userprofile_id 
        from profile_userprofile_subscriptions 
        where listing_id=2) 
        and is_valid_seabirder 
        and user_id in (
            select id 
            from auth_user 
            where is_active
        ) 
    order by id
;

insert into profile_userprofile_subscriptions (userprofile_id, listing_id) 
    select id as userprofile_id, 
    3 as listing_id 
    from profile_userprofile 
    where id not in (
        select userprofile_id 
        from profile_userprofile_subscriptions 
        where listing_id=3) 
        and is_valid_seabirder 
        and user_id in (
            select id 
            from auth_user 
            where is_staff
        ) 
    order by id
;

insert into profile_userprofile_subscriptions (userprofile_id, listing_id) 
    select id as userprofile_id, 
    4 as listing_id 
    from profile_userprofile 
    where id not in (
        select userprofile_id 
        from profile_userprofile_subscriptions 
        where listing_id=4) 
        and is_valid_seabirder 
        and user_id in (
            select id 
            from auth_user 
            where is_active
        ) 
    order by id
;

insert into profile_userprofile_subscriptions (userprofile_id, listing_id) 
    select id as userprofile_id, 
    5 as listing_id 
    from profile_userprofile 
    where id not in (
        select userprofile_id 
        from profile_userprofile_subscriptions 
        where listing_id=5) 
        and is_valid_seabirder 
        and user_id in (
            select id 
            from auth_user 
            where is_active
        ) 
    order by id
;

commit;
