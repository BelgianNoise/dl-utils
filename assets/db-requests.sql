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

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO dl_viewer;
GRANT USAGE ON SCHEMA public TO dl_creator;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
GRANT SELECT ON TABLES TO dl_viewer;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
GRANT INSERT, SELECT, DELETE, UPDATE ON TABLES TO dl_creator;


-- Table: public.dl_status

-- DROP TABLE IF EXISTS public.dl_status;

CREATE TABLE IF NOT EXISTS public.dl_status
(
    value character varying(32) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT dl_status_pkey PRIMARY KEY (value)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.dl_status
    OWNER to postgres;

-- Table: public.dl_platform

-- DROP TABLE IF EXISTS public.dl_platform;

CREATE TABLE IF NOT EXISTS public.dl_platform
(
    value character varying(32) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT dl_platform_pkey PRIMARY KEY (value)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.dl_platform
    OWNER to postgres;

-- Table: public.dl_request

-- DROP TABLE IF EXISTS public.dl_request;

CREATE TABLE IF NOT EXISTS public.dl_request
(
    id SERIAL NOT NULL,
    status character varying(32) COLLATE pg_catalog."default" NOT NULL,
    platform character varying(32) COLLATE pg_catalog."default" NOT NULL,
    video_page_url character varying(1024) COLLATE pg_catalog."default" NOT NULL,
    created timestamp with time zone NOT NULL,
    updated timestamp with time zone NOT NULL,
    mpd_or_m3u8_url character varying(1024) COLLATE pg_catalog."default" NOT NULL,
    output_filename character varying(128) COLLATE pg_catalog."default" NOT NULL,
    preferred_quality_matcher character varying(128) COLLATE pg_catalog."default",
    drm_token character varying(2048) COLLATE pg_catalog."default",
    CONSTRAINT dl_request_pkey PRIMARY KEY (id),
    CONSTRAINT f_platform FOREIGN KEY (platform)
        REFERENCES public.dl_platform (value) MATCH FULL
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT f_status FOREIGN KEY (status)
        REFERENCES public.dl_status (value) MATCH FULL
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.dl_request
    OWNER to postgres;


CREATE TABLE public.dl_request_manifest_content
(
    id serial NOT NULL,
    dl_request_id integer NOT NULL,
    content text NOT NULL,
    PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
);

ALTER TABLE IF EXISTS public.dl_request_manifest_content
    OWNER to postgres;

GRANT INSERT, SELECT, UPDATE, DELETE ON TABLE public.dl_request_manifest_content TO dl_creator;
GRANT SELECT ON TABLE public.dl_request_manifest_content TO dl_viewer;
GRANT ALL ON TABLE public.dl_request_manifest_content TO postgres;


-- NOTES

GRANT INSERT, SELECT, UPDATE, DELETE ON SCHEMA public TO dl_creator;
GRANT SELECT ON SCHEMA public TO dl_viewer;
GRANT ALL ON SCHEMA public TO postgres;
REVOKE ALL ON SCHEMA public FROM creator;
REVOKE ALL ON SCHEMA public FROM viewer;