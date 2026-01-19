use postgres::{Client, NoTls};
use redis::Commands;
use std::env;
use std::thread;
use std::time::Duration;

fn main() {
    let db_host = env::var("DB_HOST").unwrap_or_else(|_| "localhost".to_string());
    let db_name = env::var("DB_NAME").unwrap_or_else(|_| "postgres".to_string());
    let db_user = env::var("DB_USER").unwrap_or_else(|_| "postgres".to_string());
    let db_password = env::var("DB_PASSWORD").unwrap_or_else(|_| "postgres".to_string());

    let mut client = Client::connect(
        &format!(
            "host={} user={} password={} dbname={}",
            db_host, db_user, db_password, db_name
        ),
        NoTls,
    )
    .unwrap();

    client
        .batch_execute(
            "CREATE TABLE IF NOT EXISTS votes (
                id SERIAL PRIMARY KEY,
                vote VARCHAR NOT NULL
            )",
        )
        .unwrap();

    let redis_host = env::var("REDIS_HOST").unwrap_or_else(|_| "127.0.0.1".to_string());
    let redis_client = redis::Client::open(format!("redis://{}/", redis_host)).unwrap();
    let mut con = redis_client.get_connection().unwrap();

    loop {
        let vote: Option<String> = con.lpop("votes", Default::default()).unwrap();
        if let Some(vote) = vote {
            client
                .execute("INSERT INTO votes (vote) VALUES ($1)", &[&vote])
                .unwrap();
        }
        thread::sleep(Duration::from_millis(100));
    }
}
