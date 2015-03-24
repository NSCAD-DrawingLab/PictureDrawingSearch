CREATE TABLE participants (
	id integer primary key autoincrement not null,
	userhash text not null, 
	gender text not null, 
	age integer not null, 
	handedness text not null,
	created text not null,
	modified text not null --not implemented yet (ie. it is set equal to created at creation but no modification logic exists in Klibs
);

CREATE TABLE trials (
	id integer primary key autoincrement not null,
	participant_id integer key not null,
	block_num integer not null,
	trial_num integer not null,
	practicing text not null,
	mask text not null,
  mask_diam text not null,
	material text not null,
	form text not null,
	rt real not null, -- reaction time
  response text not null,
  initial_fixation text not null
);
