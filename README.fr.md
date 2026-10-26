# UnMeta Screenshare

**Affiche la vue et le son de ton Meta Quest sur ton ordinateur en Wi-Fi, sans l'app de diffusion de Meta.**

[English](README.md)

UnMeta Screenshare est une petite app en terminal pour Windows, macOS et Linux. Un assistant pas à pas configure une fois l'ADB sans fil du casque ; ensuite, une touche suffit pour lancer la diffusion. Elle s'appuie sur [scrcpy](https://github.com/Genymobile/scrcpy) et [adb](https://developer.android.com/tools/adb) : pas de connexion à un compte Meta sur le PC, pas de cloud, pas de service de cast. Elle convient donc bien à un casque durci (hardening) où les fonctions de diffusion de Meta sont désactivées.

> Ce projet n'est ni affilié, ni approuvé, ni sponsorisé par Meta Platforms, Inc. « Meta Quest » est une marque de Meta Platforms, Inc.

## Fonctionnalités

- **Configuration guidée** : brancher, autoriser le débogage USB, activer l'ADB Wi-Fi, lire l'IP, débrancher, se connecter. Chaque étape explique quoi faire et avance toute seule quand le casque est détecté.
- **Diffusion en une touche** : Espace sur l'écran d'accueil.
- **Réglages d'affichage en direct** : déplace ou redimensionne le recadrage avec les flèches, pivote avec + / -, change l'audio, les IPS, le débit, le mode fenêtre. scrcpy redémarre en une seconde environ pour afficher chaque changement.
- **Audio** : désactivé, PC uniquement, ou casque + PC en même temps.
- **Casques enregistrés** : plusieurs casques, chacun avec son adresse et ses réglages.
- Interface **en anglais et en français** (suit la langue du système ; `L` pour changer).

## Fonctionnement

```
Quest  ──(adb en Wi-Fi, port 5555)──>  ton ordinateur  ──>  fenêtre scrcpy + son
```

Le Quest produit une image côte à côte pour les deux yeux. Le préréglage *Meta Quest 3* recadre un seul œil et corrige son inclinaison pour obtenir une image plate normale.

## Prérequis

- Un Meta Quest avec le **mode développeur** activé (voir [Première configuration](#première-configuration)).
- Un **câble USB-C de données**, pour la première configuration et après chaque redémarrage du casque.
- Le casque et l'ordinateur sur le **même réseau Wi-Fi**.
- **scrcpy 3.0+** et **adb**. L'installeur Windows inclut les deux.

Testé sur Meta Quest 3. Les autres modèles devraient fonctionner avec le préréglage *Image complète* et quelques réglages : [partage tes valeurs](#contribuer).

## Installation

### Windows

Télécharge `UnMeta-Screenshare-Setup-x.y.z.exe` depuis la page [Releases](https://github.com/SeifB13/unmeta-screenshare/releases) et lance-le. scrcpy et adb sont inclus. Une version portable `.zip` est aussi disponible.

L'exécutable n'est pas encore signé : Windows SmartScreen peut afficher un avertissement. Clique sur *Informations complémentaires → Exécuter quand même*.

### macOS

```bash
curl -fsSL https://raw.githubusercontent.com/SeifB13/unmeta-screenshare/main/scripts/install.sh | bash
```

Le script installe scrcpy et adb avec Homebrew s'ils manquent, puis l'app avec pipx. Ou à la main :

```bash
brew install scrcpy pipx
brew install --cask android-platform-tools
pipx install git+https://github.com/SeifB13/unmeta-screenshare
```

### Linux

```bash
curl -fsSL https://raw.githubusercontent.com/SeifB13/unmeta-screenshare/main/scripts/install.sh | bash
```

Les paquets scrcpy des distributions sont souvent antérieurs à la 3.0. Dans ce cas, installe une version récente en suivant le [guide Linux de scrcpy](https://github.com/Genymobile/scrcpy/blob/master/doc/linux.md). L'accès USB peut nécessiter des règles udev (`android-sdk-platform-tools-common` sous Debian/Ubuntu, `android-udev-rules` sous Arch).

Puis lance :

```bash
unmeta
```

## Première configuration

1. **Active le mode développeur** dans l'app mobile Meta Horizon : *Appareils → ton casque → Paramètres du casque → Mode développeur*. Il faut un [compte développeur Meta](https://developers.meta.com/horizon/) gratuit. Redémarre le casque.
2. Lance UnMeta Screenshare. L'assistant s'ouvre au premier lancement (ou touche `W`) :
   1. Vérifie qu'adb et scrcpy sont disponibles.
   2. Te demande de brancher le casque avec le câble USB-C.
   3. Attend que tu acceptes **Autoriser le débogage USB** dans le casque (coche *Toujours autoriser*).
   4. Active l'ADB Wi-Fi et lit l'adresse IP du casque.
   5. Te demande de débrancher le câble.
   6. Se connecte en Wi-Fi et enregistre le casque.

Astuce : réserve l'adresse IP du casque dans ta box (bail DHCP statique) pour qu'elle ne change jamais.

## Au quotidien

Allume le casque, lance l'app, appuie sur **Espace**.

**Après un redémarrage du casque**, le système désactive l'ADB Wi-Fi. Appuie sur `W`, branche le câble et refais les étapes (environ 30 secondes).

| Touche | Écran d'accueil |
|---|---|
| Espace | Lancer / arrêter la diffusion |
| C | Se connecter |
| D | Réglages d'affichage |
| W | Assistant de configuration |
| L | Changer de langue |
| ? | Aide |
| Q | Quitter |

## Réglages d'affichage

Appuie sur `D`. Place le focus sur le panneau *Réglage en direct*, puis :

| Touche | Action |
|---|---|
| ← ↑ ↓ → | Déplacer le recadrage (10 px) |
| Maj + flèches | Redimensionner le recadrage |
| + / - | Pivoter (1°) |
| Entrée ou F5 | Appliquer |
| Ctrl+R | Revenir au préréglage |

Pendant la diffusion, les changements s'appliquent tout seuls après une courte pause. scrcpy ne sait pas modifier ces options à chaud : l'app le relance (environ 1-2 s), la connexion Wi-Fi reste active. La diffusion est en fenêtre par défaut pour garder l'app accessible : Alt+F dans la fenêtre scrcpy bascule le plein écran, ou active *Plein écran* dans les réglages (la diffusion reste en fenêtre pendant le réglage). La commande scrcpy générée s'affiche en bas, pratique pour signaler un bug.

Les réglages sont enregistrés par casque dans `config.json` (`unmeta --print-config-path` indique où).

## Dépannage

- **Casque injoignable** : il est en veille, sur un autre réseau, ou a redémarré (refais l'assistant avec le câble).
- **Pas de demande de débogage** : débranche et rebranche le câble ; vérifie le mode développeur ; essaie un autre câble.
- **Image décentrée ou penchée** : ajuste le recadrage et l'angle ensemble.
- **Pas de son** : essaie le mode audio *PC uniquement*.
- **Vidéo saccadée** : baisse le débit ou les IPS max, ou rapproche-toi de la box.

## Sécurité

L'ADB Wi-Fi donne un accès de débogage complet au casque depuis ton réseau local. Les connexions exigent toujours la clé RSA approuvée dans le casque, mais garde-le en tête sur un réseau partagé. Il se désactive au redémarrage du casque, ou immédiatement avec `adb usb` câble branché. Tu peux révoquer les ordinateurs autorisés dans les paramètres développeur du casque.

## Contribuer

Les rapports de bug et les préréglages pour d'autres casques sont les bienvenus : ouvre une issue avec le modèle du casque, la version de scrcpy et la commande affichée dans *Réglages d'affichage*.

Les commandes de développement et de build sont décrites dans le [README anglais](README.md#contributing).

## Crédits et licence

UnMeta Screenshare est distribué sous [licence MIT](LICENSE).

Il pilote [scrcpy](https://github.com/Genymobile/scrcpy) de Genymobile et Romain Vimont (licence Apache 2.0), que la version Windows embarque avec adb (Android SDK Platform-Tools). Voir [THIRD_PARTY_NOTICES.md](packaging/windows/THIRD_PARTY_NOTICES.md).
