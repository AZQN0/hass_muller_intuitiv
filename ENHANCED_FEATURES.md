# 🚀 Enhanced Features v0.11.0 - Complete Feature Expansion

## 📊 **Toutes les informations API maintenant exploitées**

### ✅ **Fonctionnalités ajoutées**

#### **1. 🏠 Noms de pièces dans les entités**
- **AVANT** : `FPN Thermostat 5792`
- **MAINTENANT** : `Chambre Quentin`, `Cuisine`, `Bureau`
- **Implémentation** : Mapping automatique ID device → nom de pièce depuis `/api/homesdata`

#### **2. 🎯 Types de pièces (room types)**
- `bedroom` → Chambre
- `kitchen` → Cuisine
- `home_office` → Bureau
- Intégré dans les attributs et le device registry

#### **3. 🌡️ Capteur température extérieure**
- **Nouvelle entité** : `sensor.outdoor_temperature`
- **Valeur exemple** : 14.4°C
- **Source** : Modules NMG du système

#### **4. 📶 Capteur force WiFi**
- **Nouvelle entité** : `sensor.wifi_strength`
- **Valeur exemple** : 71%
- **Icônes dynamiques** : 📶 selon la force du signal

#### **5. 👤 Capteurs de présence par pièce**
- **Nouvelle entité** : `sensor.chambre_quentin_presence`
- **États** : `detected` / `not_detected`
- **Source** : Capteurs de présence intégrés

#### **6. 🪟 Capteurs d'ouverture de fenêtres**
- **Nouvelle entité** : `sensor.chambre_quentin_window`
- **États** : `open` / `closed`
- **Icônes dynamiques** : 🪟 selon l'état

#### **7. 🔥 Capteurs de boost par pièce**
- **Nouvelle entité** : `sensor.chambre_quentin_boost_status`
- **États** : `enabled` / `disabled` / `unknown`
- **Icônes dynamiques** : 🔥 selon l'état

#### **8. ⏰ Informations temporelles étendues**
Dans les attributs des entités climate :
- **`setpoint_expires_at`** : Heure d'expiration de la consigne temporaire
- **`anticipating`** : Mode anticipation activé
- **`lowering`** : Abaissement en cours
- **`pairing_status`** : État appairage des modules

#### **9. 🔧 Device Registry enrichi**
- **Nom des devices** : Utilise le nom de la pièce
- **Area suggestion** : Auto-assignation des areas HA
- **Firmware info** : Version firmware si disponible
- **Modèles descriptifs** : "Chambre Quentin Thermostat" vs "FPN Heater"

## 🏗️ **Architecture technique**

### **Nouveaux modules**
- **`sensor.py`** : Platform sensor avec 7 types de capteurs
- **`api.get_home_system_info()`** : Récupération informations système
- **Enhanced coordinator** : Mapping room names + system info

### **Mapping des données**
```python
# Correspondance automatique
device_id → room_name + room_type + enhanced_attributes

# Exemples :
"3755235792" → "Chambre Quentin" (bedroom)
"1664008980" → "Cuisine" (kitchen)
"811784546" → "Bureau" (home_office)
```

### **Entités créées automatiquement**
```yaml
# Climate entities (existant, amélioré)
climate.chambre_quentin          # Au lieu de climate.muller_intuitiv_device_3755235792
climate.cuisine
climate.bureau

# Sensor entities (NOUVEAU)
sensor.outdoor_temperature       # Température extérieure système
sensor.wifi_strength             # Force WiFi système
sensor.chambre_quentin_presence  # Présence par pièce
sensor.chambre_quentin_window    # Fenêtre par pièce
sensor.chambre_quentin_boost_status # Boost par pièce
# ... (une entité par pièce équipée)
```

## 📋 **Informations API exploitées**

### **Données homestatus maintenant utilisées**
| Champ API | Utilisation | Avant | Maintenant |
|-----------|-------------|-------|-------------|
| `anticipating` | Attribut climate | ❌ Ignoré | ✅ Affiché |
| `boost_status` | Sensor dédié | ❌ Basic | ✅ Sensor entité |
| `lowering` | Attribut climate | ❌ Ignoré | ✅ Affiché |
| `open_window` | Sensor dédié | ❌ Basic | ✅ Sensor entité |
| `pairing` | Attribut climate | ❌ Ignoré | ✅ Affiché |
| `presence` | Sensor dédié | ❌ Basic | ✅ Sensor entité |
| `therm_setpoint_end_time` | Temps expiration | ❌ Ignoré | ✅ Formaté datetime |

### **Données homesdata maintenant utilisées**
| Champ API | Utilisation | Avant | Maintenant |
|-----------|-------------|-------|-------------|
| `rooms[].name` | Nom entité | ❌ ID technique | ✅ Nom parlant |
| `rooms[].type` | Type pièce | ❌ Ignoré | ✅ Attribut + registry |
| `modules[].outdoor_temperature` | Sensor système | ❌ Ignoré | ✅ Sensor entité |
| `modules[].wifi_strength` | Sensor système | ❌ Ignoré | ✅ Sensor entité |
| `modules[].firmware_revision` | Device registry | ❌ Ignoré | ✅ SW version |

## 🎯 **User Experience amélioré**

### **Interface Home Assistant**
- **Noms explicites** : "Chambre Quentin" au lieu de "Device 5792"
- **Areas automatiques** : Suggestion de zones basées sur le nom de pièce
- **Sensors organisés** : Groupement par pièce avec icônes cohérentes
- **Informations système** : Température extérieure et WiFi visibles
- **État temporel** : Expiration des consignes temporaires affichée

### **Device & Entity Registry**
- **Device names** : "Chambre Quentin Thermostat"
- **Manufacturer** : Muller
- **Model** : "Intuitiv FPN"
- **SW Version** : "Rev 185" (firmware)
- **Suggested Area** : "Chambre Quentin"

## 🔧 **Configuration requise**

### **Home Assistant**
- Version : 2024.1.0+
- Platforms : `climate`, `sensor` (automatique)
- Redémarrage requis après mise à jour

### **Muller Intuitiv System**
- Système compatible existant
- Aucune configuration supplémentaire
- Auto-détection de toutes les capacités

## 📦 **Installation v0.11.0**

### **HACS**
1. Mettre à jour vers v0.11.0
2. Redémarrer Home Assistant
3. Nouvelles entités apparaissent automatiquement

### **Manuel**
1. Remplacer `custom_components/muller_intuitiv/`
2. Redémarrer Home Assistant
3. Vérifier nouvelles entités dans Intégrations

## 🎉 **Résultat final**

**AVANT v0.11.0:**
- 3 entités climate : `climate.muller_intuitiv_device_XXXX`
- Informations limitées dans attributs
- Noms techniques peu parlants

**APRÈS v0.11.0:**
- 3 entités climate : `climate.chambre_quentin`, `climate.cuisine`, `climate.bureau`
- 8+ entités sensor : présence, fenêtres, boost, température extérieure, WiFi
- Device registry enrichi avec noms, firmware, areas
- 15+ attributs étendus par entité climate
- Interface utilisateur 100% francisée et intuitive

## ✨ **Technologies utilisées**
- **Python 3.9+** avec type hints complets
- **Home Assistant 2024.1.0+** avec device registry moderne
- **API Muller Intuitiv** exploitation exhaustive des endpoints
- **Architecture modulaire** avec sensor platform dédié
- **Backward compatibility** 100% sans breaking changes

**Toutes les informations API sont maintenant exploitées et présentées de manière intuitive !** 🚀