DO $$
DECLARE
    t text;
BEGIN
    -- List of tables to apply permissive policies for conthunt_service
    -- Includes all tables in the application so far
    FOREACH t IN ARRAY ARRAY[
        'users',
        'searches',
        'platform_calls',
        'content_items',
        'search_results',
        'media_assets',
        'boards',
        'board_items',
        'chats',        
        'twelvelabs_assets',
        'video_analyses'
    ]
    LOOP
        -- Enable RLS (idempotent-ish, harmless if already on)
        EXECUTE format('ALTER TABLE conthunt.%I ENABLE ROW LEVEL SECURITY', t);

        -- SELECT
        EXECUTE format('DROP POLICY IF EXISTS %I_select_service ON conthunt.%I', t, t);
        EXECUTE format('CREATE POLICY %I_select_service ON conthunt.%I FOR SELECT TO conthunt_service USING (true)', t, t);

        -- INSERT
        EXECUTE format('DROP POLICY IF EXISTS %I_insert_service ON conthunt.%I', t, t);
        EXECUTE format('CREATE POLICY %I_insert_service ON conthunt.%I FOR INSERT TO conthunt_service WITH CHECK (true)', t, t);

        -- UPDATE
        EXECUTE format('DROP POLICY IF EXISTS %I_update_service ON conthunt.%I', t, t);
        EXECUTE format('CREATE POLICY %I_update_service ON conthunt.%I FOR UPDATE TO conthunt_service USING (true)', t, t);

        -- DELETE
        EXECUTE format('DROP POLICY IF EXISTS %I_delete_service ON conthunt.%I', t, t);
        EXECUTE format('CREATE POLICY %I_delete_service ON conthunt.%I FOR DELETE TO conthunt_service USING (true)', t, t);
    END LOOP;
END
$$;
