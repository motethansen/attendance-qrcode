# Manual attendance

Upload the student excel file extracted from the student system.

add date columns in the files and rename with the format:
CLASSCODE_DDMMYYYY_HHMM.xlsx

exanple

BU2001-LA_26062024_1300.xlsx

used columns in the excel:

STUDENTID	GIVENNAME	FAMILYNAME 24/5/24	31/5/24	7/6/24	14/6/24	21/6/24	26/6/24

make sure to rename all the files in the folder to match each week new dates.

---
update July 16 2024

add SQLalchemy

init database and migrate to update schemas

```
flask db init
```

```
flask db migrate -m "Initial migration."
```

```
flask db upgrade
```

set the environmentL

```
export FLASK_APP=flask_app.py
flask run
```


when uploadingthe class register files, make sure to edit the columns as follow:
StudentID, given_name, family_name, gender, country, email, dob

