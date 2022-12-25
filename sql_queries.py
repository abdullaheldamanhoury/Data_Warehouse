import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES

staging_events_table_drop = "DROP TABLE IF EXISTS staging_events"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs"
songplay_table_drop = "DROP TABLE IF EXISTS songplays"
user_table_drop = "DROP TABLE IF EXISTS users"
song_table_drop = "DROP TABLE IF EXISTS songs"
artist_table_drop = "DROP TABLE IF EXISTS artists"
time_table_drop = "DROP TABLE IF EXISTS time"

# CREATE TABLES

staging_events_table_create= ("""
CREATE TABLE IF NOT EXISTS staging_events
(
artist VARCHAR,
auth VARCHAR, 
firstName VARCHAR,
gender VARCHAR,   
itemInSession INTEGER,
lastName VARCHAR,
length FLOAT,
level VARCHAR, 
location VARCHAR,
method VARCHAR,
page VARCHAR,
registration BIGINT,
sessionId INTEGER,
song VARCHAR,
status INTEGER,
ts BIGINT,
userAgent VARCHAR,
userId INTEGER
);
""")

staging_songs_table_create = ("""
CREATE TABLE IF NOT EXISTS staging_songs
(
song_id VARCHAR,
num_songs INTEGER,
artist_id VARCHAR,
artist_latitude float,
artist_longitude float,
artist_location VARCHAR,
artist_name VARCHAR,
title VARCHAR,
duration NUMERIC,
year INTEGER
);
""")

songplay_table_create = ("""
CREATE TABLE IF NOT EXISTS songplays
(
songplay_id INTEGER IDENTITY(0,1) PRIMARY KEY sortkey ,
start_time TIMESTAMP,
user_id INTEGER,
level VARCHAR,
song_id VARCHAR,
artist_id VARCHAR,
session_id INTEGER,
location VARCHAR,
user_agent VARCHAR
);
""")

user_table_create = ("""
CREATE TABLE IF NOT EXISTS users
(
user_id INTEGER PRIMARY KEY distkey,
first_name VARCHAR,
last_name VARCHAR,
gender VARCHAR,
level VARCHAR
);
""")

song_table_create = ("""
CREATE TABLE IF NOT EXISTS songs
(
song_id VARCHAR PRIMARY KEY,
title VARCHAR,
artist_id VARCHAR distkey,
year INTEGER,
duration FLOAT
);
""")

artist_table_create = ("""
CREATE TABLE IF NOT EXISTS artists
(
artist_id VARCHAR PRIMARY KEY distkey,
name VARCHAR,
location VARCHAR,
latitude FLOAT,
longitude FLOAT
);
""")

time_table_create = ("""
CREATE TABLE IF NOT EXISTS time
(
start_time  TIMESTAMP PRIMARY KEY sortkey distkey ,
hour INTEGER,
day INTEGER,
week INTEGER,
month INTEGER,
year INTEGER,
weekday VARCHAR
);
""")

# STAGING TABLES

staging_events_copy = ("""COPY staging_events FROM {}
    CREDENTIALS 'aws_iam_role={}'
    COMPUPDATE OFF region 'us-west-2'
    TIMEFORMAT as 'epochmillisecs'
    TRUNCATECOLUMNS BLANKSASNULL EMPTYASNULL
    FORMAT AS JSON {};""").format(config.get('S3','LOG_DATA'), config.get('IAM_ROLE', 'ARN'), config.get('S3','LOG_JSONPATH'))

staging_songs_copy = ("""COPY staging_songs FROM {}
    CREDENTIALS 'aws_iam_role={}'
    COMPUPDATE OFF region 'us-west-2'
    FORMAT AS JSON 'auto' 
    TRUNCATECOLUMNS BLANKSASNULL EMPTYASNULL;""").format(config.get('S3','SONG_DATA'), config.get('IAM_ROLE', 'ARN'))

# FINAL TABLES

songplay_table_insert = ("""
INSERT INTO songplays (start_time, user_id, level, song_id, artist_id, session_id, location, user_agent)
SELECT DISTINCT TIMESTAMP 'epoch' + (ste.ts / 1000) * INTERVAL '1 second' as start_time,
ste.userId  as user_id,
ste.level as level,
sts.song_id as song_id,
sts.artist_id as artist_id,
ste.sessionId as session_id,
ste.location as location,
ste.userAgent as user_agent
FROM staging_songs sts 
JOIN staging_events ste
ON (ste.song = sts.title AND sts.artist_name = ste.artist)
WHERE ste.page = 'NextSong';
""")

user_table_insert = ("""
INSERT INTO users (user_id, first_name, last_name, gender, level) 
SELECT DISTINCT userId as user_id,
firstName as first_name, 
lastName as last_name, 
gender as gender, 
level as level
FROM staging_events
WHERE userId IS NOT NULL;
""")

song_table_insert = ("""
INSERT INTO songs (song_id, title, artist_id, year, duration) 
SELECT DISTINCT song_id,
title, 
artist_id, 
year, 
duration
FROM staging_songs 
WHERE song_id IS NOT NULL;
""")

artist_table_insert = ("""
INSERT INTO artists (artist_id, name, location, latitude, longitude) 
SELECT DISTINCT artist_id,
artist_name, 
artist_location, 
artist_latitude, 
artist_longitude
FROM staging_songs 
where artist_id IS NOT NULL;
""")

time_table_insert = ("""
INSERT INTO time(start_time, hour, day, week, month, year, weekday) 
SELECT DISTINCT TIMESTAMP 'epoch' + (ts/1000) * INTERVAL '1 second' as start_time,
EXTRACT(HOUR FROM start_time) AS hour,
EXTRACT(DAY FROM start_time) AS day,
EXTRACT(WEEKS FROM start_time) AS week,
EXTRACT(MONTH FROM start_time) AS month,
EXTRACT(YEAR FROM start_time) AS year,
to_char(start_time, 'Day') AS weekday
FROM staging_events 
WHERE ts IS NOT NULL;
""")

# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
