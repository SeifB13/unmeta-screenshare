"""UI strings in English and French.

The language must be set before the screens are imported: their key bindings read
these strings at class definition time.
"""

from __future__ import annotations

import locale
import os

LANGUAGES = ("en", "fr")
_lang = "en"

EN: dict[str, str] = {
    # Shared
    "key.back": "Back",
    "key.cancel": "Cancel",
    "key.quit": "Quit",
    "key.help": "Help",
    "err.no_adb": "adb was not found. Open the setup (W) to see how to install it.",
    "err.no_scrcpy": "scrcpy 3.0 or newer was not found. Open the setup (W) to see how to install it.",
    "err.no_profile": "No headset saved yet. Open the setup (W).",
    "err.unreachable": (
        "Cannot reach the headset at {addr}. Check that it is on and on the same Wi-Fi "
        "network. If it rebooted, Wi-Fi ADB is off again: open the setup (W) and redo the "
        "USB steps."
    ),
    "err.unauthorized": (
        "The headset refused the connection. Put it on, accept the debugging prompt, then retry."
    ),
    "stream.ended": "Streaming ended.",
    "stream.reconnecting": "Connection to {addr} lost: reconnecting…",
    "stream.reconnected": "Reconnected: streaming again.",
    "stream.lost": (
        "Could not reconnect to {addr} within a minute. Check that the headset is on and "
        "on the same Wi-Fi, then press Space. After a reboot, run the wizard again (W)."
    ),
    "stream.crashed": "scrcpy stopped with code {code}. See the log on the home screen.",
    "lang.changed": "Language set to {lang}. Restart the app to apply it.",
    "preset.quest3": "Meta Quest 3 (one eye, straightened)",
    "preset.full": "Full frame (both eyes, no crop)",
    "audio.off": "Off",
    "audio.pc": "PC only",
    "audio.dup": "Headset + PC",
    # Home
    "home.profile": "Headset",
    "home.address": "Address",
    "home.no_profile": "No headset yet",
    "home.btn.start": "▶ Start streaming",
    "home.btn.stop": "■ Stop streaming",
    "home.btn.connect": "Connect",
    "home.btn.display": "Display settings",
    "home.btn.setup": "Setup wizard",
    "home.btn.help": "Help",
    "home.status.idle": "○ Not connected",
    "home.status.connecting": "… Connecting to {addr}",
    "home.status.connected": "● Connected to {addr}",
    "home.status.reconnecting": "… Connection lost, reconnecting to {addr} (Space to stop)",
    "home.status.streaming": (
        "▶ Streaming from {addr}\n"
        "In the scrcpy window: Alt+F toggles fullscreen, closing the window stops streaming.\n"
        "Image badly framed? Press D (display settings), then V to see the whole image."
    ),
    "home.status.no_profile": "No headset saved yet: press W to start the setup wizard.",
    "home.log": "scrcpy output",
    "home.key.stream": "Start/Stop",
    "home.key.connect": "Connect",
    "home.key.display": "Display",
    "home.key.setup": "Setup",
    "home.key.language": "Français",
    # Wizard
    "wiz.stepbar": "Step {n}/{total} · {title}",
    "wiz.back": "◀ Back",
    "wiz.next": "Next ▶",
    "wiz.saved": 'Headset "{name}" saved. Press Space to start streaming.',
    "wiz.tools.title": "Check the required tools",
    "wiz.tools.body": (
        "UnMeta Screenshare relies on two open-source tools:\n\n"
        "- **adb** (Android Debug Bridge) talks to the headset.\n"
        "- **scrcpy** (3.0 or newer) shows its screen and plays its sound.\n\n"
        "The Windows installer ships both. On macOS and Linux, install whatever is missing "
        "with the command below, then press *Check again*."
    ),
    "wiz.tools.recheck": "Check again",
    "wiz.tools.checking": "Checking…",
    "wiz.tools.adb_ok": "✓ adb: {path}",
    "wiz.tools.adb_missing": "✗ adb not found",
    "wiz.tools.scrcpy_ok": "✓ scrcpy {version}: {path}",
    "wiz.tools.scrcpy_old": "✗ scrcpy {version} is too old (3.0 or newer required): {path}",
    "wiz.tools.scrcpy_missing": "✗ scrcpy not found",
    "wiz.tools.hint": "Install: {hint}",
    "wiz.prereq.title": "Prepare the headset",
    "wiz.prereq.body": (
        "Do this once:\n\n"
        "1. **Enable developer mode.** In the Meta Horizon phone app: *Devices → your "
        "headset → Headset settings → Developer mode → On*. It needs a free Meta developer "
        "account, created at <https://developers.meta.com/horizon/>. Restart the headset "
        "afterwards.\n"
        "2. Turn the headset on and join the **same Wi-Fi network** as this computer.\n"
        "3. Get a **USB-C cable that carries data** (some cables only charge).\n\n"
        "Wi-Fi ADB already enabled since the headset last rebooted? Skip straight to the "
        "connection."
    ),
    "wiz.prereq.skip": "Skip to connection",
    "wiz.plug.title": "Plug in the headset",
    "wiz.plug.body": (
        "Connect the headset to this computer with the USB-C cable and keep it on.\n\n"
        "The next step starts by itself once the headset is detected."
    ),
    "wiz.plug.waiting": "Waiting for a headset on USB…",
    "wiz.authorize.title": "Allow USB debugging",
    "wiz.authorize.body": (
        "Put the headset on: a prompt **Allow USB debugging?** appears.\n\n"
        "Tick **Always allow from this computer**, then choose **Allow**.\n\n"
        "No prompt? Unplug and replug the cable, and check that developer mode is on."
    ),
    "wiz.authorize.waiting": "Waiting for you to accept the prompt in the headset ({name})…",
    "wiz.authorize.no_permissions": (
        "✗ The system denies USB access to the headset. On Linux, install the udev rules for "
        "Android devices (package android-sdk-platform-tools-common or android-udev-rules), "
        "add your user to the plugdev group, then replug the cable."
    ),
    "wiz.authorize.lost": "The headset is no longer detected. Plug it back in.",
    "wiz.wifi.title": "Enable Wi-Fi ADB",
    "wiz.wifi.body": (
        "Press the button: the app reads the headset's IP address and switches ADB to Wi-Fi "
        "mode (port 5555).\n\n"
        "This mode is lost every time the headset **reboots**: come back here with the cable "
        "after a restart. Tip: reserve the headset's IP address in your router (DHCP "
        "reservation) so it never changes."
    ),
    "wiz.wifi.button": "Enable Wi-Fi ADB",
    "wiz.wifi.working": "Working…",
    "wiz.wifi.ok": "✓ Wi-Fi ADB enabled. Headset IP address: {ip}",
    "wiz.wifi.no_ip": (
        "✓ Wi-Fi ADB enabled, but the IP address could not be read. Find it in the headset "
        "(Settings → Wi-Fi → your network) and type it at the last step."
    ),
    "wiz.wifi.failed": "✗ Could not enable Wi-Fi ADB: {msg}",
    "wiz.unplug.title": "Unplug the cable",
    "wiz.unplug.body": (
        "You can unplug the USB cable now: the headset stays reachable over Wi-Fi.\n\n"
        "The next step starts by itself once the cable is removed."
    ),
    "wiz.unplug.waiting": "Waiting for the cable to be unplugged…",
    "wiz.connect.title": "Connect over Wi-Fi",
    "wiz.connect.body": (
        "Check the headset's address, connect, then give the headset a name to save it."
    ),
    "wiz.connect.address": "Address",
    "wiz.connect.button": "Connect",
    "wiz.connect.working": "Connecting to {addr}…",
    "wiz.connect.ok": "✓ Connected to {model} over Wi-Fi.",
    "wiz.connect.name": "Name",
    "wiz.connect.finish": "Save and finish",
    # Display settings
    "tuning.title": "Display settings · {name}",
    "tuning.preset": "Preset",
    "tuning.crop": "Crop one eye",
    "tuning.crop_dims": "W · H · X · Y",
    "tuning.angle": "Angle (°)",
    "tuning.fps": "Max FPS",
    "tuning.bitrate": "Bitrate (Mbit/s)",
    "tuning.max_size": "Max size (px)",
    "tuning.max_size_ph": "0 = original",
    "tuning.audio": "Audio",
    "tuning.fullscreen": "Fullscreen",
    "tuning.on_top": "Always on top",
    "tuning.record": "Record to file",
    "tuning.record_ph": "optional, e.g. capture.mp4",
    "tuning.pad": (
        "[b]Live adjust[/b] (click or Tab here)\n\n"
        "←↑↓→        move the crop\n"
        "Ctrl+←↑↓→   move by 50 px\n"
        "Shift+←↑↓→  resize the crop\n"
        "+ / -       rotate\n"
        "V / F6      full frame on/off\n"
        "Enter       apply\n\n"
        "Steps: 10 px, 1°. Each change restarts scrcpy (1-2 s)."
    ),
    "tuning.auto": "Auto-apply while streaming",
    "tuning.windowed": "Windowed while tuning",
    "tuning.apply": "Apply (F5)",
    "tuning.reset": "Reset to preset",
    "tuning.key.apply": "Apply",
    "tuning.key.reset": "Reset",
    "tuning.saved": "Settings saved.",
    "tuning.key.full_view": "Full frame",
    "tuning.map.unknown": "Frame size unknown. Connect the headset, or show the full frame once.",
    "tuning.map.size": "Raw frame: {w}×{h}",
    "tuning.map.crop": "Crop: {w}×{h} at x={x}, y={y}",
    "tuning.map.outside": "⚠ The crop goes past the edge of the frame.",
    "tuning.map.full_view": "Full frame shown: find the eye, then fit the rectangle on it.",
    # Help
    "help.title": "Help",
    "help.diagnostic": "Copy a diagnostic report (I)",
    "key.diagnostic": "Diagnostic",
    "diag.working": "Collecting the diagnostic report…",
    "diag.copied": "Diagnostic copied: paste it in your message (Ctrl+V).",
    "diag.also_saved": "Also saved to {path}",
    "diag.saved": "Diagnostic saved to {path}: attach this file to your message.",
    "diag.failed": "Could not copy or save the diagnostic report.",
    "help.body": (
        "# Help\n\n"
        "## Every day\n\n"
        "1. Turn the headset on (same Wi-Fi as this computer).\n"
        "2. Press **Space** (or *Start streaming*).\n\n"
        "After a **headset reboot**, Wi-Fi ADB is off: press **W**, plug the cable and "
        "follow the steps again (about 30 s).\n\n"
        "## Home shortcuts\n\n"
        "| Key | Action |\n|---|---|\n"
        "| Space | Start / stop streaming |\n"
        "| C | Connect to the headset |\n"
        "| D | Display settings |\n"
        "| W | Setup wizard |\n"
        "| L | Switch language |\n"
        "| I | Copy a diagnostic report |\n"
        "| Q | Quit |\n\n"
        "## In the scrcpy window\n\n"
        "MOD is Left Alt or Left Super by default.\n\n"
        "| Key | Action |\n|---|---|\n"
        "| MOD+F | Toggle fullscreen |\n"
        "| MOD+G | Resize to 1:1 |\n"
        "| MOD+W | Resize to remove black borders |\n"
        "| MOD+←/→ | Rotate the display |\n\n"
        "## Troubleshooting\n\n"
        "- **Cannot reach the headset**: it is asleep, on another network, or rebooted "
        "(redo the setup with the cable).\n"
        "- **Image off-center or tilted**: open *Display settings* (D), press V to see "
        "the whole image, place the rectangle on the eye, then press V again. "
        "Crop and angle depend on each other.\n"
        "- **No sound**: audio capture needs Android 11+ on the headset; try *PC only*.\n"
        "- **Choppy video**: lower the bitrate or the max FPS, or move closer to the router.\n"
        "- To turn Wi-Fi ADB off without rebooting, run `adb usb` with the cable plugged in."
    ),
}

FR: dict[str, str] = {
    "key.back": "Retour",
    "key.cancel": "Annuler",
    "key.quit": "Quitter",
    "key.help": "Aide",
    "err.no_adb": "adb est introuvable. Ouvre l'assistant (W) pour savoir comment l'installer.",
    "err.no_scrcpy": (
        "scrcpy 3.0 ou plus récent est introuvable. Ouvre l'assistant (W) pour savoir "
        "comment l'installer."
    ),
    "err.no_profile": "Aucun casque enregistré. Ouvre l'assistant (W).",
    "err.unreachable": (
        "Impossible de joindre le casque à {addr}. Vérifie qu'il est allumé et sur le même "
        "Wi-Fi. S'il a redémarré, l'ADB Wi-Fi est désactivé : ouvre l'assistant (W) et refais "
        "les étapes USB."
    ),
    "err.unauthorized": (
        "Le casque a refusé la connexion. Mets-le, accepte la demande de débogage, puis réessaie."
    ),
    "stream.ended": "Diffusion terminée.",
    "stream.reconnecting": "Connexion à {addr} perdue : reconnexion…",
    "stream.reconnected": "Reconnecté : la diffusion reprend.",
    "stream.lost": (
        "Impossible de se reconnecter à {addr} en une minute. Vérifie que le casque est allumé "
        "et sur le même Wi-Fi, puis appuie sur Espace. Après un redémarrage, relance "
        "l'assistant (W)."
    ),
    "stream.crashed": "scrcpy s'est arrêté (code {code}). Voir le journal sur l'accueil.",
    "lang.changed": "Langue réglée sur {lang}. Relance l'app pour l'appliquer.",
    "preset.quest3": "Meta Quest 3 (un œil, redressé)",
    "preset.full": "Image complète (deux yeux, sans recadrage)",
    "audio.off": "Désactivé",
    "audio.pc": "PC uniquement",
    "audio.dup": "Casque + PC",
    "home.profile": "Casque",
    "home.address": "Adresse",
    "home.no_profile": "Aucun casque",
    "home.btn.start": "▶ Lancer la diffusion",
    "home.btn.stop": "■ Arrêter la diffusion",
    "home.btn.connect": "Connecter",
    "home.btn.display": "Réglages d'affichage",
    "home.btn.setup": "Assistant",
    "home.btn.help": "Aide",
    "home.status.idle": "○ Non connecté",
    "home.status.connecting": "… Connexion à {addr}",
    "home.status.connected": "● Connecté à {addr}",
    "home.status.reconnecting": "… Connexion perdue, reconnexion à {addr} (Espace pour arrêter)",
    "home.status.streaming": (
        "▶ Diffusion depuis {addr}\n"
        "Dans la fenêtre scrcpy : Alt+F bascule le plein écran, fermer la fenêtre arrête la diffusion.\n"
        "Image mal cadrée ? Appuie sur D (réglages d'affichage), puis sur V pour voir l'image entière."
    ),
    "home.status.no_profile": "Aucun casque enregistré : appuie sur W pour lancer l'assistant.",
    "home.log": "Sortie de scrcpy",
    "home.key.stream": "Lancer/Arrêter",
    "home.key.connect": "Connecter",
    "home.key.display": "Affichage",
    "home.key.setup": "Assistant",
    "home.key.language": "English",
    "wiz.stepbar": "Étape {n}/{total} · {title}",
    "wiz.back": "◀ Retour",
    "wiz.next": "Suivant ▶",
    "wiz.saved": "Casque « {name} » enregistré. Appuie sur Espace pour lancer la diffusion.",
    "wiz.tools.title": "Vérifier les outils nécessaires",
    "wiz.tools.body": (
        "UnMeta Screenshare s'appuie sur deux outils open source :\n\n"
        "- **adb** (Android Debug Bridge) communique avec le casque.\n"
        "- **scrcpy** (3.0 ou plus récent) affiche son écran et diffuse son son.\n\n"
        "L'installeur Windows inclut les deux. Sous macOS et Linux, installe ce qui manque "
        "avec la commande ci-dessous, puis clique sur *Vérifier à nouveau*."
    ),
    "wiz.tools.recheck": "Vérifier à nouveau",
    "wiz.tools.checking": "Vérification…",
    "wiz.tools.adb_ok": "✓ adb : {path}",
    "wiz.tools.adb_missing": "✗ adb introuvable",
    "wiz.tools.scrcpy_ok": "✓ scrcpy {version} : {path}",
    "wiz.tools.scrcpy_old": "✗ scrcpy {version} est trop ancien (3.0 ou plus requis) : {path}",
    "wiz.tools.scrcpy_missing": "✗ scrcpy introuvable",
    "wiz.tools.hint": "Installation : {hint}",
    "wiz.prereq.title": "Préparer le casque",
    "wiz.prereq.body": (
        "À faire une seule fois :\n\n"
        "1. **Active le mode développeur.** Dans l'app mobile Meta Horizon : *Appareils → ton "
        "casque → Paramètres du casque → Mode développeur → Activé*. Il faut un compte "
        "développeur Meta gratuit, à créer sur <https://developers.meta.com/horizon/>. "
        "Redémarre ensuite le casque.\n"
        "2. Allume le casque et connecte-le au **même réseau Wi-Fi** que cet ordinateur.\n"
        "3. Prends un **câble USB-C qui transmet les données** (certains ne font que charger).\n\n"
        "L'ADB Wi-Fi est déjà activé depuis le dernier redémarrage du casque ? Passe "
        "directement à la connexion."
    ),
    "wiz.prereq.skip": "Passer à la connexion",
    "wiz.plug.title": "Brancher le casque",
    "wiz.plug.body": (
        "Branche le casque à cet ordinateur avec le câble USB-C et laisse-le allumé.\n\n"
        "L'étape suivante démarre toute seule dès que le casque est détecté."
    ),
    "wiz.plug.waiting": "En attente d'un casque branché en USB…",
    "wiz.authorize.title": "Autoriser le débogage USB",
    "wiz.authorize.body": (
        "Mets le casque : une fenêtre **Autoriser le débogage USB ?** apparaît.\n\n"
        "Coche **Toujours autoriser depuis cet ordinateur**, puis choisis **Autoriser**.\n\n"
        "Pas de fenêtre ? Débranche puis rebranche le câble, et vérifie que le mode "
        "développeur est activé."
    ),
    "wiz.authorize.waiting": "En attente de ton accord dans le casque ({name})…",
    "wiz.authorize.no_permissions": (
        "✗ Le système refuse l'accès USB au casque. Sous Linux, installe les règles udev pour "
        "Android (paquet android-sdk-platform-tools-common ou android-udev-rules), ajoute ton "
        "utilisateur au groupe plugdev, puis rebranche le câble."
    ),
    "wiz.authorize.lost": "Le casque n'est plus détecté. Rebranche-le.",
    "wiz.wifi.title": "Activer l'ADB Wi-Fi",
    "wiz.wifi.body": (
        "Clique sur le bouton : l'app lit l'adresse IP du casque et passe l'ADB en mode Wi-Fi "
        "(port 5555).\n\n"
        "Ce mode est perdu à chaque **redémarrage** du casque : reviens ici avec le câble "
        "après un redémarrage. Astuce : réserve l'adresse IP du casque dans ta box (bail DHCP "
        "statique) pour qu'elle ne change jamais."
    ),
    "wiz.wifi.button": "Activer l'ADB Wi-Fi",
    "wiz.wifi.working": "En cours…",
    "wiz.wifi.ok": "✓ ADB Wi-Fi activé. Adresse IP du casque : {ip}",
    "wiz.wifi.no_ip": (
        "✓ ADB Wi-Fi activé, mais l'adresse IP n'a pas pu être lue. Trouve-la dans le casque "
        "(Paramètres → Wi-Fi → ton réseau) et saisis-la à la dernière étape."
    ),
    "wiz.wifi.failed": "✗ Impossible d'activer l'ADB Wi-Fi : {msg}",
    "wiz.unplug.title": "Débrancher le câble",
    "wiz.unplug.body": (
        "Tu peux débrancher le câble USB : le casque reste joignable en Wi-Fi.\n\n"
        "L'étape suivante démarre toute seule dès que le câble est retiré."
    ),
    "wiz.unplug.waiting": "En attente du débranchement du câble…",
    "wiz.connect.title": "Se connecter en Wi-Fi",
    "wiz.connect.body": (
        "Vérifie l'adresse du casque, connecte-toi, puis donne un nom au casque pour l'enregistrer."
    ),
    "wiz.connect.address": "Adresse",
    "wiz.connect.button": "Connecter",
    "wiz.connect.working": "Connexion à {addr}…",
    "wiz.connect.ok": "✓ Connecté à {model} en Wi-Fi.",
    "wiz.connect.name": "Nom",
    "wiz.connect.finish": "Enregistrer et terminer",
    "tuning.title": "Réglages d'affichage · {name}",
    "tuning.preset": "Préréglage",
    "tuning.crop": "Recadrer un œil",
    "tuning.crop_dims": "L · H · X · Y",
    "tuning.angle": "Angle (°)",
    "tuning.fps": "IPS max",
    "tuning.bitrate": "Débit (Mbit/s)",
    "tuning.max_size": "Taille max (px)",
    "tuning.max_size_ph": "0 = d'origine",
    "tuning.audio": "Audio",
    "tuning.fullscreen": "Plein écran",
    "tuning.on_top": "Toujours au premier plan",
    "tuning.record": "Enregistrer dans",
    "tuning.record_ph": "facultatif, ex. capture.mp4",
    "tuning.pad": (
        "[b]Réglage en direct[/b] (clic ou Tab ici)\n\n"
        "←↑↓→        déplacer le recadrage\n"
        "Ctrl+←↑↓→   déplacer de 50 px\n"
        "Maj+←↑↓→    redimensionner\n"
        "+ / -       pivoter\n"
        "V / F6      image complète oui/non\n"
        "Entrée      appliquer\n\n"
        "Pas : 10 px, 1°. Chaque changement relance scrcpy (1-2 s)."
    ),
    "tuning.auto": "Appliquer pendant la diffusion",
    "tuning.windowed": "Fenêtré pendant le réglage",
    "tuning.apply": "Appliquer (F5)",
    "tuning.reset": "Revenir au préréglage",
    "tuning.key.apply": "Appliquer",
    "tuning.key.reset": "Réinitialiser",
    "tuning.saved": "Réglages enregistrés.",
    "tuning.key.full_view": "Image complète",
    "tuning.map.unknown": (
        "Taille de l'image inconnue. Connecte le casque ou affiche une fois l'image complète."
    ),
    "tuning.map.size": "Image brute : {w}×{h}",
    "tuning.map.crop": "Recadrage : {w}×{h} à x={x}, y={y}",
    "tuning.map.outside": "⚠ Le recadrage dépasse le bord de l'image.",
    "tuning.map.full_view": "Image complète affichée : repère l'œil, puis places-y le rectangle.",
    "help.title": "Aide",
    "help.diagnostic": "Copier un rapport de diagnostic (I)",
    "key.diagnostic": "Diagnostic",
    "diag.working": "Préparation du rapport de diagnostic…",
    "diag.copied": "Diagnostic copié : colle-le dans ton message (Ctrl+V).",
    "diag.also_saved": "Également enregistré dans {path}",
    "diag.saved": "Diagnostic enregistré dans {path} : joins ce fichier à ton message.",
    "diag.failed": "Impossible de copier ou d'enregistrer le rapport de diagnostic.",
    "help.body": (
        "# Aide\n\n"
        "## Au quotidien\n\n"
        "1. Allume le casque (même Wi-Fi que cet ordinateur).\n"
        "2. Appuie sur **Espace** (ou *Lancer la diffusion*).\n\n"
        "Après un **redémarrage du casque**, l'ADB Wi-Fi est désactivé : appuie sur **W**, "
        "branche le câble et refais les étapes (environ 30 s).\n\n"
        "## Raccourcis de l'accueil\n\n"
        "| Touche | Action |\n|---|---|\n"
        "| Espace | Lancer / arrêter la diffusion |\n"
        "| C | Se connecter au casque |\n"
        "| D | Réglages d'affichage |\n"
        "| W | Assistant de configuration |\n"
        "| L | Changer de langue |\n"
        "| I | Copier un rapport de diagnostic |\n"
        "| Q | Quitter |\n\n"
        "## Dans la fenêtre scrcpy\n\n"
        "MOD correspond par défaut à Alt gauche ou Super gauche.\n\n"
        "| Touche | Action |\n|---|---|\n"
        "| MOD+F | Basculer en plein écran |\n"
        "| MOD+G | Taille 1:1 |\n"
        "| MOD+W | Ajuster pour supprimer les bandes noires |\n"
        "| MOD+←/→ | Pivoter l'affichage |\n\n"
        "## Dépannage\n\n"
        "- **Casque injoignable** : il est en veille, sur un autre réseau, ou a redémarré "
        "(refais l'assistant avec le câble).\n"
        "- **Image décentrée ou penchée** : ouvre *Réglages d'affichage* (D), appuie sur V "
        "pour voir toute l'image, place le rectangle sur l'œil, puis rappuie sur V. "
        "Recadrage et angle sont liés.\n"
        "- **Pas de son** : la capture audio nécessite Android 11+ sur le casque ; essaie "
        "*PC uniquement*.\n"
        "- **Vidéo saccadée** : baisse le débit ou les IPS max, ou rapproche-toi de la box.\n"
        "- Pour couper l'ADB Wi-Fi sans redémarrer, lance `adb usb` câble branché."
    ),
}

STRINGS = {"en": EN, "fr": FR}


def detect_language() -> str:
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var)
        if value:
            return "fr" if value.lower().startswith("fr") else "en"
    try:
        # Windows returns names like "French_France" here, POSIX "fr_FR".
        name = locale.getlocale()[0] or ""
    except ValueError:
        name = ""
    return "fr" if name.lower().startswith("fr") else "en"


def set_language(lang: str) -> None:
    global _lang
    _lang = lang if lang in STRINGS else "en"


def get_language() -> str:
    return _lang


def t(key: str, **kwargs: object) -> str:
    text = STRINGS[_lang].get(key) or EN[key]
    return text.format(**kwargs) if kwargs else text
