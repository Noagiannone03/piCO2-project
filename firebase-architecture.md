# Architecture Firebase - My Pico 🌱

## Vue d'ensemble du système

My Pico devient une plateforme collaborative de surveillance de la qualité de l'air à Marseille, avec auto-enregistrement des capteurs et configuration simplifiée via interface web.

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
├── pendingDevices: array<deviceId> // Devices en attente d'ajout manuel
└── permissions: {
    └── canViewPublicData: boolean
}
```

### 2. Collection `devices` 📡
```
devices/{deviceId} // deviceId = code unique du Pico (ex: "picoAZ12")
├── info/
│   ├── deviceId: string (unique, ex: "picoAZ12")
│   ├── name: string ("Mon Pico Salon") // défini par l'utilisateur
│   ├── type: string ("pico-co2")
│   ├── owner: string (uid) // null au début, assigné quand utilisateur l'ajoute
│   ├── location: {
│   │   ├── lat: number // récupéré automatiquement via WiFi/IP
│   │   ├── lng: number
│   │   ├── address: string // géocodage inverse
│   │   ├── indoor: boolean (true par défaut)
│   │   └── room?: string // défini par l'utilisateur
│   ├── isPublic: boolean (false par défaut)
│   ├── isRegistered: boolean // true dès le premier démarrage
│   ├── isConfigured: boolean // true quand utilisateur l'a ajouté
│   ├── registeredAt: timestamp // première connexion du Pico
│   ├── configuredAt: timestamp // quand utilisateur l'a configuré
│   ├── lastSeen: timestamp
│   └── status: "online" | "offline" | "error"
├── settings/
│   ├── alertThresholds: {
│   │   ├── warning: number (1000)
│   │   └── danger: number (1500)
│   ├── measurementInterval: number (30 secondes)
│   └── sharePublicly: boolean (false par défaut)
├── calibration/
│   ├── lastCalibration: timestamp
│   ├── calibrationOffset: number (0)
│   └── calibrationNote?: string
└── network/
    ├── macAddress: string
    ├── ipAddress: string
    ├── wifiSSID: string
    └── signalStrength: number
```

### 3. Collection `measurements` 📊
```
measurements/{deviceId}/data/{auto-generated-id}
├── deviceId: string
├── timestamp: timestamp
├── co2_ppm: number
├── temperature?: number
├── humidity?: number
├── air_quality: "excellent" | "good" | "medium" | "bad" | "danger"
├── location: {lat, lng} // copie pour requêtes géo
├── isPublic: boolean // copié depuis device.isPublic
└── metadata: {
    ├── firmware_version: string
    ├── uptime_seconds: number
    ├── wifi_rssi: number
    └── free_memory?: number
}
```

### 4. Collection `deviceRegistration` 🔄 (temporaire pour le flux)
```
deviceRegistration/{deviceId}
├── deviceId: string
├── registrationStep: "wifi_config" | "initial_setup" | "ready"
├── tempData: {
│   ├── location?: {lat, lng, address}
│   ├── networkInfo?: {macAddress, ipAddress, wifiSSID}
│   └── firstBootTime: timestamp
├── createdAt: timestamp
└── expiresAt: timestamp // auto-suppression après 24h
```

### 5. Collection `publicStats` 🌍 (inchangée)
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

## Flux de Configuration des Picos

### 1. Premier démarrage du Pico
```
Pico démarre → Vérifie first_boot_flag → Si premier boot:
└── Affiche "Configuration initiale - Connectez-vous à https://noagiannone03.github.io/piCO2-project"
└── Active point d'accès WiFi "My-Pico-picoAZ12"
└── Attend configuration WiFi
```

### 2. Configuration WiFi
```
Utilisateur connecte WiFi → Pico obtient Internet → 
└── Auto-enregistrement dans Firestore:
    ├── Crée document devices/picoAZ12
    ├── Récupère géolocalisation (IP → lat/lng)
    ├── Sauvegarde infos réseau
    └── Marque isRegistered = true
```

### 3. Ajout par l'utilisateur
```
Dashboard → "Ajouter Pico" → Tutoriel → 
└── Page d'attente avec deviceId en paramètre →
└── Polling Firestore pour détecter le device →
└── Ajout automatique aux devices de l'utilisateur
```

## API Cloud Functions

### `/api/device/register` (nouveau)
- **Méthode**: POST
- **Auth**: None (appelé par le Pico)
- **Body**: `{deviceId, location, networkInfo, metadata}`
- **Fonction**: Auto-enregistrement du Pico au premier boot

### `/api/measurements/submit` (modifié)
- **Méthode**: POST  
- **Auth**: Device token (deviceId)
- **Body**: `{deviceId, timestamp, co2_ppm, temperature?, humidity?, metadata}`
- **Fonction**: Ajout direct dans Firestore measurements

### `/api/device/claim` (nouveau)
- **Méthode**: POST
- **Auth**: User token
- **Body**: `{deviceId, name, room?, sharePublicly?}`
- **Fonction**: Utilisateur revendique un device

### `/api/geolocation/resolve` (nouveau)
- **Méthode**: POST
- **Auth**: None
- **Body**: `{ip}`
- **Fonction**: Résout IP → lat/lng → adresse

## Règles de Sécurité Firestore

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Utilisateurs peuvent lire/écrire leurs propres données
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Devices : lecture libre, écriture par propriétaire ou création initiale
    match /devices/{deviceId} {
      allow read: if request.auth != null;
      allow create: if request.auth == null; // Pico peut créer au premier boot
      allow write: if request.auth != null && 
        (request.auth.uid == resource.data.owner || resource.data.owner == null);
    }
    
    // Mesures : lecture selon permissions, écriture libre (Picos)
    match /measurements/{deviceId}/data/{measurementId} {
      allow read: if request.auth != null && 
        (request.auth.uid == get(/databases/$(database)/documents/devices/$(deviceId)).data.owner ||
         get(/databases/$(database)/documents/devices/$(deviceId)).data.isPublic == true);
      allow write: if true; // Picos peuvent écrire librement
    }
    
    // Registration temporaire : lecture/écriture libre
    match /deviceRegistration/{deviceId} {
      allow read, write: if true;
    }
    
    // Stats publiques : lecture libre, écriture par fonctions Cloud
    match /publicStats/{document=**} {
      allow read: if true;
      allow write: if false; // Seulement via Cloud Functions
    }
  }
}
```

## Nouvelles Pages Web

### `/config/{deviceId}` - Page d'attente configuration
- Affiche le statut de configuration du Pico
- Polling pour détecter quand le device est enregistré
- Redirection automatique vers dashboard

### `/setup` - Tutoriel de configuration
- Guide étape par étape pour configurer un Pico
- Instructions détaillées avec animations
- Génération du lien vers la page d'attente

## Architecture de Déploiement

### Frontend
- **Hébergement**: Firebase Hosting
- **Domaine**: https://noagiannone03.github.io/piCO2-project
- **CDN**: Global via Firebase

### Backend
- **Database**: Firestore (multi-région)
- **Functions**: Cloud Functions 2nd gen
- **Storage**: Cloud Storage pour exports/logs
- **Monitoring**: Cloud Monitoring + Custom metrics

### Sécurité
- **HTTPS**: Forcé partout
- **CORS**: Configuré pour domaine principal
- **Rate Limiting**: Implémenté dans Cloud Functions
- **Validation**: Stricte sur tous les endpoints

Cette architecture assure une scalabilité excellente, une configuration automatisée et une expérience utilisateur fluide ! 🚀