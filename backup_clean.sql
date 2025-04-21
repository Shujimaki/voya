--
-- PostgreSQL database dump
--

-- Dumped from database version 16.8 (Debian 16.8-1.pgdg120+1)
-- Dumped by pg_dump version 17.4

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
-- Name: public; Type: SCHEMA; Schema: -; Owner: voya_q77i_user
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO voya_q77i_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: route_steps; Type: TABLE; Schema: public; Owner: voya_q77i_user
--

CREATE TABLE public.route_steps (
    id integer NOT NULL,
    stop_id integer NOT NULL,
    step_order integer NOT NULL,
    step_text text NOT NULL
);


ALTER TABLE public.route_steps OWNER TO voya_q77i_user;

--
-- Name: route_steps_id_seq; Type: SEQUENCE; Schema: public; Owner: voya_q77i_user
--

CREATE SEQUENCE public.route_steps_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.route_steps_id_seq OWNER TO voya_q77i_user;

--
-- Name: route_steps_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: voya_q77i_user
--

ALTER SEQUENCE public.route_steps_id_seq OWNED BY public.route_steps.id;


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: voya_q77i_user
--

CREATE TABLE public.sessions (
    id integer NOT NULL,
    session_id character varying(255),
    data bytea,
    expiry timestamp without time zone
);


ALTER TABLE public.sessions OWNER TO voya_q77i_user;

--
-- Name: sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: voya_q77i_user
--

CREATE SEQUENCE public.sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sessions_id_seq OWNER TO voya_q77i_user;

--
-- Name: sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: voya_q77i_user
--

ALTER SEQUENCE public.sessions_id_seq OWNED BY public.sessions.id;


--
-- Name: stops; Type: TABLE; Schema: public; Owner: voya_q77i_user
--

CREATE TABLE public.stops (
    id integer NOT NULL,
    trip_id integer NOT NULL,
    user_id integer NOT NULL,
    action character varying(120) NOT NULL,
    "time" character varying(10) NOT NULL,
    date character varying(10) NOT NULL,
    destination character varying(120) NOT NULL,
    route text NOT NULL
);


ALTER TABLE public.stops OWNER TO voya_q77i_user;

--
-- Name: stops_id_seq; Type: SEQUENCE; Schema: public; Owner: voya_q77i_user
--

CREATE SEQUENCE public.stops_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.stops_id_seq OWNER TO voya_q77i_user;

--
-- Name: stops_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: voya_q77i_user
--

ALTER SEQUENCE public.stops_id_seq OWNED BY public.stops.id;


--
-- Name: trips; Type: TABLE; Schema: public; Owner: voya_q77i_user
--

CREATE TABLE public.trips (
    id integer NOT NULL,
    user_id integer NOT NULL,
    destination character varying(120) NOT NULL,
    arrival_date character varying(10) NOT NULL,
    departure_date character varying(10) NOT NULL
);


ALTER TABLE public.trips OWNER TO voya_q77i_user;

--
-- Name: trips_id_seq; Type: SEQUENCE; Schema: public; Owner: voya_q77i_user
--

CREATE SEQUENCE public.trips_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.trips_id_seq OWNER TO voya_q77i_user;

--
-- Name: trips_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: voya_q77i_user
--

ALTER SEQUENCE public.trips_id_seq OWNED BY public.trips.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: voya_q77i_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(80),
    email character varying(120) NOT NULL,
    password bytea,
    email_verified boolean,
    verification_token character varying(128),
    token_expiry timestamp without time zone
);


ALTER TABLE public.users OWNER TO voya_q77i_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: voya_q77i_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO voya_q77i_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: voya_q77i_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: route_steps id; Type: DEFAULT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.route_steps ALTER COLUMN id SET DEFAULT nextval('public.route_steps_id_seq'::regclass);


--
-- Name: sessions id; Type: DEFAULT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.sessions ALTER COLUMN id SET DEFAULT nextval('public.sessions_id_seq'::regclass);


--
-- Name: stops id; Type: DEFAULT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.stops ALTER COLUMN id SET DEFAULT nextval('public.stops_id_seq'::regclass);


--
-- Name: trips id; Type: DEFAULT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.trips ALTER COLUMN id SET DEFAULT nextval('public.trips_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: route_steps; Type: TABLE DATA; Schema: public; Owner: voya_q77i_user
--

COPY public.route_steps (id, stop_id, step_order, step_text) FROM stdin;
\.


--
-- Data for Name: sessions; Type: TABLE DATA; Schema: public; Owner: voya_q77i_user
--

COPY public.sessions (id, session_id, data, expiry) FROM stdin;
\.


--
-- Data for Name: stops; Type: TABLE DATA; Schema: public; Owner: voya_q77i_user
--

COPY public.stops (id, trip_id, user_id, action, "time", date, destination, route) FROM stdin;
\.


--
-- Data for Name: trips; Type: TABLE DATA; Schema: public; Owner: voya_q77i_user
--

COPY public.trips (id, user_id, destination, arrival_date, departure_date) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: voya_q77i_user
--

COPY public.users (id, username, email, password, email_verified, verification_token, token_expiry) FROM stdin;
\.


--
-- Name: route_steps_id_seq; Type: SEQUENCE SET; Schema: public; Owner: voya_q77i_user
--

SELECT pg_catalog.setval('public.route_steps_id_seq', 1, false);


--
-- Name: sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: voya_q77i_user
--

SELECT pg_catalog.setval('public.sessions_id_seq', 1, false);


--
-- Name: stops_id_seq; Type: SEQUENCE SET; Schema: public; Owner: voya_q77i_user
--

SELECT pg_catalog.setval('public.stops_id_seq', 1, false);


--
-- Name: trips_id_seq; Type: SEQUENCE SET; Schema: public; Owner: voya_q77i_user
--

SELECT pg_catalog.setval('public.trips_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: voya_q77i_user
--

SELECT pg_catalog.setval('public.users_id_seq', 1, false);


--
-- Name: route_steps route_steps_pkey; Type: CONSTRAINT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.route_steps
    ADD CONSTRAINT route_steps_pkey PRIMARY KEY (id);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: sessions sessions_session_id_key; Type: CONSTRAINT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_session_id_key UNIQUE (session_id);


--
-- Name: stops stops_pkey; Type: CONSTRAINT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.stops
    ADD CONSTRAINT stops_pkey PRIMARY KEY (id);


--
-- Name: trips trips_pkey; Type: CONSTRAINT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT trips_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: route_steps route_steps_stop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.route_steps
    ADD CONSTRAINT route_steps_stop_id_fkey FOREIGN KEY (stop_id) REFERENCES public.stops(id);


--
-- Name: stops stops_trip_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.stops
    ADD CONSTRAINT stops_trip_id_fkey FOREIGN KEY (trip_id) REFERENCES public.trips(id);


--
-- Name: stops stops_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.stops
    ADD CONSTRAINT stops_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: trips trips_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: voya_q77i_user
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT trips_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON SEQUENCES TO voya_q77i_user;


--
-- Name: DEFAULT PRIVILEGES FOR TYPES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TYPES TO voya_q77i_user;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON FUNCTIONS TO voya_q77i_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLES TO voya_q77i_user;


--
-- PostgreSQL database dump complete
--

