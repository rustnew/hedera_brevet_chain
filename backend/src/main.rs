use actix_cors::Cors;
use actix_web::{App, HttpServer, web};
use actix_files::Files;


mod db;
mod models;
mod routes;
mod ai_client;
mod hedera_client;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let pool = web::Data::new(db::create_pool().await);

    println!("Backend en cours d'exécution sur http://127.0.0.1:8080");

    HttpServer::new(move || {
        let cors = Cors::permissive()
            .allow_any_origin()
            .allow_any_header()
            .allow_any_method()
            .supports_credentials();

        App::new()
            .wrap(cors)
            .wrap(actix_web::middleware::Logger::default())
            .app_data(pool.clone())
            .service(Files::new("/static", "./static").show_files_listing())
            .service(Files::new("/", "./static").index_file("index.html"))
            .service(
                web::scope("/api")
                    .route("/submit", web::post().to(routes::submit_idea))
            )
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}