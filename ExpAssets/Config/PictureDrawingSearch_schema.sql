CREATE TABLE participants (
	id integer primary key autoincrement not null,
	userhash text not null,
	random_seed text not null,
	sex text not null,
	age integer not null, 
	handedness text not null,
	created text not null,
	klibs_commit text not null
);

CREATE TABLE events (
	id integer primary key autoincrement not null,
	user_id integer not null,
	trial_id integer not null,
	trial_num integer not null,
	label text not null,
	trial_clock float not null,
	eyelink_clock integer
);

CREATE TABLE logs (
	id integer primary key autoincrement not null,
	user_id integer not null,
	message text not null,
	trial_clock float not null,
	eyelink_clock integer
);

CREATE TABLE trials (
	id integer primary key autoincrement not null,
	participant_id integer key not null,
	block_num integer not null,
	trial_num integer not null,
	practicing text not null,
    image text not null,
	mask_type text not null,
    mask_size text not null,
	rt real not null, -- reaction time
    response text not null,
    init_fix text not null
);
