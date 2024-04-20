REVOKE ALL ON SCHEMA public FROM PUBLIC;

CREATE ROLE dl_viewer WITH
	NOLOGIN
	NOSUPERUSER
	NOCREATEDB
	NOCREATEROLE
	INHERIT
	NOREPLICATION
	CONNECTION LIMIT -1;

CREATE ROLE dl_frontend WITH
	LOGIN
	NOSUPERUSER
	NOCREATEDB
	NOCREATEROLE
	INHERIT
	NOREPLICATION
	CONNECTION LIMIT -1
	PASSWORD 'xxx';

GRANT dl_viewer TO dl_frontend;

CREATE ROLE dl_creator WITH
	NOLOGIN
	NOSUPERUSER
	NOCREATEDB
	NOCREATEROLE
	INHERIT
	NOREPLICATION
	CONNECTION LIMIT -1;

CREATE ROLE dl_backend WITH
	LOGIN
	NOSUPERUSER
	NOCREATEDB
	NOCREATEROLE
	INHERIT
	NOREPLICATION
	CONNECTION LIMIT -1
	PASSWORD 'xxx';

GRANT dl_creator TO dl_backend;

-- CREATE NEW DATABASE
CREATE DATABASE dl
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

-- ====================
-- SWITCH TO NEW DATABASE HERE
-- ====================

CREATE SCHEMA dl AUTHORIZATION postgres;

GRANT USAGE ON SCHEMA dl TO dl_creator;
GRANT USAGE ON SCHEMA dl TO dl_viewer;
GRANT ALL ON SCHEMA dl TO postgres;

ALTER DEFAULT PRIVILEGES IN SCHEMA dl GRANT SELECT ON TABLES TO dl_viewer;
ALTER DEFAULT PRIVILEGES IN SCHEMA dl GRANT SELECT ON SEQUENCES TO dl_viewer;

ALTER DEFAULT PRIVILEGES IN SCHEMA dl
GRANT INSERT, SELECT, DELETE, UPDATE ON TABLES TO dl_creator;
ALTER DEFAULT PRIVILEGES IN SCHEMA dl
GRANT SELECT, UPDATE ON SEQUENCES TO dl_creator;

-- Table: public.dl_status

CREATE TABLE IF NOT EXISTS dl.dl_status
(
    value character varying(32) NOT NULL,
    CONSTRAINT dl_status_pkey PRIMARY KEY (value)
);

-- Table: public.dl_platform
CREATE TABLE IF NOT EXISTS dl.dl_platform
(
    value character varying(32) NOT NULL,
    CONSTRAINT dl_platform_pkey PRIMARY KEY (value)
);

-- Table: public.dl_request
CREATE TABLE IF NOT EXISTS dl.dl_request
(
    id SERIAL NOT NULL,
    status character varying(32) NOT NULL,
    platform character varying(32) NOT NULL,
    video_page_or_manifest_url character varying(1024) NOT NULL,
    created timestamp with time zone NOT NULL,
    updated timestamp with time zone NOT NULL,
    output_filename character varying(128),
    preferred_quality_matcher character varying(128),
    CONSTRAINT dl_request_pkey PRIMARY KEY (id),
    CONSTRAINT f_platform FOREIGN KEY (platform)
        REFERENCES dl.dl_platform (value) MATCH FULL
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT f_status FOREIGN KEY (status)
        REFERENCES dl.dl_status (value) MATCH FULL
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);


-- INSERT DEFAULT VALUES

INSERT INTO dl.dl_platform (value) VALUES
('VRTMAX'),('VTMGO'),('GOPLAY'),('STREAMZ'),('UNKNOWN');

INSERT INTO dl.dl_status (value) VALUES
('PENDING'),('IN_PROGRESS'),('COMPLETED'),('FAILED');
