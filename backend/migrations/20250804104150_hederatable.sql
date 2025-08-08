CREATE TYPE status AS ENUM ('draft', 'submitted', 'rejected', 'on_blockchain');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    country TEXT,
    wallet_address TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE patent_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    raw_idea TEXT NOT NULL,
    status status NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);