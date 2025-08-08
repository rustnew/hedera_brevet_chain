// src/routes.rs
use actix_web::{web, HttpResponse, Result};
use serde_json::json;
use crate::models::{SubmitIdeaRequest, SubmitIdeaResponse, PatentDraft, PatentStatus,  StructuredPatent};
use sqlx::PgPool;
use uuid::Uuid;
use chrono::Utc;
use crate::ai_client;
use crate::hedera_client;

pub async fn submit_idea(
    data: web::Json<SubmitIdeaRequest>,  // ✅ CORRECTION: Nommer le paramètre
    pool: web::Data<PgPool>,
) -> Result<HttpResponse> {
    let user_info = data.user.clone();  // ✅ CORRECTION: Utiliser 'data' correctement
    let raw_idea = data.patent.raw_idea.clone();  // ✅ CORRECTION: Utiliser 'data' correctement
    
    let user_id = match get_or_create_user(&pool, &user_info).await {
        Ok(id) => id,
        Err(_) => return Ok(HttpResponse::InternalServerError().json(json!({
            "message": "Échec de création de l'utilisateur"
        }))),
    };

    let patent_id = Uuid::new_v4();
    
    let ai_response = match ai_client::call_ai_service(raw_idea.clone()).await {
        Ok(resp) => resp,
        Err(e) => {
            eprintln!("Erreur IA: {}", e);
            return Ok(HttpResponse::InternalServerError().json(json!({
                "message": "Service IA indisponible"
            })));
        }
    };

    if ai_response.novelty_score < 50 {
        return Ok(HttpResponse::BadRequest().json(json!({
            "message": "Idée probablement non brevetable"
        })));
    }

    let draft = PatentDraft {
        id: patent_id,
        user_id,
        raw_idea,
        status: PatentStatus::Submitted,
        created_at: Utc::now(),
    };

    if let Err(e) = sqlx::query!(
        r#"
        INSERT INTO patent_drafts (id, user_id, raw_idea, status)
        VALUES ($1, $2, $3, $4)
        "#,
        draft.id,
        draft.user_id,
        draft.raw_idea,
        draft.status as PatentStatus,
    )
    .execute(pool.as_ref())
    .await
    {
        eprintln!("Erreur SQL: {}", e);
        return Ok(HttpResponse::InternalServerError().finish());
    }

    let ipfs_cid = "QmXy...Z123".to_string();
    let hash = "a1b2c3d4...".to_string();

    match hedera_client::submit_to_hedera(
        hash,
        ipfs_cid,
        ai_response.cpc_code.clone(),
        user_info.wallet_address,
    ).await {
        Ok(_timestamp) => {
            if let Err(e) = sqlx::query!(
                "UPDATE patent_drafts SET status = $1 WHERE id = $2",
                PatentStatus::OnBlockchain as PatentStatus,
                patent_id
            )
            .execute(pool.as_ref())
            .await
            {
                eprintln!("Échec mise à jour DB: {}", e);
            }
        }
        Err(e) => {
            eprintln!("Échec Hedera: {}", e);
            return Ok(HttpResponse::InternalServerError().json(json!({
                "message": "Échec enregistrement blockchain"
            })));
        }
    }

    Ok(HttpResponse::Ok().json(SubmitIdeaResponse {
        patent_id,
        message: "Idée enregistrée sur la blockchain".to_string(),
        structured_patent: Some(StructuredPatent {
            title: ai_response.title,
            problem: ai_response.problem,
            solution: ai_response.solution,
            claims: ai_response.claims,
            cpc_code: ai_response.cpc_code,
        }),
    }))
}


async fn get_or_create_user(
    pool: &PgPool,
    info: &crate::models::UserInfo,
) -> Result<Uuid, Box<dyn std::error::Error>> {
    // Vérifier si l'utilisateur existe déjà
    let result = sqlx::query!(
        "SELECT id FROM users WHERE email = $1",
        &info.email
    )
    .fetch_optional(pool)
    .await?;

    if let Some(row) = result {
        // L'utilisateur existe, retourner son ID
        Ok(row.id)
    } else {
        // L'utilisateur n'existe pas, le créer
        let new_id = Uuid::new_v4();
        
        sqlx::query!(
            "INSERT INTO users (id, full_name, email, phone, country, wallet_address) 
             VALUES ($1, $2, $3, $4, $5, $6)",
            new_id,
            info.full_name,
            info.email,
            info.phone,
            info.country,
            info.wallet_address
        )
        .execute(pool)
        .await?;

        Ok(new_id)
    }
}
