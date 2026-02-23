--
-- PostgreSQL database dump
--

\restrict cANvuASzRvSKyjs5925ooAluC2phZnZtkfnOFLfirGWlBaWsuM5lJ1A0gnZVqMe

-- Dumped from database version 17.7
-- Dumped by pg_dump version 17.7 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: conthunt; Type: SCHEMA; Schema: -; Owner: conthunt_app
--

CREATE SCHEMA conthunt;


ALTER SCHEMA conthunt OWNER TO conthunt_app;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: board_insights; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.board_insights (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    board_id uuid NOT NULL,
    status text DEFAULT 'processing'::text NOT NULL,
    insights_result jsonb DEFAULT '{}'::jsonb NOT NULL,
    error text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    last_completed_at timestamp with time zone
);

ALTER TABLE ONLY conthunt.board_insights FORCE ROW LEVEL SECURITY;


ALTER TABLE conthunt.board_insights OWNER TO conthunt_app;

--
-- Name: board_items; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.board_items (
    board_id uuid NOT NULL,
    content_item_id uuid NOT NULL,
    added_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE conthunt.board_items OWNER TO conthunt_app;

--
-- Name: boards; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.boards (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    name text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE conthunt.boards OWNER TO conthunt_app;

--
-- Name: chat_tags; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.chat_tags (
    id uuid NOT NULL,
    chat_id uuid NOT NULL,
    tag_type text NOT NULL,
    tag_id uuid NOT NULL,
    tag_label text,
    source text DEFAULT 'user'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    sort_order integer,
    deleted_at timestamp with time zone,
    CONSTRAINT chat_tags_source_check CHECK ((source = ANY (ARRAY['user'::text, 'agent'::text]))),
    CONSTRAINT chat_tags_tag_type_check CHECK ((tag_type = ANY (ARRAY['board'::text, 'search'::text, 'media'::text])))
);


ALTER TABLE conthunt.chat_tags OWNER TO conthunt_app;

--
-- Name: chats; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.chats (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    thread_id text NOT NULL,
    title text,
    status text DEFAULT 'idle'::text NOT NULL,
    active_run_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone,
    context_type text,
    context_id uuid,
    deep_research_enabled boolean DEFAULT false NOT NULL,
    CONSTRAINT chats_context_type_check CHECK ((context_type = ANY (ARRAY['board'::text, 'search'::text]))),
    CONSTRAINT chats_status_check CHECK ((status = ANY (ARRAY['idle'::text, 'running'::text, 'needs_input'::text, 'failed'::text])))
);

ALTER TABLE ONLY conthunt.chats FORCE ROW LEVEL SECURITY;


ALTER TABLE conthunt.chats OWNER TO conthunt_app;

--
-- Name: checkpoint_blobs; Type: TABLE; Schema: conthunt; Owner: conthunt_service
--

CREATE TABLE conthunt.checkpoint_blobs (
    thread_id text NOT NULL,
    checkpoint_ns text DEFAULT ''::text NOT NULL,
    channel text NOT NULL,
    version text NOT NULL,
    type text NOT NULL,
    blob bytea
);


ALTER TABLE conthunt.checkpoint_blobs OWNER TO conthunt_service;

--
-- Name: checkpoint_migrations; Type: TABLE; Schema: conthunt; Owner: conthunt_service
--

CREATE TABLE conthunt.checkpoint_migrations (
    v integer NOT NULL
);


ALTER TABLE conthunt.checkpoint_migrations OWNER TO conthunt_service;

--
-- Name: checkpoint_writes; Type: TABLE; Schema: conthunt; Owner: conthunt_service
--

CREATE TABLE conthunt.checkpoint_writes (
    thread_id text NOT NULL,
    checkpoint_ns text DEFAULT ''::text NOT NULL,
    checkpoint_id text NOT NULL,
    task_id text NOT NULL,
    idx integer NOT NULL,
    channel text NOT NULL,
    type text,
    blob bytea NOT NULL,
    task_path text DEFAULT ''::text NOT NULL
);


ALTER TABLE conthunt.checkpoint_writes OWNER TO conthunt_service;

--
-- Name: checkpoints; Type: TABLE; Schema: conthunt; Owner: conthunt_service
--

CREATE TABLE conthunt.checkpoints (
    thread_id text NOT NULL,
    checkpoint_ns text DEFAULT ''::text NOT NULL,
    checkpoint_id text NOT NULL,
    parent_checkpoint_id text,
    type text,
    checkpoint jsonb NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL
);


ALTER TABLE conthunt.checkpoints OWNER TO conthunt_service;

--
-- Name: content_items; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.content_items (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    platform text NOT NULL,
    external_id text NOT NULL,
    content_type text NOT NULL,
    canonical_url text,
    title text,
    primary_text text,
    published_at timestamp with time zone,
    creator_handle text,
    metrics jsonb DEFAULT '{}'::jsonb NOT NULL,
    payload jsonb NOT NULL,
    raw_gcs_uri text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    author_id text,
    author_name text,
    author_url text,
    author_image_url text
)
WITH (fillfactor='80', autovacuum_vacuum_scale_factor='0.01', autovacuum_vacuum_threshold='2000', autovacuum_analyze_scale_factor='0.005', autovacuum_analyze_threshold='1000', autovacuum_vacuum_cost_limit='2000');


ALTER TABLE conthunt.content_items OWNER TO conthunt_app;

--
-- Name: feature_config; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.feature_config (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    feature text NOT NULL,
    credit_cost integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE conthunt.feature_config OWNER TO conthunt_app;

--
-- Name: media_assets; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.media_assets (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    content_item_id uuid NOT NULL,
    asset_type text NOT NULL,
    source_url text NOT NULL,
    source_url_list jsonb,
    gcs_uri text,
    sha256 text,
    mime_type text,
    bytes bigint,
    width integer,
    height integer,
    duration_ms integer,
    status text DEFAULT 'pending'::text NOT NULL,
    error text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
)
WITH (fillfactor='75', autovacuum_vacuum_scale_factor='0.005', autovacuum_vacuum_threshold='1000', autovacuum_analyze_scale_factor='0.002', autovacuum_analyze_threshold='500', autovacuum_vacuum_cost_limit='3000');


ALTER TABLE conthunt.media_assets OWNER TO conthunt_app;

--
-- Name: pending_plan_changes; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.pending_plan_changes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    subscription_id text NOT NULL,
    target_product_id text NOT NULL,
    target_role text NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    applied_at timestamp with time zone,
    cancelled_at timestamp with time zone,
    CONSTRAINT pending_plan_changes_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'applied'::text, 'cancelled'::text])))
);


ALTER TABLE conthunt.pending_plan_changes OWNER TO conthunt_app;

--
-- Name: platform_calls; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.platform_calls (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    search_id uuid NOT NULL,
    platform text NOT NULL,
    request_params jsonb NOT NULL,
    response_gcs_uri text,
    response_meta jsonb DEFAULT '{}'::jsonb NOT NULL,
    next_cursor jsonb,
    success boolean DEFAULT false NOT NULL,
    http_status integer,
    error text,
    duration_ms integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY conthunt.platform_calls FORCE ROW LEVEL SECURITY;


ALTER TABLE conthunt.platform_calls OWNER TO conthunt_app;

--
-- Name: processed_events; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.processed_events (
    handler_name text NOT NULL,
    event_id uuid NOT NULL,
    idempotency_key text NOT NULL,
    processed_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE conthunt.processed_events OWNER TO conthunt_app;

--
-- Name: reward_balances; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.reward_balances (
    user_id uuid NOT NULL,
    reward_feature text,
    balance integer DEFAULT 0 NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL
);


ALTER TABLE conthunt.reward_balances OWNER TO conthunt_app;

--
-- Name: search_results; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.search_results (
    search_id uuid NOT NULL,
    content_item_id uuid NOT NULL,
    platform text NOT NULL,
    rank integer NOT NULL
);

ALTER TABLE ONLY conthunt.search_results FORCE ROW LEVEL SECURITY;


ALTER TABLE conthunt.search_results OWNER TO conthunt_app;

--
-- Name: searches; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.searches (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    query text NOT NULL,
    inputs jsonb NOT NULL,
    search_hash text NOT NULL,
    mode text DEFAULT 'prefer_cache'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    status text DEFAULT 'running'::text NOT NULL
);

ALTER TABLE ONLY conthunt.searches FORCE ROW LEVEL SECURITY;


ALTER TABLE conthunt.searches OWNER TO conthunt_app;

--
-- Name: streak_milestones; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.streak_milestones (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    role text NOT NULL,
    streak_type_id uuid NOT NULL,
    days_required integer NOT NULL,
    reward_description text NOT NULL,
    icon_name text DEFAULT 'gift'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    reward_feature text,
    reward_credits integer DEFAULT 0 NOT NULL,
    reward_feature_amount integer DEFAULT 0 NOT NULL
);


ALTER TABLE conthunt.streak_milestones OWNER TO conthunt_app;

--
-- Name: streak_reward_grants; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.streak_reward_grants (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    streak_type_id uuid NOT NULL,
    days_required integer NOT NULL,
    role text NOT NULL,
    reward_feature text NOT NULL,
    claimed_at timestamp with time zone DEFAULT now() NOT NULL,
    reward_credits integer DEFAULT 0 NOT NULL,
    reward_feature_amount integer DEFAULT 0 NOT NULL
);


ALTER TABLE conthunt.streak_reward_grants OWNER TO conthunt_app;

--
-- Name: streak_types; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.streak_types (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    slug text NOT NULL,
    label text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE conthunt.streak_types OWNER TO conthunt_app;

--
-- Name: twelvelabs_assets; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.twelvelabs_assets (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    asset_id text NOT NULL,
    indexed_asset_id text,
    asset_status text DEFAULT 'pending'::text NOT NULL,
    index_status text,
    error text,
    upload_raw_gcs_uri text,
    index_raw_gcs_uri text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    index_id text,
    media_asset_id uuid NOT NULL
);


ALTER TABLE conthunt.twelvelabs_assets OWNER TO conthunt_app;

--
-- Name: usage_limits; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.usage_limits (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    plan_role text NOT NULL,
    feature text NOT NULL,
    period text NOT NULL,
    limit_count integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT usage_limits_period_check CHECK ((period = ANY (ARRAY['hourly'::text, 'daily'::text, 'monthly'::text, 'yearly'::text, 'total'::text])))
);


ALTER TABLE conthunt.usage_limits OWNER TO conthunt_app;

--
-- Name: usage_logs; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.usage_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    feature text NOT NULL,
    quantity integer DEFAULT 1 NOT NULL,
    context jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE conthunt.usage_logs OWNER TO conthunt_app;

--
-- Name: user_analysis_access; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.user_analysis_access (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    media_asset_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE conthunt.user_analysis_access OWNER TO conthunt_app;

--
-- Name: user_onboarding_progress; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.user_onboarding_progress (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    flow_id character varying(50) NOT NULL,
    current_step integer DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'not_started'::character varying NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    restart_count integer DEFAULT 0 NOT NULL
);


ALTER TABLE conthunt.user_onboarding_progress OWNER TO conthunt_app;

--
-- Name: user_streak_days; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.user_streak_days (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    streak_type_id uuid NOT NULL,
    activity_date date NOT NULL,
    first_activity_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE conthunt.user_streak_days OWNER TO conthunt_app;

--
-- Name: user_streaks; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.user_streaks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    streak_type_id uuid NOT NULL,
    current_streak integer DEFAULT 0 NOT NULL,
    longest_streak integer DEFAULT 0 NOT NULL,
    last_activity_date date,
    last_action_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE conthunt.user_streaks OWNER TO conthunt_app;

--
-- Name: user_subscriptions; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.user_subscriptions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    subscription_id text NOT NULL,
    customer_id text,
    product_id text NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    cancel_at_period_end boolean DEFAULT false NOT NULL,
    current_period_start timestamp with time zone,
    current_period_end timestamp with time zone,
    last_webhook_ts timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE conthunt.user_subscriptions OWNER TO conthunt_app;

--
-- Name: users; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    firebase_uid text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    role text DEFAULT 'free'::text NOT NULL,
    current_period_start timestamp with time zone,
    dodo_customer_id text,
    credit_period_start timestamp with time zone,
    timezone text DEFAULT 'UTC'::text NOT NULL,
    whop_user_id character varying(255) DEFAULT NULL::character varying,
    CONSTRAINT users_role_check CHECK ((role = ANY (ARRAY['free'::text, 'creator'::text, 'pro_research'::text])))
);


ALTER TABLE conthunt.users OWNER TO conthunt_app;

--
-- Name: video_analyses; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.video_analyses (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    twelvelabs_asset_id uuid,
    prompt text NOT NULL,
    analysis_result jsonb NOT NULL,
    token_usage integer,
    raw_gcs_uri text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    status text DEFAULT 'processing'::text,
    error text,
    media_asset_id uuid NOT NULL
);


ALTER TABLE conthunt.video_analyses OWNER TO conthunt_app;

--
-- Name: waitlist; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.waitlist (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email text NOT NULL,
    ip_address text,
    user_agent text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE conthunt.waitlist OWNER TO conthunt_app;

--
-- Name: waitlist_requests; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.waitlist_requests (
    id bigint NOT NULL,
    ip_address text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE conthunt.waitlist_requests OWNER TO conthunt_app;

--
-- Name: waitlist_requests_id_seq; Type: SEQUENCE; Schema: conthunt; Owner: conthunt_app
--

CREATE SEQUENCE conthunt.waitlist_requests_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE conthunt.waitlist_requests_id_seq OWNER TO conthunt_app;

--
-- Name: waitlist_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: conthunt; Owner: conthunt_app
--

ALTER SEQUENCE conthunt.waitlist_requests_id_seq OWNED BY conthunt.waitlist_requests.id;


--
-- Name: webhook_events; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.webhook_events (
    webhook_id text NOT NULL,
    event_type text NOT NULL,
    subscription_id text,
    payload jsonb NOT NULL,
    processed_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE conthunt.webhook_events OWNER TO conthunt_app;

--
-- Name: write_outbox; Type: TABLE; Schema: conthunt; Owner: conthunt_app
--

CREATE TABLE conthunt.write_outbox (
    event_id uuid DEFAULT gen_random_uuid() NOT NULL,
    domain text NOT NULL,
    event_type text NOT NULL,
    ordering_mode text NOT NULL,
    partition_key text NOT NULL,
    idempotency_key text NOT NULL,
    actor_user_id uuid,
    actor_role text,
    source text,
    payload jsonb NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    attempt_count integer DEFAULT 0 NOT NULL,
    next_attempt_at timestamp with time zone DEFAULT now() NOT NULL,
    leased_by text,
    lease_until timestamp with time zone,
    last_error text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT write_outbox_ordering_mode_check CHECK ((ordering_mode = ANY (ARRAY['strict'::text, 'unordered'::text]))),
    CONSTRAINT write_outbox_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'processing'::text, 'done'::text, 'retry'::text, 'dead'::text])))
);


ALTER TABLE conthunt.write_outbox OWNER TO conthunt_app;

--
-- Name: waitlist_requests id; Type: DEFAULT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.waitlist_requests ALTER COLUMN id SET DEFAULT nextval('conthunt.waitlist_requests_id_seq'::regclass);


--
-- Name: board_insights board_insights_board_id_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.board_insights
    ADD CONSTRAINT board_insights_board_id_key UNIQUE (board_id);


--
-- Name: board_insights board_insights_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.board_insights
    ADD CONSTRAINT board_insights_pkey PRIMARY KEY (id);


--
-- Name: board_items board_items_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.board_items
    ADD CONSTRAINT board_items_pkey PRIMARY KEY (board_id, content_item_id);


--
-- Name: boards boards_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.boards
    ADD CONSTRAINT boards_pkey PRIMARY KEY (id);


--
-- Name: chat_tags chat_tags_chat_id_tag_type_tag_id_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.chat_tags
    ADD CONSTRAINT chat_tags_chat_id_tag_type_tag_id_key UNIQUE (chat_id, tag_type, tag_id);


--
-- Name: chat_tags chat_tags_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.chat_tags
    ADD CONSTRAINT chat_tags_pkey PRIMARY KEY (id);


--
-- Name: chats chats_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.chats
    ADD CONSTRAINT chats_pkey PRIMARY KEY (id);


--
-- Name: chats chats_thread_id_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.chats
    ADD CONSTRAINT chats_thread_id_key UNIQUE (thread_id);


--
-- Name: checkpoint_blobs checkpoint_blobs_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_service
--

ALTER TABLE ONLY conthunt.checkpoint_blobs
    ADD CONSTRAINT checkpoint_blobs_pkey PRIMARY KEY (thread_id, checkpoint_ns, channel, version);


--
-- Name: checkpoint_migrations checkpoint_migrations_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_service
--

ALTER TABLE ONLY conthunt.checkpoint_migrations
    ADD CONSTRAINT checkpoint_migrations_pkey PRIMARY KEY (v);


--
-- Name: checkpoint_writes checkpoint_writes_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_service
--

ALTER TABLE ONLY conthunt.checkpoint_writes
    ADD CONSTRAINT checkpoint_writes_pkey PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx);


--
-- Name: checkpoints checkpoints_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_service
--

ALTER TABLE ONLY conthunt.checkpoints
    ADD CONSTRAINT checkpoints_pkey PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id);


--
-- Name: content_items content_items_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.content_items
    ADD CONSTRAINT content_items_pkey PRIMARY KEY (id);


--
-- Name: content_items content_items_platform_external_id_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.content_items
    ADD CONSTRAINT content_items_platform_external_id_key UNIQUE (platform, external_id);


--
-- Name: feature_config feature_config_feature_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.feature_config
    ADD CONSTRAINT feature_config_feature_key UNIQUE (feature);


--
-- Name: feature_config feature_config_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.feature_config
    ADD CONSTRAINT feature_config_pkey PRIMARY KEY (id);


--
-- Name: media_assets media_assets_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.media_assets
    ADD CONSTRAINT media_assets_pkey PRIMARY KEY (id);


--
-- Name: pending_plan_changes pending_plan_changes_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.pending_plan_changes
    ADD CONSTRAINT pending_plan_changes_pkey PRIMARY KEY (id);


--
-- Name: platform_calls platform_calls_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.platform_calls
    ADD CONSTRAINT platform_calls_pkey PRIMARY KEY (id);


--
-- Name: processed_events processed_events_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.processed_events
    ADD CONSTRAINT processed_events_pkey PRIMARY KEY (handler_name, event_id);


--
-- Name: reward_balances reward_balances_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.reward_balances
    ADD CONSTRAINT reward_balances_pkey PRIMARY KEY (id);


--
-- Name: search_results search_results_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.search_results
    ADD CONSTRAINT search_results_pkey PRIMARY KEY (search_id, content_item_id);


--
-- Name: searches searches_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.searches
    ADD CONSTRAINT searches_pkey PRIMARY KEY (id);


--
-- Name: streak_milestones streak_milestones_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.streak_milestones
    ADD CONSTRAINT streak_milestones_pkey PRIMARY KEY (id);


--
-- Name: streak_milestones streak_milestones_role_streak_type_id_days_required_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.streak_milestones
    ADD CONSTRAINT streak_milestones_role_streak_type_id_days_required_key UNIQUE (role, streak_type_id, days_required);


--
-- Name: streak_reward_grants streak_reward_grants_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.streak_reward_grants
    ADD CONSTRAINT streak_reward_grants_pkey PRIMARY KEY (id);


--
-- Name: streak_reward_grants streak_reward_grants_user_id_streak_type_id_days_required_r_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.streak_reward_grants
    ADD CONSTRAINT streak_reward_grants_user_id_streak_type_id_days_required_r_key UNIQUE (user_id, streak_type_id, days_required, role);


--
-- Name: streak_types streak_types_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.streak_types
    ADD CONSTRAINT streak_types_pkey PRIMARY KEY (id);


--
-- Name: streak_types streak_types_slug_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.streak_types
    ADD CONSTRAINT streak_types_slug_key UNIQUE (slug);


--
-- Name: twelvelabs_assets twelvelabs_assets_media_asset_id_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.twelvelabs_assets
    ADD CONSTRAINT twelvelabs_assets_media_asset_id_key UNIQUE (media_asset_id);


--
-- Name: twelvelabs_assets twelvelabs_assets_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.twelvelabs_assets
    ADD CONSTRAINT twelvelabs_assets_pkey PRIMARY KEY (id);


--
-- Name: usage_limits usage_limits_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.usage_limits
    ADD CONSTRAINT usage_limits_pkey PRIMARY KEY (id);


--
-- Name: usage_limits usage_limits_plan_role_feature_period_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.usage_limits
    ADD CONSTRAINT usage_limits_plan_role_feature_period_key UNIQUE (plan_role, feature, period);


--
-- Name: usage_logs usage_logs_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.usage_logs
    ADD CONSTRAINT usage_logs_pkey PRIMARY KEY (id);


--
-- Name: user_analysis_access user_analysis_access_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_analysis_access
    ADD CONSTRAINT user_analysis_access_pkey PRIMARY KEY (id);


--
-- Name: user_analysis_access user_analysis_access_user_id_media_asset_id_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_analysis_access
    ADD CONSTRAINT user_analysis_access_user_id_media_asset_id_key UNIQUE (user_id, media_asset_id);


--
-- Name: user_onboarding_progress user_onboarding_progress_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_onboarding_progress
    ADD CONSTRAINT user_onboarding_progress_pkey PRIMARY KEY (id);


--
-- Name: user_onboarding_progress user_onboarding_progress_user_id_flow_id_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_onboarding_progress
    ADD CONSTRAINT user_onboarding_progress_user_id_flow_id_key UNIQUE (user_id, flow_id);


--
-- Name: user_streak_days user_streak_days_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_streak_days
    ADD CONSTRAINT user_streak_days_pkey PRIMARY KEY (id);


--
-- Name: user_streak_days user_streak_days_user_id_streak_type_id_activity_date_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_streak_days
    ADD CONSTRAINT user_streak_days_user_id_streak_type_id_activity_date_key UNIQUE (user_id, streak_type_id, activity_date);


--
-- Name: user_streaks user_streaks_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_streaks
    ADD CONSTRAINT user_streaks_pkey PRIMARY KEY (id);


--
-- Name: user_streaks user_streaks_user_id_streak_type_id_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_streaks
    ADD CONSTRAINT user_streaks_user_id_streak_type_id_key UNIQUE (user_id, streak_type_id);


--
-- Name: user_subscriptions user_subscriptions_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_subscriptions
    ADD CONSTRAINT user_subscriptions_pkey PRIMARY KEY (id);


--
-- Name: user_subscriptions user_subscriptions_subscription_id_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_subscriptions
    ADD CONSTRAINT user_subscriptions_subscription_id_key UNIQUE (subscription_id);


--
-- Name: user_subscriptions user_subscriptions_user_id_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_subscriptions
    ADD CONSTRAINT user_subscriptions_user_id_key UNIQUE (user_id);


--
-- Name: users users_firebase_uid_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.users
    ADD CONSTRAINT users_firebase_uid_key UNIQUE (firebase_uid);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_whop_user_id_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.users
    ADD CONSTRAINT users_whop_user_id_key UNIQUE (whop_user_id);


--
-- Name: video_analyses video_analyses_media_asset_id_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.video_analyses
    ADD CONSTRAINT video_analyses_media_asset_id_key UNIQUE (media_asset_id);


--
-- Name: video_analyses video_analyses_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.video_analyses
    ADD CONSTRAINT video_analyses_pkey PRIMARY KEY (id);


--
-- Name: waitlist waitlist_email_key; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.waitlist
    ADD CONSTRAINT waitlist_email_key UNIQUE (email);


--
-- Name: waitlist waitlist_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.waitlist
    ADD CONSTRAINT waitlist_pkey PRIMARY KEY (id);


--
-- Name: waitlist_requests waitlist_requests_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.waitlist_requests
    ADD CONSTRAINT waitlist_requests_pkey PRIMARY KEY (id);


--
-- Name: webhook_events webhook_events_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.webhook_events
    ADD CONSTRAINT webhook_events_pkey PRIMARY KEY (webhook_id);


--
-- Name: write_outbox write_outbox_domain_idempotency_unique; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.write_outbox
    ADD CONSTRAINT write_outbox_domain_idempotency_unique UNIQUE (domain, idempotency_key);


--
-- Name: write_outbox write_outbox_pkey; Type: CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.write_outbox
    ADD CONSTRAINT write_outbox_pkey PRIMARY KEY (event_id);


--
-- Name: checkpoint_blobs_thread_id_idx; Type: INDEX; Schema: conthunt; Owner: conthunt_service
--

CREATE INDEX checkpoint_blobs_thread_id_idx ON conthunt.checkpoint_blobs USING btree (thread_id);


--
-- Name: checkpoint_writes_thread_id_idx; Type: INDEX; Schema: conthunt; Owner: conthunt_service
--

CREATE INDEX checkpoint_writes_thread_id_idx ON conthunt.checkpoint_writes USING btree (thread_id);


--
-- Name: checkpoints_thread_id_idx; Type: INDEX; Schema: conthunt; Owner: conthunt_service
--

CREATE INDEX checkpoints_thread_id_idx ON conthunt.checkpoints USING btree (thread_id);


--
-- Name: idx_board_insights_board_status; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_board_insights_board_status ON conthunt.board_insights USING btree (board_id, status);


--
-- Name: idx_board_items_added; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_board_items_added ON conthunt.board_items USING btree (board_id, added_at DESC);


--
-- Name: idx_board_items_content; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_board_items_content ON conthunt.board_items USING btree (content_item_id);


--
-- Name: idx_boards_user; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_boards_user ON conthunt.boards USING btree (user_id);


--
-- Name: idx_boards_user_updated; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_boards_user_updated ON conthunt.boards USING btree (user_id, updated_at DESC);


--
-- Name: idx_chat_tags_chat_order; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_chat_tags_chat_order ON conthunt.chat_tags USING btree (chat_id, sort_order);


--
-- Name: idx_chat_tags_chat_type; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_chat_tags_chat_type ON conthunt.chat_tags USING btree (chat_id, tag_type);


--
-- Name: idx_chat_tags_not_deleted; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_chat_tags_not_deleted ON conthunt.chat_tags USING btree (chat_id) WHERE (deleted_at IS NULL);


--
-- Name: idx_chats_context_updated; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_chats_context_updated ON conthunt.chats USING btree (context_type, context_id, updated_at DESC);


--
-- Name: idx_chats_deep_research_enabled; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_chats_deep_research_enabled ON conthunt.chats USING btree (deep_research_enabled);


--
-- Name: idx_chats_user_updated; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_chats_user_updated ON conthunt.chats USING btree (user_id, updated_at DESC);


--
-- Name: idx_content_items_author_id; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_content_items_author_id ON conthunt.content_items USING btree (author_id) WHERE (author_id IS NOT NULL);


--
-- Name: idx_media_assets_content_asset_created; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_media_assets_content_asset_created ON conthunt.media_assets USING btree (content_item_id, asset_type, created_at DESC);


--
-- Name: idx_media_assets_content_item; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_media_assets_content_item ON conthunt.media_assets USING btree (content_item_id);


--
-- Name: idx_outbox_lease_expiry; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_outbox_lease_expiry ON conthunt.write_outbox USING btree (lease_until);


--
-- Name: idx_outbox_sched; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_outbox_sched ON conthunt.write_outbox USING btree (status, next_attempt_at, created_at);


--
-- Name: idx_outbox_strict_partition; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_outbox_strict_partition ON conthunt.write_outbox USING btree (partition_key, status, next_attempt_at, created_at) WHERE (ordering_mode = 'strict'::text);


--
-- Name: idx_pending_plan_changes_status; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_pending_plan_changes_status ON conthunt.pending_plan_changes USING btree (status) WHERE (status = 'pending'::text);


--
-- Name: idx_pending_plan_changes_subscription; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_pending_plan_changes_subscription ON conthunt.pending_plan_changes USING btree (subscription_id);


--
-- Name: idx_pending_plan_changes_user_id; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_pending_plan_changes_user_id ON conthunt.pending_plan_changes USING btree (user_id);


--
-- Name: idx_platform_calls_search_created; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_platform_calls_search_created ON conthunt.platform_calls USING btree (search_id, created_at);


--
-- Name: idx_platform_calls_search_platform_cursor_created; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_platform_calls_search_platform_cursor_created ON conthunt.platform_calls USING btree (search_id, platform, created_at DESC) WHERE (next_cursor IS NOT NULL);


--
-- Name: idx_processed_by_key; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_processed_by_key ON conthunt.processed_events USING btree (handler_name, idempotency_key);


--
-- Name: idx_search_results_content_item; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_search_results_content_item ON conthunt.search_results USING btree (content_item_id);


--
-- Name: idx_search_results_search_rank; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_search_results_search_rank ON conthunt.search_results USING btree (search_id, rank);


--
-- Name: idx_searches_inputs_gin; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_searches_inputs_gin ON conthunt.searches USING gin (inputs jsonb_path_ops);


--
-- Name: idx_searches_status; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_searches_status ON conthunt.searches USING btree (status);


--
-- Name: idx_searches_user_created; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_searches_user_created ON conthunt.searches USING btree (user_id, created_at DESC);


--
-- Name: idx_searches_user_hash; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_searches_user_hash ON conthunt.searches USING btree (user_id, search_hash);


--
-- Name: idx_streak_reward_grants_user_type; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_streak_reward_grants_user_type ON conthunt.streak_reward_grants USING btree (user_id, streak_type_id);


--
-- Name: idx_twelvelabs_assets_indexed_partial; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_twelvelabs_assets_indexed_partial ON conthunt.twelvelabs_assets USING btree (indexed_asset_id) WHERE (indexed_asset_id IS NOT NULL);


--
-- Name: idx_usage_logs_user_feature_date; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_usage_logs_user_feature_date ON conthunt.usage_logs USING btree (user_id, feature, created_at DESC);


--
-- Name: idx_user_subscriptions_status; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_user_subscriptions_status ON conthunt.user_subscriptions USING btree (status);


--
-- Name: idx_users_dodo_customer; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_users_dodo_customer ON conthunt.users USING btree (dodo_customer_id);


--
-- Name: idx_users_role; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_users_role ON conthunt.users USING btree (role);


--
-- Name: idx_video_analyses_status; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_video_analyses_status ON conthunt.video_analyses USING btree (media_asset_id, status);


--
-- Name: idx_waitlist_requests_ip_created; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_waitlist_requests_ip_created ON conthunt.waitlist_requests USING btree (ip_address, created_at DESC);


--
-- Name: idx_webhook_events_processed; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_webhook_events_processed ON conthunt.webhook_events USING btree (processed_at DESC);


--
-- Name: idx_webhook_events_subscription; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE INDEX idx_webhook_events_subscription ON conthunt.webhook_events USING btree (subscription_id);


--
-- Name: reward_balances_unique_credits; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE UNIQUE INDEX reward_balances_unique_credits ON conthunt.reward_balances USING btree (user_id) WHERE (reward_feature IS NULL);


--
-- Name: reward_balances_unique_feature; Type: INDEX; Schema: conthunt; Owner: conthunt_app
--

CREATE UNIQUE INDEX reward_balances_unique_feature ON conthunt.reward_balances USING btree (user_id, reward_feature) WHERE (reward_feature IS NOT NULL);


--
-- Name: board_insights board_insights_board_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.board_insights
    ADD CONSTRAINT board_insights_board_id_fkey FOREIGN KEY (board_id) REFERENCES conthunt.boards(id) ON DELETE CASCADE;


--
-- Name: board_items board_items_board_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.board_items
    ADD CONSTRAINT board_items_board_id_fkey FOREIGN KEY (board_id) REFERENCES conthunt.boards(id) ON DELETE CASCADE;


--
-- Name: board_items board_items_content_item_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.board_items
    ADD CONSTRAINT board_items_content_item_id_fkey FOREIGN KEY (content_item_id) REFERENCES conthunt.content_items(id) ON DELETE CASCADE;


--
-- Name: boards boards_user_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.boards
    ADD CONSTRAINT boards_user_id_fkey FOREIGN KEY (user_id) REFERENCES conthunt.users(id) ON DELETE CASCADE;


--
-- Name: chat_tags chat_tags_chat_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.chat_tags
    ADD CONSTRAINT chat_tags_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES conthunt.chats(id) ON DELETE CASCADE;


--
-- Name: chats chats_user_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.chats
    ADD CONSTRAINT chats_user_id_fkey FOREIGN KEY (user_id) REFERENCES conthunt.users(id) ON DELETE CASCADE;


--
-- Name: twelvelabs_assets fk_twelvelabs_assets_media_asset; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.twelvelabs_assets
    ADD CONSTRAINT fk_twelvelabs_assets_media_asset FOREIGN KEY (media_asset_id) REFERENCES conthunt.media_assets(id) ON DELETE CASCADE;


--
-- Name: video_analyses fk_video_analyses_media_asset; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.video_analyses
    ADD CONSTRAINT fk_video_analyses_media_asset FOREIGN KEY (media_asset_id) REFERENCES conthunt.media_assets(id) ON DELETE CASCADE;


--
-- Name: media_assets media_assets_content_item_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.media_assets
    ADD CONSTRAINT media_assets_content_item_id_fkey FOREIGN KEY (content_item_id) REFERENCES conthunt.content_items(id) ON DELETE CASCADE;


--
-- Name: pending_plan_changes pending_plan_changes_user_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.pending_plan_changes
    ADD CONSTRAINT pending_plan_changes_user_id_fkey FOREIGN KEY (user_id) REFERENCES conthunt.users(id) ON DELETE CASCADE;


--
-- Name: platform_calls platform_calls_search_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.platform_calls
    ADD CONSTRAINT platform_calls_search_id_fkey FOREIGN KEY (search_id) REFERENCES conthunt.searches(id) ON DELETE CASCADE;


--
-- Name: reward_balances reward_balances_user_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.reward_balances
    ADD CONSTRAINT reward_balances_user_id_fkey FOREIGN KEY (user_id) REFERENCES conthunt.users(id) ON DELETE CASCADE;


--
-- Name: search_results search_results_content_item_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.search_results
    ADD CONSTRAINT search_results_content_item_id_fkey FOREIGN KEY (content_item_id) REFERENCES conthunt.content_items(id) ON DELETE CASCADE;


--
-- Name: search_results search_results_search_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.search_results
    ADD CONSTRAINT search_results_search_id_fkey FOREIGN KEY (search_id) REFERENCES conthunt.searches(id) ON DELETE CASCADE;


--
-- Name: searches searches_user_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.searches
    ADD CONSTRAINT searches_user_id_fkey FOREIGN KEY (user_id) REFERENCES conthunt.users(id) ON DELETE CASCADE;


--
-- Name: streak_milestones streak_milestones_streak_type_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.streak_milestones
    ADD CONSTRAINT streak_milestones_streak_type_id_fkey FOREIGN KEY (streak_type_id) REFERENCES conthunt.streak_types(id) ON DELETE CASCADE;


--
-- Name: streak_reward_grants streak_reward_grants_streak_type_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.streak_reward_grants
    ADD CONSTRAINT streak_reward_grants_streak_type_id_fkey FOREIGN KEY (streak_type_id) REFERENCES conthunt.streak_types(id) ON DELETE CASCADE;


--
-- Name: streak_reward_grants streak_reward_grants_user_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.streak_reward_grants
    ADD CONSTRAINT streak_reward_grants_user_id_fkey FOREIGN KEY (user_id) REFERENCES conthunt.users(id) ON DELETE CASCADE;


--
-- Name: usage_logs usage_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.usage_logs
    ADD CONSTRAINT usage_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES conthunt.users(id) ON DELETE CASCADE;


--
-- Name: user_analysis_access user_analysis_access_user_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_analysis_access
    ADD CONSTRAINT user_analysis_access_user_id_fkey FOREIGN KEY (user_id) REFERENCES conthunt.users(id) ON DELETE CASCADE;


--
-- Name: user_onboarding_progress user_onboarding_progress_user_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_onboarding_progress
    ADD CONSTRAINT user_onboarding_progress_user_id_fkey FOREIGN KEY (user_id) REFERENCES conthunt.users(id) ON DELETE CASCADE;


--
-- Name: user_streak_days user_streak_days_streak_type_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_streak_days
    ADD CONSTRAINT user_streak_days_streak_type_id_fkey FOREIGN KEY (streak_type_id) REFERENCES conthunt.streak_types(id) ON DELETE CASCADE;


--
-- Name: user_streak_days user_streak_days_user_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_streak_days
    ADD CONSTRAINT user_streak_days_user_id_fkey FOREIGN KEY (user_id) REFERENCES conthunt.users(id) ON DELETE CASCADE;


--
-- Name: user_streaks user_streaks_streak_type_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_streaks
    ADD CONSTRAINT user_streaks_streak_type_id_fkey FOREIGN KEY (streak_type_id) REFERENCES conthunt.streak_types(id) ON DELETE CASCADE;


--
-- Name: user_streaks user_streaks_user_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_streaks
    ADD CONSTRAINT user_streaks_user_id_fkey FOREIGN KEY (user_id) REFERENCES conthunt.users(id) ON DELETE CASCADE;


--
-- Name: user_subscriptions user_subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.user_subscriptions
    ADD CONSTRAINT user_subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES conthunt.users(id) ON DELETE CASCADE;


--
-- Name: video_analyses video_analyses_twelvelabs_asset_id_fkey; Type: FK CONSTRAINT; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE ONLY conthunt.video_analyses
    ADD CONSTRAINT video_analyses_twelvelabs_asset_id_fkey FOREIGN KEY (twelvelabs_asset_id) REFERENCES conthunt.twelvelabs_assets(id) ON DELETE SET NULL;


--
-- Name: board_insights; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.board_insights ENABLE ROW LEVEL SECURITY;

--
-- Name: board_insights board_insights_delete_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY board_insights_delete_own ON conthunt.board_insights FOR DELETE TO conthunt_app USING ((board_id IN ( SELECT boards.id
   FROM conthunt.boards
  WHERE (boards.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: board_insights board_insights_delete_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY board_insights_delete_service ON conthunt.board_insights FOR DELETE TO conthunt_service USING ((board_id IN ( SELECT boards.id
   FROM conthunt.boards
  WHERE (boards.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: board_insights board_insights_insert_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY board_insights_insert_own ON conthunt.board_insights FOR INSERT TO conthunt_app WITH CHECK ((board_id IN ( SELECT boards.id
   FROM conthunt.boards
  WHERE (boards.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: board_insights board_insights_insert_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY board_insights_insert_service ON conthunt.board_insights FOR INSERT TO conthunt_service WITH CHECK ((board_id IN ( SELECT boards.id
   FROM conthunt.boards
  WHERE (boards.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: board_insights board_insights_select_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY board_insights_select_own ON conthunt.board_insights FOR SELECT TO conthunt_app USING ((board_id IN ( SELECT boards.id
   FROM conthunt.boards
  WHERE (boards.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: board_insights board_insights_select_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY board_insights_select_service ON conthunt.board_insights FOR SELECT TO conthunt_service USING ((board_id IN ( SELECT boards.id
   FROM conthunt.boards
  WHERE (boards.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: board_insights board_insights_update_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY board_insights_update_own ON conthunt.board_insights FOR UPDATE TO conthunt_app USING ((board_id IN ( SELECT boards.id
   FROM conthunt.boards
  WHERE (boards.user_id = (current_setting('app.user_id'::text, true))::uuid)))) WITH CHECK ((board_id IN ( SELECT boards.id
   FROM conthunt.boards
  WHERE (boards.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: board_insights board_insights_update_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY board_insights_update_service ON conthunt.board_insights FOR UPDATE TO conthunt_service USING ((board_id IN ( SELECT boards.id
   FROM conthunt.boards
  WHERE (boards.user_id = (current_setting('app.user_id'::text, true))::uuid)))) WITH CHECK ((board_id IN ( SELECT boards.id
   FROM conthunt.boards
  WHERE (boards.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: board_items; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.board_items ENABLE ROW LEVEL SECURITY;

--
-- Name: board_items board_items_delete_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY board_items_delete_service ON conthunt.board_items FOR DELETE TO conthunt_service USING ((board_id IN ( SELECT boards.id
   FROM conthunt.boards
  WHERE (boards.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: board_items board_items_insert_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY board_items_insert_service ON conthunt.board_items FOR INSERT TO conthunt_service WITH CHECK ((board_id IN ( SELECT boards.id
   FROM conthunt.boards
  WHERE (boards.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: board_items board_items_select_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY board_items_select_service ON conthunt.board_items FOR SELECT TO conthunt_service USING ((board_id IN ( SELECT boards.id
   FROM conthunt.boards
  WHERE (boards.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: boards; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.boards ENABLE ROW LEVEL SECURITY;

--
-- Name: boards boards_delete_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY boards_delete_service ON conthunt.boards FOR DELETE TO conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: boards boards_insert_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY boards_insert_service ON conthunt.boards FOR INSERT TO conthunt_service WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: boards boards_select_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY boards_select_service ON conthunt.boards FOR SELECT TO conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: boards boards_update_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY boards_update_service ON conthunt.boards FOR UPDATE TO conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: chats; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.chats ENABLE ROW LEVEL SECURITY;

--
-- Name: chats chats_delete_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY chats_delete_own ON conthunt.chats FOR DELETE TO conthunt_app USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: chats chats_delete_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY chats_delete_service ON conthunt.chats FOR DELETE TO conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: chats chats_insert_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY chats_insert_own ON conthunt.chats FOR INSERT TO conthunt_app WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: chats chats_insert_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY chats_insert_service ON conthunt.chats FOR INSERT TO conthunt_service WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: chats chats_select_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY chats_select_own ON conthunt.chats FOR SELECT TO conthunt_app USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: chats chats_select_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY chats_select_service ON conthunt.chats FOR SELECT TO conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: chats chats_update_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY chats_update_own ON conthunt.chats FOR UPDATE TO conthunt_app USING ((user_id = (current_setting('app.user_id'::text, true))::uuid)) WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: chats chats_update_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY chats_update_service ON conthunt.chats FOR UPDATE TO conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: feature_config config_select_all; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY config_select_all ON conthunt.feature_config FOR SELECT USING (true);


--
-- Name: content_items; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.content_items ENABLE ROW LEVEL SECURITY;

--
-- Name: content_items content_items_all_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY content_items_all_service ON conthunt.content_items TO conthunt_service USING (true) WITH CHECK (true);


--
-- Name: feature_config; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.feature_config ENABLE ROW LEVEL SECURITY;

--
-- Name: usage_limits limits_select_all; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY limits_select_all ON conthunt.usage_limits FOR SELECT TO conthunt_app USING (true);


--
-- Name: usage_limits limits_select_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY limits_select_service ON conthunt.usage_limits FOR SELECT TO conthunt_service USING (true);


--
-- Name: media_assets; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.media_assets ENABLE ROW LEVEL SECURITY;

--
-- Name: media_assets media_assets_all_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY media_assets_all_service ON conthunt.media_assets TO conthunt_service USING (true) WITH CHECK (true);


--
-- Name: user_onboarding_progress onboarding_insert_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY onboarding_insert_own ON conthunt.user_onboarding_progress FOR INSERT TO conthunt_app, conthunt_service WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: user_onboarding_progress onboarding_select_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY onboarding_select_own ON conthunt.user_onboarding_progress FOR SELECT TO conthunt_app, conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: user_onboarding_progress onboarding_update_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY onboarding_update_own ON conthunt.user_onboarding_progress FOR UPDATE TO conthunt_app, conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid)) WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: pending_plan_changes pending_changes_select_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY pending_changes_select_own ON conthunt.pending_plan_changes FOR SELECT TO conthunt_app USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: pending_plan_changes pending_changes_service_all; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY pending_changes_service_all ON conthunt.pending_plan_changes TO conthunt_service USING (true) WITH CHECK (true);


--
-- Name: pending_plan_changes; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.pending_plan_changes ENABLE ROW LEVEL SECURITY;

--
-- Name: platform_calls; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.platform_calls ENABLE ROW LEVEL SECURITY;

--
-- Name: platform_calls platform_calls_delete_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY platform_calls_delete_service ON conthunt.platform_calls FOR DELETE TO conthunt_service USING ((search_id IN ( SELECT searches.id
   FROM conthunt.searches
  WHERE (searches.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: platform_calls platform_calls_insert_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY platform_calls_insert_service ON conthunt.platform_calls FOR INSERT TO conthunt_service WITH CHECK ((search_id IN ( SELECT searches.id
   FROM conthunt.searches
  WHERE (searches.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: platform_calls platform_calls_select_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY platform_calls_select_service ON conthunt.platform_calls FOR SELECT TO conthunt_service USING ((search_id IN ( SELECT searches.id
   FROM conthunt.searches
  WHERE (searches.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: platform_calls platform_calls_update_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY platform_calls_update_service ON conthunt.platform_calls FOR UPDATE TO conthunt_service USING ((search_id IN ( SELECT searches.id
   FROM conthunt.searches
  WHERE (searches.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: reward_balances; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.reward_balances ENABLE ROW LEVEL SECURITY;

--
-- Name: reward_balances reward_balances_insert_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY reward_balances_insert_own ON conthunt.reward_balances FOR INSERT TO conthunt_app, conthunt_service WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: reward_balances reward_balances_select_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY reward_balances_select_own ON conthunt.reward_balances FOR SELECT TO conthunt_app, conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: reward_balances reward_balances_update_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY reward_balances_update_own ON conthunt.reward_balances FOR UPDATE TO conthunt_app, conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid)) WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: search_results; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.search_results ENABLE ROW LEVEL SECURITY;

--
-- Name: search_results search_results_delete_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY search_results_delete_service ON conthunt.search_results FOR DELETE TO conthunt_service USING ((search_id IN ( SELECT searches.id
   FROM conthunt.searches
  WHERE (searches.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: search_results search_results_insert_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY search_results_insert_service ON conthunt.search_results FOR INSERT TO conthunt_service WITH CHECK ((search_id IN ( SELECT searches.id
   FROM conthunt.searches
  WHERE (searches.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: search_results search_results_select_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY search_results_select_service ON conthunt.search_results FOR SELECT TO conthunt_service USING ((search_id IN ( SELECT searches.id
   FROM conthunt.searches
  WHERE (searches.user_id = (current_setting('app.user_id'::text, true))::uuid))));


--
-- Name: searches; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.searches ENABLE ROW LEVEL SECURITY;

--
-- Name: searches searches_delete_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY searches_delete_service ON conthunt.searches FOR DELETE TO conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: searches searches_insert_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY searches_insert_service ON conthunt.searches FOR INSERT TO conthunt_service WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: searches searches_select_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY searches_select_service ON conthunt.searches FOR SELECT TO conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: searches searches_update_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY searches_update_service ON conthunt.searches FOR UPDATE TO conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: streak_milestones; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.streak_milestones ENABLE ROW LEVEL SECURITY;

--
-- Name: streak_milestones streak_milestones_select_all; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY streak_milestones_select_all ON conthunt.streak_milestones FOR SELECT TO conthunt_app, conthunt_service USING (true);


--
-- Name: streak_reward_grants; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.streak_reward_grants ENABLE ROW LEVEL SECURITY;

--
-- Name: streak_reward_grants streak_reward_grants_insert_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY streak_reward_grants_insert_own ON conthunt.streak_reward_grants FOR INSERT TO conthunt_app, conthunt_service WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: streak_reward_grants streak_reward_grants_select_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY streak_reward_grants_select_own ON conthunt.streak_reward_grants FOR SELECT TO conthunt_app, conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: streak_types; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.streak_types ENABLE ROW LEVEL SECURITY;

--
-- Name: streak_types streak_types_select_all; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY streak_types_select_all ON conthunt.streak_types FOR SELECT TO conthunt_app, conthunt_service USING (true);


--
-- Name: user_subscriptions subscriptions_select_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY subscriptions_select_own ON conthunt.user_subscriptions FOR SELECT TO conthunt_app USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: user_subscriptions subscriptions_service_all; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY subscriptions_service_all ON conthunt.user_subscriptions TO conthunt_service USING (true) WITH CHECK (true);


--
-- Name: twelvelabs_assets; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.twelvelabs_assets ENABLE ROW LEVEL SECURITY;

--
-- Name: twelvelabs_assets twelvelabs_assets_all_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY twelvelabs_assets_all_service ON conthunt.twelvelabs_assets TO conthunt_service USING (true) WITH CHECK (true);


--
-- Name: usage_logs usage_delete_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY usage_delete_service ON conthunt.usage_logs FOR DELETE TO conthunt_service USING (true);


--
-- Name: usage_logs usage_insert_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY usage_insert_own ON conthunt.usage_logs FOR INSERT TO conthunt_app WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: usage_logs usage_insert_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY usage_insert_service ON conthunt.usage_logs FOR INSERT TO conthunt_service WITH CHECK (true);


--
-- Name: usage_limits; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.usage_limits ENABLE ROW LEVEL SECURITY;

--
-- Name: usage_logs; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.usage_logs ENABLE ROW LEVEL SECURITY;

--
-- Name: usage_logs usage_select_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY usage_select_own ON conthunt.usage_logs FOR SELECT TO conthunt_app USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: usage_logs usage_select_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY usage_select_service ON conthunt.usage_logs FOR SELECT TO conthunt_service USING (true);


--
-- Name: usage_logs usage_update_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY usage_update_service ON conthunt.usage_logs FOR UPDATE TO conthunt_service USING (true);


--
-- Name: user_analysis_access; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.user_analysis_access ENABLE ROW LEVEL SECURITY;

--
-- Name: user_analysis_access user_analysis_access_insert_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY user_analysis_access_insert_own ON conthunt.user_analysis_access FOR INSERT TO conthunt_app WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: user_analysis_access user_analysis_access_select_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY user_analysis_access_select_own ON conthunt.user_analysis_access FOR SELECT TO conthunt_app USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: user_analysis_access user_analysis_access_service_insert; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY user_analysis_access_service_insert ON conthunt.user_analysis_access FOR INSERT TO conthunt_service WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: user_analysis_access user_analysis_access_service_select; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY user_analysis_access_service_select ON conthunt.user_analysis_access FOR SELECT TO conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: user_onboarding_progress; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.user_onboarding_progress ENABLE ROW LEVEL SECURITY;

--
-- Name: user_streak_days; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.user_streak_days ENABLE ROW LEVEL SECURITY;

--
-- Name: user_streak_days user_streak_days_insert_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY user_streak_days_insert_own ON conthunt.user_streak_days FOR INSERT TO conthunt_app, conthunt_service WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: user_streak_days user_streak_days_select_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY user_streak_days_select_own ON conthunt.user_streak_days FOR SELECT TO conthunt_app, conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: user_streaks; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.user_streaks ENABLE ROW LEVEL SECURITY;

--
-- Name: user_streaks user_streaks_insert_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY user_streaks_insert_own ON conthunt.user_streaks FOR INSERT TO conthunt_app, conthunt_service WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: user_streaks user_streaks_select_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY user_streaks_select_own ON conthunt.user_streaks FOR SELECT TO conthunt_app, conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: user_streaks user_streaks_update_own; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY user_streaks_update_own ON conthunt.user_streaks FOR UPDATE TO conthunt_app, conthunt_service USING ((user_id = (current_setting('app.user_id'::text, true))::uuid)) WITH CHECK ((user_id = (current_setting('app.user_id'::text, true))::uuid));


--
-- Name: user_subscriptions; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.user_subscriptions ENABLE ROW LEVEL SECURITY;

--
-- Name: users; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.users ENABLE ROW LEVEL SECURITY;

--
-- Name: users users_all_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY users_all_service ON conthunt.users TO conthunt_service USING (true) WITH CHECK (true);


--
-- Name: video_analyses; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.video_analyses ENABLE ROW LEVEL SECURITY;

--
-- Name: video_analyses video_analyses_all_service; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY video_analyses_all_service ON conthunt.video_analyses TO conthunt_service USING (true) WITH CHECK (true);


--
-- Name: webhook_events; Type: ROW SECURITY; Schema: conthunt; Owner: conthunt_app
--

ALTER TABLE conthunt.webhook_events ENABLE ROW LEVEL SECURITY;

--
-- Name: webhook_events webhook_events_service_all; Type: POLICY; Schema: conthunt; Owner: conthunt_app
--

CREATE POLICY webhook_events_service_all ON conthunt.webhook_events TO conthunt_service USING (true) WITH CHECK (true);


--
-- Name: SCHEMA conthunt; Type: ACL; Schema: -; Owner: conthunt_app
--

GRANT ALL ON SCHEMA conthunt TO conthunt_service;


--
-- Name: TABLE board_insights; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.board_insights TO conthunt_service;


--
-- Name: TABLE board_items; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.board_items TO conthunt_service;


--
-- Name: TABLE boards; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.boards TO conthunt_service;


--
-- Name: TABLE chat_tags; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.chat_tags TO conthunt_service;


--
-- Name: TABLE chats; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.chats TO conthunt_service;


--
-- Name: TABLE checkpoint_blobs; Type: ACL; Schema: conthunt; Owner: conthunt_service
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.checkpoint_blobs TO conthunt_app;


--
-- Name: TABLE checkpoint_migrations; Type: ACL; Schema: conthunt; Owner: conthunt_service
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.checkpoint_migrations TO conthunt_app;


--
-- Name: TABLE checkpoint_writes; Type: ACL; Schema: conthunt; Owner: conthunt_service
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.checkpoint_writes TO conthunt_app;


--
-- Name: TABLE checkpoints; Type: ACL; Schema: conthunt; Owner: conthunt_service
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.checkpoints TO conthunt_app;


--
-- Name: TABLE content_items; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.content_items TO conthunt_service;


--
-- Name: TABLE feature_config; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT ALL ON TABLE conthunt.feature_config TO conthunt_service;


--
-- Name: TABLE media_assets; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.media_assets TO conthunt_service;


--
-- Name: TABLE pending_plan_changes; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT ALL ON TABLE conthunt.pending_plan_changes TO conthunt_service;


--
-- Name: TABLE platform_calls; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.platform_calls TO conthunt_service;


--
-- Name: TABLE processed_events; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.processed_events TO conthunt_service;


--
-- Name: TABLE reward_balances; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT ALL ON TABLE conthunt.reward_balances TO conthunt_service;


--
-- Name: TABLE search_results; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.search_results TO conthunt_service;


--
-- Name: TABLE searches; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.searches TO conthunt_service;


--
-- Name: TABLE streak_milestones; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT ALL ON TABLE conthunt.streak_milestones TO conthunt_service;


--
-- Name: TABLE streak_reward_grants; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT ALL ON TABLE conthunt.streak_reward_grants TO conthunt_service;


--
-- Name: TABLE streak_types; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT ALL ON TABLE conthunt.streak_types TO conthunt_service;


--
-- Name: TABLE twelvelabs_assets; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.twelvelabs_assets TO conthunt_service;


--
-- Name: TABLE usage_limits; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT ALL ON TABLE conthunt.usage_limits TO conthunt_service;


--
-- Name: TABLE usage_logs; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT ALL ON TABLE conthunt.usage_logs TO conthunt_service;


--
-- Name: TABLE user_analysis_access; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT ALL ON TABLE conthunt.user_analysis_access TO conthunt_service;


--
-- Name: TABLE user_onboarding_progress; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT ALL ON TABLE conthunt.user_onboarding_progress TO conthunt_service;


--
-- Name: TABLE user_streak_days; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT ALL ON TABLE conthunt.user_streak_days TO conthunt_service;


--
-- Name: TABLE user_streaks; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT ALL ON TABLE conthunt.user_streaks TO conthunt_service;


--
-- Name: TABLE user_subscriptions; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT ALL ON TABLE conthunt.user_subscriptions TO conthunt_service;


--
-- Name: TABLE users; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.users TO conthunt_service;


--
-- Name: TABLE video_analyses; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.video_analyses TO conthunt_service;


--
-- Name: TABLE waitlist; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.waitlist TO conthunt_service;


--
-- Name: TABLE waitlist_requests; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.waitlist_requests TO conthunt_service;


--
-- Name: SEQUENCE waitlist_requests_id_seq; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,USAGE ON SEQUENCE conthunt.waitlist_requests_id_seq TO conthunt_service;


--
-- Name: TABLE webhook_events; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT ALL ON TABLE conthunt.webhook_events TO conthunt_service;


--
-- Name: TABLE write_outbox; Type: ACL; Schema: conthunt; Owner: conthunt_app
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE conthunt.write_outbox TO conthunt_service;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: conthunt; Owner: conthunt_app
--

ALTER DEFAULT PRIVILEGES FOR ROLE conthunt_app IN SCHEMA conthunt GRANT SELECT,USAGE ON SEQUENCES TO conthunt_app;
ALTER DEFAULT PRIVILEGES FOR ROLE conthunt_app IN SCHEMA conthunt GRANT SELECT,USAGE ON SEQUENCES TO conthunt_service;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: conthunt; Owner: conthunt_service
--

ALTER DEFAULT PRIVILEGES FOR ROLE conthunt_service IN SCHEMA conthunt GRANT ALL ON FUNCTIONS TO conthunt_app;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: conthunt; Owner: conthunt_app
--

ALTER DEFAULT PRIVILEGES FOR ROLE conthunt_app IN SCHEMA conthunt GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO conthunt_app;
ALTER DEFAULT PRIVILEGES FOR ROLE conthunt_app IN SCHEMA conthunt GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO conthunt_service;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: conthunt; Owner: conthunt_service
--

ALTER DEFAULT PRIVILEGES FOR ROLE conthunt_service IN SCHEMA conthunt GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO conthunt_app;


--
-- PostgreSQL database dump complete
--

\unrestrict cANvuASzRvSKyjs5925ooAluC2phZnZtkfnOFLfirGWlBaWsuM5lJ1A0gnZVqMe

