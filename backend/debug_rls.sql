BEGIN;
  ALTER TABLE conthunt.chats DISABLE ROW LEVEL SECURITY;
  
  -- Run your query here:
  SELECT thread_id FROM conthunt.chats WHERE id = 'cd94449e-07d7-43cb-aad1-ecb556e2ce03';

  ALTER TABLE conthunt.chats ENABLE ROW LEVEL SECURITY;
COMMIT;
