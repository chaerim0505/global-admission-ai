PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS programs (
    programId TEXT PRIMARY KEY,

    universityName TEXT NOT NULL,
    country TEXT NOT NULL
        CHECK (country IN ('KR', 'US', 'GB', 'NL', 'IE')),

    programName TEXT NOT NULL,
    degreeLevel TEXT NOT NULL
        CHECK (degreeLevel IN ('undergraduate', 'master', 'phd')),

    engineeringFields TEXT NOT NULL
        CHECK (json_valid(engineeringFields)),
    topics TEXT NOT NULL
        CHECK (json_valid(topics)),

    intake TEXT,
    academicRequirementText TEXT,
    minimumGpa REAL
        CHECK (minimumGpa IS NULL OR minimumGpa >= 0),
    applicationDeadline TEXT,

    tuition TEXT
        CHECK (tuition IS NULL OR json_valid(tuition)),
    scholarships TEXT
        CHECK (scholarships IS NULL OR json_valid(scholarships)),

    sourceUrl TEXT NOT NULL
        CHECK (length(trim(sourceUrl)) > 0),
    checkedAt TEXT NOT NULL
        CHECK (length(trim(checkedAt)) > 0),

    verificationStatus TEXT NOT NULL DEFAULT 'needs_check'
        CHECK (verificationStatus IN ('needs_check', 'verified'))
);

CREATE INDEX IF NOT EXISTS idx_program_country_degree
ON programs (country, degreeLevel);