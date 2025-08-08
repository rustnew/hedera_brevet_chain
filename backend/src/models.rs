use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::Utc;
use sqlx::Type;
use  sqlx::FromRow;

#[derive(Serialize, Deserialize, Clone, Debug, FromRow)]
pub struct User {
    pub id: Uuid,
    pub full_name: String,
    pub email: String,
    pub phone: Option<String>,
    pub country: Option<String>,
    pub wallet_address: String,
    pub created_at: chrono::DateTime<Utc>,
}

#[derive(Deserialize, Serialize, Clone, Debug, FromRow)]
pub struct PatentDraft {
    pub id: Uuid,
    pub user_id: Uuid,
    pub raw_idea: String,
    pub status: PatentStatus,
    pub created_at: chrono::DateTime<Utc>,
}

#[derive(Deserialize, Serialize, Clone, Type, Debug)]
#[sqlx(type_name = "status", rename_all = "lowercase")]
pub enum PatentStatus {
    Draft,
    Submitted,
    Rejected,
    OnBlockchain,
}

#[derive(Deserialize, Serialize, Clone, Debug)]
pub struct SubmitIdeaRequest {
    pub user: UserInfo,
    pub patent: PatentInput,
}

#[derive(Deserialize, Clone, Debug, Serialize)]
pub struct UserInfo {
    pub full_name: String,
    pub email: String,
    pub phone: Option<String>,
    pub country: Option<String>,
    pub wallet_address: String,
}

#[derive(Deserialize, Clone, Debug, Serialize)]
pub struct PatentInput {
    pub raw_idea: String,
}

#[derive(Serialize, Clone , Debug, FromRow)]
pub struct SubmitIdeaResponse {
    pub patent_id: Uuid,
    pub message: String,
    pub structured_patent: Option<StructuredPatent>,
}

#[derive(Serialize, Debug, Clone, Deserialize)]
pub struct StructuredPatent {
    pub title: String,
    pub problem: String,
    pub solution: String,
    pub claims: Vec<String>,
    pub cpc_code: String,
}