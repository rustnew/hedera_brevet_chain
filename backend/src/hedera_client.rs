// src/hedera_client.rs
use hedera::{
    Client,
    TopicMessageSubmitTransaction,
    PrivateKey,
    TopicId,
    Hbar,
    AccountId,
    Status,
};

use chrono;
use hex;

pub async fn submit_to_hedera(
    hash: String,
    ipfs_cid: String,
    cpc_code: String,
    user_wallet: String,
) -> Result<String, Box<dyn std::error::Error>> {
    
    // ✅ Utiliser for_testnet()
    let client = Client::for_testnet();
    
    // 🔑 Charger la clé privée
    let private_key_bytes = hex::decode(
        "302e020100300506032b6570042204200f909cd346a9d947d89bce0bc9358fa3833f92547ed74681de2389fb9ba60301"
    ).map_err(|e| format!("Hex decode error: {}", e))?;
    
    let private_key = PrivateKey::from_bytes_der(&private_key_bytes)
        .map_err(|e| format!("Private key parsing error: {}", e))?;
    
    // 🧑‍⚖️ Définir l'opérateur - Parse explicitement en AccountId
    let operator_account_id: AccountId = "0.0.123456".parse()
        .map_err(|e| format!("Account ID parsing error: {}", e))?;
    
    client.set_operator(operator_account_id, private_key.clone());
    
    // 📌 ID du topic HCS → convertir en TopicId
    let topic_id: TopicId = "0.0.987654".parse()
        .map_err(|e| format!("Topic ID parsing error: {}", e))?;
    
    // 📝 Message à envoyer
    let message = serde_json::json!({
        "hash": hash,
        "ipfs_cid": ipfs_cid,
        "cpc_code": cpc_code,
        "user_wallet": user_wallet,
        "timestamp": chrono::Utc::now().timestamp(),
    }).to_string();
    
    // ✅ CORRECTION PRINCIPALE : Construire, signer et exécuter en une seule chaîne
    let response = TopicMessageSubmitTransaction::new()
        .topic_id(topic_id)
        .message(message.as_bytes())
        .max_transaction_fee(Hbar::from_tinybars(1_000_000))
        .sign(private_key)  // Signer directement
        .execute(&client)   // Exécuter directement
        .await?;
    
    // 📋 Obtenir le reçu pour vérifier le statut
    let receipt = response.get_receipt(&client).await?;
    
    // ✅ Vérifier que la transaction a réussi en comparant avec Status::Success
    if receipt.status != Status::Success {
        return Err(format!("Transaction failed with status: {:?}", receipt.status).into());
    }
    
    // ✅ Retourner l'ID de transaction - gérer le cas Option
    match receipt.transaction_id {
        Some(tx_id) => Ok(tx_id.to_string()),
        None => Ok("Transaction successful but no ID available".to_string()),
    }
}