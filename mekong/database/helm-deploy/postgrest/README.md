## Usage

### GET
```
curl -H "Accept-Profile: migration" "http://localhost:3000/white_listed_tables"
```

### POST
```
curl -X POST -H "Content-Profile: migration" -H "Content-Type: application/json" -H "Prefer: return=representation" "http://localhost:3000/white_listed_tables" -d '{ "table_name": "data-platform-exp-322803.VINHDP.TABLE_N", "cron": "15 3 * * *", "alias": ""}'
```

## Permissions

Create schema and table

```
create schema scoreboards;
create table scoreboards.users(id int, email text);

insert into scoreboards.users values (1, 'vinh.dang@mservice.com.vn');
```

Grant unsecured permissions
```
set role postgres;

GRANT SELECT ON ALL TABLES IN SCHEMA scoreboards TO anonymous;
GRANT USAGE ON SCHEMA scoreboards TO anonymous;

GRANT INSERT, UPDATE, DELETE ON TABLE scoreboards.users TO anonymous;
```

Check permissions
```
set role anonymous;

select * from public.users;
 id |           email           
----+---------------------------
  1 | vinh.dang@mservice.com.vn
  2 | quoc.ho@mservice.com.vn
  3 | duy.ha@mservice.com.vn
  4 | giang.vu1@mservice.com.vn
(4 rows)
```