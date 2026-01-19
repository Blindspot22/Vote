use actix_web::{web, App, HttpResponse, HttpServer, Responder};
use postgres::{Client, NoTls};
use redis::{Commands};
use serde::Serialize;
use std::collections::HashMap;
use std::env;

#[derive(Serialize)]
struct Result {
    vote: String,
    count: i64,
}

async fn health() -> impl Responder {
    HttpResponse::Ok().body("OK")
}

async fn get_results() -> impl Responder {
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

    let mut votes: Vec<String> = con.lrange("votes", 0, -1).unwrap();
    let _: () = con.del("votes").unwrap();

    for vote in votes.drain(..) {
        client
            .execute("INSERT INTO votes (vote) VALUES ($1)", &[&vote])
            .unwrap();
    }

    let mut results = HashMap::new();
    for row in client.query("SELECT vote, count(*) FROM votes GROUP BY vote", &[]).unwrap() {
        let vote: String = row.get(0);
        let count: i64 = row.get(1);
        results.insert(vote, count);
    }

    HttpResponse::Ok().json(results)
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .route("/health", web::get().to(health))
            .route("/", web::get().to(get_results))
    })
    .bind("0.0.0.0:80")?
    .run()
    .await
}
