use rusqlite;
use std::{path::PathBuf, str::FromStr};

struct SqliteWrapper {
    pub file: PathBuf,
    connection: rusqlite::Connection,
}

impl SqliteWrapper {
    pub fn new(&mut self){
        self.file = PathBuf::new();
    }

    pub fn initialize(&mut self){
        self.connection = rusqlite::Connection::open(self.file.to_str().unwrap());
    }
}


fn main() {
    let conn = rusqlite::Connection::open_in_memory().unwrap();
    conn.execute(
        "CREATE TABLE person (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        data BLOB)",
        (),
    )

    conn.execute(
        "INSERT INTO person (name, data) VALUES (?1, ?2)",
        (&me.name, &me.data),
    )
    .unwrap();

    let mut stmt = conn.prepare("SELECT id, name, data FROM person").unwrap();
    let person_iterator = stmt.query_map([], |row| {
        Ok(Person {
            id: row.get(0).unwrap(),
            name: row.get(1).unwrap(),
            data: row.get(2).unwrap(),
        })
    });

    for person in person_iterator.unwrap() {
        println!("Found person {}", person.unwrap().to_str());
    }
}
