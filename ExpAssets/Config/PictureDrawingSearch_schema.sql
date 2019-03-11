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

CREATE TABLE trials (
	id integer primary key autoincrement not null,
	participant_id integer key not null,
	block_num integer not null,
	trial_num integer not null,
    arrangement text not null,
	mask_type text not null
);
