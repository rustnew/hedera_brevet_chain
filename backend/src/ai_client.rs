use reqwest;
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
struct AiRequest {
    raw_idea: String,
}

#[derive(Deserialize)]
pub struct AiResponse {
    pub title: String,
    pub problem: String,
    pub solution: String,
    pub claims: Vec<String>,
    pub cpc_code: String,
    pub novelty_score: u8,
}

pub async fn call_ai_service(raw_idea: String) -> Result<AiResponse, Box<dyn std::error::Error>> {
    let client = reqwest::Client::new();

    let response = client
        .post("http://localhost:8000/ai/structure")
        .json(&AiRequest { raw_idea })
        .timeout(std::time::Duration::from_secs(30))
        .send()
        .await?;

    let ai_response = response.json::<AiResponse>().await?;
    Ok(ai_response)
}