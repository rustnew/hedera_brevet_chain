// Contrôle des étapes
function nextStep(step) {
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    document.getElementById(`step${step}`).classList.add('active');
}

function prevStep(step) {
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    document.getElementById(`step${step}`).classList.add('active');
}

// Stockage temporaire
let userData = {};
let patentData = {};

// Soumettre l'idée
async function submitIdea() {
    const fullName = document.getElementById('fullName').value.trim();
    const email = document.getElementById('email').value.trim();
    const idea = document.getElementById('idea').value.trim();
    const country = document.getElementById('country').value.trim() || null;
    const phone = document.getElementById('phone').value.trim() || null;
    const walletAddress = document.getElementById('walletAddress').value.trim() || "0.0.anonymous";

    if (!fullName || !email || !idea) {
        alert("Veuillez remplir tous les champs obligatoires.");
        return;
    }

    userData = { fullName, email, country, phone, walletAddress };
    const responseDiv = document.getElementById('response');
    responseDiv.className = 'response';
    responseDiv.textContent = 'Analyse par l’IA en cours...';

    try {
        const res = await fetch('/api/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user: userData,
                patent: { raw_idea: idea }
            })
        });

        const data = await res.json();

        if (res.ok) {
            // Stocker les données
            patentData = data.structured_patent || {};
            // Afficher le brevet
            displayPatent(data, userData);
            nextStep(3);
        } else {
            responseDiv.className = 'response error';
            responseDiv.textContent = `Échec : ${data.message || 'Erreur inconnue'}`;
        }
    } catch (error) {
        responseDiv.className = 'response error';
        responseDiv.textContent = 'Erreur réseau : impossible de contacter le backend.';
        console.error('Erreur:', error);
    }
}

// Afficher le brevet structuré
function displayPatent(backendData, userData) {
    const preview = document.getElementById('patentPreview');
    const patent = backendData.structured_patent || {};

    preview.innerHTML = `
📝 BREVET STRUCTURÉ PAR L'IA
================================
TITRE : ${patent.title || "Non disponible"}

PROBLÈME TECHNIQUE :
${patent.problem || "Non spécifié"}

SOLUTION :
${patent.solution || "Non spécifiée"}

REVENDICATIONS :
${(patent.claims || ["Non spécifiées"]).join('\n')}

CODE CPC : ${patent.cpc_code || "À déterminer"}

--- INFORMATIONS INVENTEUR ---
Nom : ${userData.fullName}
Email : ${userData.email}
Pays : ${userData.country || "Non spécifié"}
Téléphone : ${userData.phone || "Non spécifié"}
Adresse Wallet : ${userData.walletAddress}

Date de dépôt : ${new Date().toLocaleDateString('fr-FR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
    `.trim();
}

// Télécharger en PDF
function downloadPDF() {
    if (!window.jspdf) {
        alert("Le générateur PDF n'est pas chargé.");
        return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4'
    });

    const content = document.getElementById('patentPreview').innerText;
    const lines = doc.splitTextToSize(content, 180);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(16);
    doc.text('Brevet Structuré - BrevetChain', 10, 20);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    doc.text(lines, 10, 40);

    doc.setFontSize(8);
    doc.setTextColor(100);
    doc.text(`Déposé par : ${userData.fullName} | Date : ${new Date().toLocaleDateString('fr-FR')}`, 10, 280);

    doc.save(`brevet_${Date.now()}.pdf`);
}