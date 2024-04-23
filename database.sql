CREATE TABLE "credentials" (
	"username"		TEXT,
	"hashed_pw"		TEXT,

	"primary_key"	INTEGER,
	PRIMARY KEY("primary_key" AUTOINCREMENT)
);


CREATE TABLE "reports" (
	"user_id"		TEXT,
	"latitude"		FLOAT,
	"longitude"		FLOAT,
	"state"			TEXT,
	"country"		TEXT,
	"description"	TEXT,
	"category"		TEXT,
	"temperature"	FLOAT,
	"humidity"		FLOAT,
	"rain"			FLOAT,
	"date"			TEXT,
	"time"			TEXT,
	"filepath"		TEXT,
	
	"primary_key"	INTEGER,
	PRIMARY KEY("primary_key" AUTOINCREMENT)
);