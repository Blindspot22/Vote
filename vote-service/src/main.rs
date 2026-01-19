use actix_web::{web, App, HttpResponse, HttpServer, Responder};
use redis::{Commands, RedisResult};
use serde::Deserialize;
use std::env;

#[derive(Deserialize)]
struct Vote {
    vote: String,
}

async fn health() -> impl Responder {
    HttpResponse::Ok().body("OK")
}

async fn vote(vote: web::Json<Vote>) -> impl Responder {
    let redis_host = env::var("REDIS_HOST").unwrap_or_else(|_| "127.0.0.1".to_string());
    let client = redis::Client::open(format!("redis://{}/", redis_host)).unwrap();
    let mut con = client.get_connection().unwrap();

    let _: () = con.rpush("votes", &vote.vote).unwrap();

    HttpResponse::Ok().body("Voted!")
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .route("/health", web::get().to(health))
            .route("/", web::post().to(vote))
    })
    .bind("0.0.0.0:80")?
    .run()
    .await
}
