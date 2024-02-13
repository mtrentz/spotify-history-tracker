-- There is a problem when adding 'extended-history' of a track
-- that was already added by the 'recently-played' endpoint.
-- On the 'recently-played' you have the 'played_at' with milliseconds
-- and on the 'extended-history' you have the 'played_at' without milliseconds.
-- This causes both to not be counted as duplicated and thus both are added.
-- Moreover, on 'recently-played' you have the 'context' field that is not present on 'extended-history'.
-- And in the 'extended-history' you have the 'reason_start' and 'reason_end' fields that are not present on 'recently-played'.

-- The goal here is that every time a 'extended-history' is added I found these duplicates and merge them!
-- Keeping all relevant information and removing duplicates.


-- Step 1: Create a temp table for duplicates
CREATE TEMP TABLE x_streaming_history_duplicates AS
SELECT
    played_at,
    ms_played,
    track_id,
    context,
    reason_start,
    reason_end,
    skipped,
    shuffle
FROM (
    SELECT *,
    COUNT(*) OVER (PARTITION BY date_trunc('second', played_at), track_id) AS cnt
    FROM public.streaming_history
) sub
WHERE cnt > 1;

-- Step 2: Create another temp table for merged duplicates
CREATE TEMP TABLE merged AS
SELECT
    date_trunc('second', played_at) AS played_at,
    track_id,
    MAX(ms_played) AS ms_played,
    MAX(context) AS context,
    MAX(reason_start) AS reason_start,
    MAX(reason_end) AS reason_end,
    bool_or(skipped) AS skipped,
    bool_or(shuffle) AS shuffle
FROM x_streaming_history_duplicates
GROUP BY date_trunc('second', played_at), track_id;

-- Step 3: Remove duplicates from the original table
DELETE FROM public.streaming_history
WHERE (played_at, track_id) IN (
    SELECT played_at, track_id
    FROM x_streaming_history_duplicates
);

-- Step 4: Add merged duplicates back to the original table
INSERT INTO public.streaming_history (played_at, ms_played, track_id, context, reason_start, reason_end, skipped, shuffle)
SELECT
    played_at,
    ms_played,
    track_id,
    context,
    reason_start,
    reason_end,
    skipped,
    shuffle
FROM merged;