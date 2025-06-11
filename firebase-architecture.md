# Architecture Firebase - My Pico 🌱

## Vue d'ensemble du système

My Pico devient une plateforme collaborative de surveillance de la qualité de l'air à Marseille, permettant à chaque utilisateur de gérer ses capteurs et de contribuer aux données publiques agrégées.

## Structure de Base de Données Firestore

### 1. Collection `users` 👤
```
users/{uid}
├── profile/
│   ├── email: string
│   ├── displayName: string
│   ├── photoURL: string
│   ├── createdAt: timestamp
│   ├── lastLoginAt: timestamp
│   └── location?: {lat, lng, address}
├── devices: array<deviceId>
└── permissions: {
    └── canViewPublicData: boolean
}
```

### 2. Collection `devices` 📡
```
devices/{deviceId}
├── info/
│   ├── deviceId: string (unique)
│   ├── name: string ("Mon Pico Salon")
│   ├── type: string ("pico-co2")
│   ├── owner: string (uid)
│   ├── location: {
│   │   ├── lat: number
│   │   ├── lng: number
│   │   ├── address: string
│   │   ├── indoor: boolean
│   │   └── room?: string
│   ├── isPublic: boolean (contribute aux données publiques)
│   ├── createdAt: timestamp
│   ├── lastSeen: timestamp
│   └── status: "online" | "offline" | "error"
├── settings/
│   ├── alertThresholds: {
│   │   ├── warning: number (1000)
│   │   └── danger: number (1500)
│   ├── measurementInterval: number (minutes)
│   └── sharePublicly: boolean
└── calibration/
    ├── lastCalibration: timestamp
    ├── calibrationOffset: number
    └── calibrationNote?: string
```

### 3. Collection `measurements` 📊
```
measurements/{deviceId}/data/{timestamp-documentId}
├── deviceId: string
├── timestamp: timestamp
├── co2_ppm: number
├── temperature?: number
├── humidity?: number
├── air_quality: "excellent" | "good" | "medium" | "bad" | "danger"
├── location: {lat, lng} (copie pour requêtes géo)
├── isPublic: boolean
└── metadata: {
    ├── firmware_version?: string
    ├── battery_level?: number
    └── signal_strength?: number
}
```

### 4. Collection `publicStats` 🌍 (données agrégées publiques)
```
publicStats/marseille/zones/{zoneId}
├── zoneId: string ("centre", "nord", "sud", "est", "ouest")
├── zoneName: string
├── bounds: {
│   ├── north: number
│   ├── south: number
│   ├── east: number
│   └── west: number
├── lastUpdate: timestamp
├── activeDevices: number
├── currentStats: {
│   ├── avgCO2: number
│   ├── minCO2: number
│   ├── maxCO2: number
│   └── qualityDistribution: {
│       ├── excellent: number
│       ├── good: number
│       ├── medium: number
│       ├── bad: number
│       └── danger: number
│   }
├── hourlyAverage: array<{hour, avgCO2, count}>
└── lastMeasurements: array<{lat, lng, co2_ppm, quality, timestamp}>
```

### 5. Collection `alerts` 🚨
```
alerts/{alertId}
├── deviceId: string
├── userId: string
├── type: "high_co2" | "device_offline" | "calibration_needed"
├── level: "warning" | "danger" | "info"
├── message: string
├── value?: number (pour high_co2)
├── createdAt: timestamp
├── acknowledged: boolean
└── acknowledgedAt?: timestamp
```

## Règles de Sécurité Firestore

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Utilisateurs peuvent lire/écrire leurs propres données
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Appareils : seul le propriétaire peut modifier
    match /devices/{deviceId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && 
        (request.auth.uid == resource.data.owner || 
         !exists(/databases/$(database)/documents/devices/$(deviceId)));
    }
    
    // Mesures : lecture selon permissions, écriture par l'appareil
    match /measurements/{deviceId}/data/{measurementId} {
      allow read: if request.auth != null && 
        (request.auth.uid == get(/databases/$(database)/documents/devices/$(deviceId)).data.owner ||
         get(/databases/$(database)/documents/devices/$(deviceId)).data.isPublic == true);
      allow write: if request.auth != null;
    }
    
    // Stats publiques : lecture libre, écriture par fonctions Cloud
    match /publicStats/{document=**} {
      allow read: if true;
      allow write: if false; // Seulement via Cloud Functions
    }
    
    // Alertes : seul le propriétaire
    match /alerts/{alertId} {
      allow read, write: if request.auth != null && request.auth.uid == resource.data.userId;
    }
  }
}
```

## Architecture Technique

### Frontend (Web App)
- **Framework**: Vanilla JS avec Firebase SDK v9+
- **Authentification**: Firebase Auth (Google, Email/Password)
- **Base de données**: Firestore avec écouteurs temps réel
- **Cartes**: Leaflet.js pour la visualisation géographique
- **Graphiques**: Chart.js pour les visualisations de données
- **Hébergement**: Firebase Hosting

### Backend Services
- **Cloud Functions**: Agrégation des données publiques, alertes automatiques
- **Cloud Storage**: Stockage des exports de données, logs
- **Cloud Scheduler**: Tâches périodiques de nettoyage et agrégation

### Capteurs (Pico)
- **Communication**: HTTPS POST vers Cloud Function
- **Authentification**: API Key par device
- **Données**: JSON avec timestamp, géolocalisation, mesures

## Flux de Données

### 1. Enregistrement d'un capteur
```
User créé compte → Device ajouté à user.devices → Device doc créée → Configuration initiale
```

### 2. Réception de données capteur
```
Pico → Cloud Function → Validation → Firestore measurements → Trigger stats update
```

### 3. Mise à jour stats publiques
```
New measurement → Cloud Function trigger → Update zone stats → Real-time update frontend
```

### 4. Visualisation utilisateur
```
User login → Load devices → Real-time listeners → Charts & alerts update
```

## API Cloud Functions

### `/api/device/register`
- **Méthode**: POST
- **Auth**: User token
- **Body**: `{deviceId, name, location, settings}`
- **Retour**: Device configuration

### `/api/measurements/submit`
- **Méthode**: POST  
- **Auth**: Device API key
- **Body**: `{deviceId, timestamp, co2_ppm, temperature?, humidity?}`
- **Retour**: Success status

### `/api/public/zones`
- **Méthode**: GET
- **Auth**: None (public)
- **Retour**: Données agrégées par zone de Marseille

### `/api/export/{deviceId}`
- **Méthode**: GET
- **Auth**: Owner token
- **Params**: `?start=timestamp&end=timestamp&format=csv|json`
- **Retour**: Export des données

## Performance & Optimisation

### Indexation Firestore
```
measurements/{deviceId}/data
├── timestamp (DESC)
├── air_quality + timestamp (DESC) 
└── isPublic + location + timestamp (DESC)
```

### Pagination & Limites
- **Mesures en temps réel**: 50 derniers points
- **Historique**: Pagination par tranches de 1000
- **Cache client**: 5 minutes pour stats publiques
- **Cleanup automatique**: Données > 1 an archivées

Cette architecture assure une scalabilité, une sécurité robuste et une expérience utilisateur fluide pour la plateforme My Pico. 🚀