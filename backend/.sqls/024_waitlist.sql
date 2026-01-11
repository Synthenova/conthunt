SET search_path = conthunt, public;

CREATE TABLE conthunt.waitlist (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email       text NOT NULL UNIQUE,
  ip_address  text,
  user_agent  text,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE conthunt.waitlist_requests (
  id          bigserial PRIMARY KEY,
  ip_address  text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_waitlist_requests_ip_created
  ON conthunt.waitlist_requests (ip_address, created_at DESC);

GRANT SELECT, INSERT ON conthunt.waitlist TO conthunt_app;
GRANT SELECT, INSERT ON conthunt.waitlist_requests TO conthunt_app;
