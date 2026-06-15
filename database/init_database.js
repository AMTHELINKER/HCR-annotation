// =============================================================
// Initialisation de la Base de Données MongoDB - HCR4
// Système de Gestion des Ordonnances Médicales
// =============================================================
// Diagramme de classe implémenté :
//   Utilisateur (parent) -> Medecin, Patient (héritage)
//   Ordonnance -> LigneOrdonnance (embedded) -> Medicament (ref)
//   Pharmacie -> DisponibiliteMedicament (embedded) -> Medicament (ref)
//   Medecin <-> Patient (relation CONSULTER many-to-many)
// =============================================================

const DB_NAME = "hcr4_ordonnances";
db = db.getSiblingDB(DB_NAME);

print("=== Nettoyage des collections existantes ===");
db.getCollectionNames().forEach(c => db[c].drop());

// =============================================================
// 1. COLLECTION : utilisateurs (Single Table Inheritance)
// =============================================================
// Stratégie : On utilise le champ "role" pour différencier
// Medecin et Patient (héritage par discriminateur).
// C'est la meilleure approche MongoDB pour l'héritage.
// =============================================================

print("[1/6] Création de la collection 'utilisateurs'...");
db.createCollection("utilisateurs", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["nom", "email", "motDePasse", "role"],
      properties: {
        nom:         { bsonType: "string", description: "Nom complet" },
        email:       { bsonType: "string", description: "Email unique" },
        motDePasse:  { bsonType: "string", description: "Mot de passe hashé" },
        role:        { enum: ["medecin", "patient"], description: "Discriminateur d'héritage" },
        // --- Champs spécifiques Medecin ---
        specialite:   { bsonType: "string", description: "Spécialité médicale (medecin)" },
        numeroOrdre:  { bsonType: "string", description: "Numéro d'ordre (medecin)" },
        // --- Champs spécifiques Patient ---
        telephone:    { bsonType: "string", description: "Téléphone (patient)" },
        adresse:      { bsonType: "string", description: "Adresse postale (patient)" },
        // --- Relation CONSULTER ---
        patientsIds:  { bsonType: "array", description: "IDs des patients consultés (medecin)", items: { bsonType: "objectId" } },
        medecinsIds:  { bsonType: "array", description: "IDs des médecins consultants (patient)", items: { bsonType: "objectId" } }
      }
    }
  }
});

// Index unique sur email + index sur role pour les requêtes polymorphiques
db.utilisateurs.createIndex({ email: 1 }, { unique: true });
db.utilisateurs.createIndex({ role: 1 });
db.utilisateurs.createIndex({ numeroOrdre: 1 }, { sparse: true, unique: true });

// =============================================================
// 2. COLLECTION : medicaments
// =============================================================
// Collection indépendante car référencée par Ordonnance ET Pharmacie.
// Pattern "referenced" pour éviter la duplication.
// =============================================================

print("[2/6] Création de la collection 'medicaments'...");
db.createCollection("medicaments", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["nom", "dosage", "forme"],
      properties: {
        nom:    { bsonType: "string", description: "Nom du médicament" },
        dosage: { bsonType: "string", description: "Dosage (ex: 500mg)" },
        forme:  { bsonType: "string", description: "Forme galénique (comprimé, sirop, etc.)" }
      }
    }
  }
});

db.medicaments.createIndex({ nom: 1 });
db.medicaments.createIndex({ nom: "text" });

// =============================================================
// 3. COLLECTION : ordonnances
// =============================================================
// LigneOrdonnance est EMBARQUÉE dans Ordonnance car :
//   - Une ligne n'existe pas sans son ordonnance (composition)
//   - On lit toujours les lignes avec l'ordonnance (locality)
//   - Chaque ligne référence un médicament par ObjectId
// =============================================================

print("[3/6] Création de la collection 'ordonnances'...");
db.createCollection("ordonnances", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["dateCreation", "statut", "medecinId", "patientId"],
      properties: {
        dateCreation:       { bsonType: "date", description: "Date de création" },
        statut:             { enum: ["brouillon", "digitalisee", "validee", "envoyee"], description: "Statut du workflow" },
        fichierOriginal:    { bsonType: "string", description: "Chemin vers le scan original" },
        contenuDigitalise:  { bsonType: "string", description: "Contenu OCR/HTR extrait" },
        medecinId:          { bsonType: "objectId", description: "Réf vers le médecin prescripteur" },
        patientId:          { bsonType: "objectId", description: "Réf vers le patient" },
        // --- LigneOrdonnance embarquée (pattern Embedded Document) ---
        lignes: {
          bsonType: "array",
          description: "Lignes de l'ordonnance (médicaments prescrits)",
          items: {
            bsonType: "object",
            required: ["medicamentId", "quantite", "posologie", "duree"],
            properties: {
              medicamentId: { bsonType: "objectId", description: "Réf vers le médicament" },
              quantite:     { bsonType: "int", description: "Quantité prescrite" },
              posologie:    { bsonType: "string", description: "Posologie (ex: 1 cp 3x/jour)" },
              duree:        { bsonType: "string", description: "Durée du traitement (ex: 7 jours)" }
            }
          }
        }
      }
    }
  }
});

db.ordonnances.createIndex({ medecinId: 1 });
db.ordonnances.createIndex({ patientId: 1 });
db.ordonnances.createIndex({ statut: 1 });
db.ordonnances.createIndex({ dateCreation: -1 });

// =============================================================
// 4. COLLECTION : pharmacies
// =============================================================
// DisponibiliteMedicament est EMBARQUÉE dans Pharmacie car :
//   - La disponibilité est propre à chaque pharmacie
//   - On consulte le stock en même temps que la pharmacie
//   - Évite les jointures coûteuses
// =============================================================

print("[4/6] Création de la collection 'pharmacies'...");
db.createCollection("pharmacies", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["nom", "adresse", "telephone", "email"],
      properties: {
        nom:       { bsonType: "string", description: "Nom de la pharmacie" },
        adresse:   { bsonType: "string", description: "Adresse physique" },
        telephone: { bsonType: "string", description: "Numéro de téléphone" },
        email:     { bsonType: "string", description: "Email de contact" },
        // --- DisponibiliteMedicament embarquée ---
        stock: {
          bsonType: "array",
          description: "Stock de médicaments disponibles",
          items: {
            bsonType: "object",
            required: ["medicamentId", "disponible", "quantiteStock", "dateMiseAJour"],
            properties: {
              medicamentId:  { bsonType: "objectId", description: "Réf vers le médicament" },
              disponible:    { bsonType: "bool", description: "En stock oui/non" },
              quantiteStock: { bsonType: "int", description: "Quantité en stock" },
              dateMiseAJour: { bsonType: "date", description: "Dernière mise à jour" }
            }
          }
        }
      }
    }
  }
});

db.pharmacies.createIndex({ email: 1 }, { unique: true });
db.pharmacies.createIndex({ nom: 1 });
db.pharmacies.createIndex({ "stock.medicamentId": 1 });

// =============================================================
// 5. INSERTION DES DONNÉES DE DÉMONSTRATION
// =============================================================

print("[5/6] Insertion des données de démonstration...");

// --- Médicaments ---
const meds = db.medicaments.insertMany([
  { nom: "Amoxicilline",   dosage: "500mg",  forme: "comprimé" },
  { nom: "Paracétamol",    dosage: "1000mg", forme: "comprimé" },
  { nom: "Ibuprofène",     dosage: "400mg",  forme: "comprimé" },
  { nom: "Oméprazole",     dosage: "20mg",   forme: "gélule" },
  { nom: "Métformine",     dosage: "850mg",  forme: "comprimé" },
  { nom: "Doliprane",      dosage: "500mg",  forme: "sirop" },
  { nom: "Augmentin",      dosage: "1g",     forme: "sachet" },
  { nom: "Ventoline",      dosage: "100µg",  forme: "inhalateur" }
]);
const medIds = Object.values(meds.insertedIds);

// --- Médecins ---
const med1 = db.utilisateurs.insertOne({
  nom: "Dr. Mamadou Diallo",
  email: "m.diallo@hopital.sn",
  motDePasse: "$2b$12$hashedpassword1",
  role: "medecin",
  specialite: "Médecine Générale",
  numeroOrdre: "MED-2024-001",
  patientsIds: []
});

const med2 = db.utilisateurs.insertOne({
  nom: "Dr. Fatou Ndiaye",
  email: "f.ndiaye@hopital.sn",
  motDePasse: "$2b$12$hashedpassword2",
  role: "medecin",
  specialite: "Cardiologie",
  numeroOrdre: "MED-2024-002",
  patientsIds: []
});

// --- Patients ---
const pat1 = db.utilisateurs.insertOne({
  nom: "Abdoulaye Sow",
  email: "a.sow@email.sn",
  motDePasse: "$2b$12$hashedpassword3",
  role: "patient",
  telephone: "+221 77 123 45 67",
  adresse: "123 Rue de Dakar, Dakar",
  medecinsIds: [med1.insertedId, med2.insertedId]
});

const pat2 = db.utilisateurs.insertOne({
  nom: "Aminata Ba",
  email: "a.ba@email.sn",
  motDePasse: "$2b$12$hashedpassword4",
  role: "patient",
  telephone: "+221 76 987 65 43",
  adresse: "45 Avenue Cheikh Anta Diop, Dakar",
  medecinsIds: [med1.insertedId]
});

// Mise à jour relation bidirectionnelle CONSULTER
db.utilisateurs.updateOne({ _id: med1.insertedId }, { $set: { patientsIds: [pat1.insertedId, pat2.insertedId] } });
db.utilisateurs.updateOne({ _id: med2.insertedId }, { $set: { patientsIds: [pat1.insertedId] } });

// --- Ordonnances avec LigneOrdonnance embarquées ---
db.ordonnances.insertMany([
  {
    dateCreation: new Date("2026-06-01"),
    statut: "validee",
    fichierOriginal: "/uploads/ordonnance_001.jpeg",
    contenuDigitalise: "Amoxicilline 500mg - 1cp 3x/jour pendant 7 jours\nParacétamol 1g - si douleur",
    medecinId: med1.insertedId,
    patientId: pat1.insertedId,
    lignes: [
      { medicamentId: medIds[0], quantite: NumberInt(21), posologie: "1 comprimé 3 fois par jour", duree: "7 jours" },
      { medicamentId: medIds[1], quantite: NumberInt(10), posologie: "1 comprimé si douleur (max 3/jour)", duree: "5 jours" }
    ]
  },
  {
    dateCreation: new Date("2026-06-02"),
    statut: "envoyee",
    fichierOriginal: "/uploads/ordonnance_002.jpeg",
    contenuDigitalise: "Oméprazole 20mg - 1 gélule le matin à jeun",
    medecinId: med2.insertedId,
    patientId: pat1.insertedId,
    lignes: [
      { medicamentId: medIds[3], quantite: NumberInt(30), posologie: "1 gélule le matin à jeun", duree: "30 jours" },
      { medicamentId: medIds[4], quantite: NumberInt(60), posologie: "1 comprimé matin et soir", duree: "30 jours" }
    ]
  },
  {
    dateCreation: new Date("2026-06-03"),
    statut: "digitalisee",
    fichierOriginal: "/uploads/ordonnance_003.jpeg",
    contenuDigitalise: "Doliprane sirop 500mg - 1 dose poids 3x/jour",
    medecinId: med1.insertedId,
    patientId: pat2.insertedId,
    lignes: [
      { medicamentId: medIds[5], quantite: NumberInt(1), posologie: "1 dose poids 3 fois par jour", duree: "5 jours" },
      { medicamentId: medIds[7], quantite: NumberInt(1), posologie: "2 bouffées si crise", duree: "selon besoin" }
    ]
  }
]);

// --- Pharmacies avec DisponibiliteMedicament embarquées ---
db.pharmacies.insertMany([
  {
    nom: "Pharmacie Centrale de Dakar",
    adresse: "Place de l'Indépendance, Dakar",
    telephone: "+221 33 821 00 00",
    email: "contact@pharma-centrale.sn",
    stock: [
      { medicamentId: medIds[0], disponible: true,  quantiteStock: NumberInt(500),  dateMiseAJour: new Date() },
      { medicamentId: medIds[1], disponible: true,  quantiteStock: NumberInt(1200), dateMiseAJour: new Date() },
      { medicamentId: medIds[2], disponible: true,  quantiteStock: NumberInt(300),  dateMiseAJour: new Date() },
      { medicamentId: medIds[3], disponible: false, quantiteStock: NumberInt(0),    dateMiseAJour: new Date() },
      { medicamentId: medIds[5], disponible: true,  quantiteStock: NumberInt(80),   dateMiseAJour: new Date() }
    ]
  },
  {
    nom: "Pharmacie du Point E",
    adresse: "Rue 6, Point E, Dakar",
    telephone: "+221 33 825 11 22",
    email: "info@pharma-pointe.sn",
    stock: [
      { medicamentId: medIds[0], disponible: true,  quantiteStock: NumberInt(150),  dateMiseAJour: new Date() },
      { medicamentId: medIds[1], disponible: true,  quantiteStock: NumberInt(800),  dateMiseAJour: new Date() },
      { medicamentId: medIds[3], disponible: true,  quantiteStock: NumberInt(200),  dateMiseAJour: new Date() },
      { medicamentId: medIds[4], disponible: true,  quantiteStock: NumberInt(100),  dateMiseAJour: new Date() },
      { medicamentId: medIds[6], disponible: true,  quantiteStock: NumberInt(60),   dateMiseAJour: new Date() },
      { medicamentId: medIds[7], disponible: false, quantiteStock: NumberInt(0),    dateMiseAJour: new Date() }
    ]
  }
]);

// =============================================================
// 6. VÉRIFICATION FINALE
// =============================================================

print("[6/6] Vérification finale...");
print("");
print("=== Résumé de la base '" + DB_NAME + "' ===");
print("Collections : " + db.getCollectionNames().join(", "));
print("Utilisateurs : " + db.utilisateurs.countDocuments() + " (Médecins: " + db.utilisateurs.countDocuments({role:"medecin"}) + ", Patients: " + db.utilisateurs.countDocuments({role:"patient"}) + ")");
print("Médicaments  : " + db.medicaments.countDocuments());
print("Ordonnances  : " + db.ordonnances.countDocuments());
print("Pharmacies   : " + db.pharmacies.countDocuments());
print("");

// Test de requête : Ordonnances d'un patient avec lookup
print("=== Test: Ordonnances du patient Abdoulaye Sow ===");
db.ordonnances.aggregate([
  { $match: { patientId: pat1.insertedId } },
  { $lookup: { from: "utilisateurs", localField: "medecinId", foreignField: "_id", as: "medecin" } },
  { $unwind: "$medecin" },
  { $project: { "medecin.nom": 1, statut: 1, dateCreation: 1, nbLignes: { $size: "$lignes" } } }
]).forEach(doc => printjson(doc));

print("");
print("=== Test: Pharmacies ayant Amoxicilline en stock ===");
db.pharmacies.find(
  { "stock": { $elemMatch: { medicamentId: medIds[0], disponible: true } } },
  { nom: 1, adresse: 1, "stock.$": 1 }
).forEach(doc => printjson(doc));

print("");
print("============================================");
print(" Base de données initialisée avec succès !");
print("============================================");
