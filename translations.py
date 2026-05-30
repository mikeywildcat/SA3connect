"""UI string translations for SA3 NMEA Relay.

Supported languages:
    en  – English (default)
    fr  – French
    de  – German
    nl  – Dutch (Netherlands)

Usage:
    from translations import set_language, tr
    set_language("fr")
    label = tr("connect")       # → "Connecter"
"""

from __future__ import annotations

_STRINGS: dict[str, dict[str, str]] = {
    # ---- Window / general ----
    "app_title": {
        "en": "SA3 NMEA Relay",
        "fr": "SA3 NMEA Relay",
        "de": "SA3 NMEA Relay",
        "nl": "SA3 NMEA Relay",
    },
    "language_label": {
        "en": "Language",
        "fr": "Langue",
        "de": "Sprache",
        "nl": "Taal",
    },

    # ---- Tabs ----
    "tab_connection": {
        "en": "Connection",
        "fr": "Connexion",
        "de": "Verbindung",
        "nl": "Verbinding",
    },
    "tab_tcp_relay": {
        "en": "TCP Relay",
        "fr": "Relais TCP",
        "de": "TCP-Weiterleitung",
        "nl": "TCP-doorstuur",
    },

    # ---- Connection tab ----
    "host_label": {
        "en": "Host",
        "fr": "Hôte",
        "de": "Host",
        "nl": "Host",
    },
    "port_label": {
        "en": "Port",
        "fr": "Port",
        "de": "Port",
        "nl": "Poort",
    },
    "btn_connect": {
        "en": "Connect",
        "fr": "Connecter",
        "de": "Verbinden",
        "nl": "Verbinden",
    },
    "btn_disconnect": {
        "en": "Disconnect",
        "fr": "Déconnecter",
        "de": "Trennen",
        "nl": "Verbreken",
    },
    "btn_clear_history": {
        "en": "Clear History",
        "fr": "Effacer l'historique",
        "de": "Verlauf löschen",
        "nl": "Geschiedenis wissen",
    },
    "auto_connect": {
        "en": "Auto Connect",
        "fr": "Connexion auto",
        "de": "Auto-Verbinden",
        "nl": "Auto-verbinden",
    },
    "auto_connect_on": {
        "en": "Auto Connect ON",
        "fr": "Connexion auto ACTIVÉE",
        "de": "Auto-Verbinden EIN",
        "nl": "Auto-verbinden AAN",
    },
    "auto_connect_tooltip": {
        "en": "Automatically connects to the last host/port on startup.",
        "fr": "Se connecte automatiquement au dernier hôte/port au démarrage.",
        "de": "Verbindet beim Start automatisch mit dem letzten Host/Port.",
        "nl": "Maakt automatisch verbinding met de laatste host/poort bij opstarten.",
    },
    "connection_help": {
        "en": (
            "<div style='font-size: 11px; line-height: 1.4; text-align: center;'>"
            "Enable the NMEA Gateway in Sailaway 3:<br/>"
            "Settings → NMEA Gateway → Activate NMEA.<br/>"
            "Default port: <b>10110</b>. Use <b>127.0.0.1</b> if<br/>"
            "Sailaway runs on the same machine.<br/>"
            "Recommended interval: 500 ms."
            "</div>"
        ),
        "fr": (
            "<div style='font-size: 11px; line-height: 1.4; text-align: center;'>"
            "Activez la passerelle NMEA dans Sailaway 3 :<br/>"
            "Paramètres → Passerelle NMEA → Activer NMEA.<br/>"
            "Port par défaut : <b>10110</b>. Utilisez <b>127.0.0.1</b> si<br/>"
            "Sailaway tourne sur la même machine.<br/>"
            "Intervalle recommandé : 500 ms."
            "</div>"
        ),
        "de": (
            "<div style='font-size: 11px; line-height: 1.4; text-align: center;'>"
            "NMEA-Gateway in Sailaway 3 aktivieren:<br/>"
            "Einstellungen → NMEA-Gateway → NMEA aktivieren.<br/>"
            "Standardport: <b>10110</b>. <b>127.0.0.1</b> verwenden, wenn<br/>"
            "Sailaway auf demselben Rechner läuft.<br/>"
            "Empfohlenes Intervall: 500 ms."
            "</div>"
        ),
        "nl": (
            "<div style='font-size: 11px; line-height: 1.4; text-align: center;'>"
            "Activeer de NMEA-gateway in Sailaway 3:<br/>"
            "Instellingen → NMEA-gateway → NMEA activeren.<br/>"
            "Standaardpoort: <b>10110</b>. Gebruik <b>127.0.0.1</b> als<br/>"
            "Sailaway op dezelfde computer draait.<br/>"
            "Aanbevolen interval: 500 ms."
            "</div>"
        ),
    },

    # ---- Connection status ----
    "status_disconnected": {
        "en": "Disconnected",
        "fr": "Déconnecté",
        "de": "Getrennt",
        "nl": "Verbroken",
    },
    "status_connecting": {
        "en": "Connecting to {host}:{port}…",
        "fr": "Connexion à {host}:{port}…",
        "de": "Verbinde mit {host}:{port}…",
        "nl": "Verbinden met {host}:{port}…",
    },
    "status_connected": {
        "en": "Connected  {host}:{port}",
        "fr": "Connecté  {host}:{port}",
        "de": "Verbunden  {host}:{port}",
        "nl": "Verbonden  {host}:{port}",
    },
    "status_error": {
        "en": "Error: {msg}",
        "fr": "Erreur : {msg}",
        "de": "Fehler: {msg}",
        "nl": "Fout: {msg}",
    },
    "log_connected": {
        "en": "# Connected to {host}:{port}",
        "fr": "# Connecté à {host}:{port}",
        "de": "# Verbunden mit {host}:{port}",
        "nl": "# Verbonden met {host}:{port}",
    },
    "log_disconnected": {
        "en": "# Disconnected",
        "fr": "# Déconnecté",
        "de": "# Getrennt",
        "nl": "# Verbroken",
    },
    "conn_lost_title": {
        "en": "Connection Lost",
        "fr": "Connexion perdue",
        "de": "Verbindung unterbrochen",
        "nl": "Verbinding verbroken",
    },
    "conn_lost_msg": {
        "en": "Connection lost. Please check Sailaway is running and reconnect with the Connect button.",
        "fr": "Connexion perdue. Veuillez vérifier que Sailaway est en cours d'exécution et reconnectez-vous avec le bouton Connecter.",
        "de": "Verbindung unterbrochen. Bitte prüfen Sie, ob Sailaway läuft, und stellen Sie die Verbindung mit dem Verbinden-Schaltfläche wieder her.",
        "nl": "Verbinding verbroken. Controleer of Sailaway actief is en maak opnieuw verbinding via de knop Verbinden.",
    },
    "log_error": {
        "en": "# Error: {msg}",
        "fr": "# Erreur : {msg}",
        "de": "# Fehler: {msg}",
        "nl": "# Fout: {msg}",
    },
    "log_boat_id": {
        "en": "# Boat ID detected: {bid}",
        "fr": "# ID bateau détecté : {bid}",
        "de": "# Boot-ID erkannt: {bid}",
        "nl": "# Boot-ID gedetecteerd: {bid}",
    },

    # ---- Stats bar ----
    "stat_received": {
        "en": "Received: {n}",
        "fr": "Reçus : {n}",
        "de": "Empfangen: {n}",
        "nl": "Ontvangen: {n}",
    },
    "stat_relayed": {
        "en": "Relayed: {n}",
        "fr": "Relayés : {n}",
        "de": "Weitergeleitet: {n}",
        "nl": "Doorgestuurd: {n}",
    },
    "stat_boat_id": {
        "en": "Boat ID: {bid}",
        "fr": "ID bateau : {bid}",
        "de": "Boot-ID: {bid}",
        "nl": "Boot-ID: {bid}",
    },
    "stat_boat_id_none": {
        "en": "Boat ID: –",
        "fr": "ID bateau : –",
        "de": "Boot-ID: –",
        "nl": "Boot-ID: –",
    },

    # ---- TCP Relay tab ----
    "relay_group": {
        "en": "NMEA TCP Relay",
        "fr": "Relais TCP NMEA",
        "de": "NMEA-TCP-Weiterleitung",
        "nl": "NMEA TCP-doorstuur",
    },
    "relay_listen_host": {
        "en": "Listen host:",
        "fr": "Hôte d'écoute :",
        "de": "Abhörhost:",
        "nl": "Luisterhost:",
    },
    "relay_port": {
        "en": "Port:",
        "fr": "Port :",
        "de": "Port:",
        "nl": "Poort:",
    },
    "auto_relay": {
        "en": "Auto Relay",
        "fr": "Relais auto",
        "de": "Auto-Weiterleitung",
        "nl": "Auto-doorstuur",
    },
    "auto_relay_on": {
        "en": "Auto Relay ON",
        "fr": "Relais auto ACTIVÉ",
        "de": "Auto-Weiterleitung EIN",
        "nl": "Auto-doorstuur AAN",
    },
    "auto_relay_tooltip": {
        "en": "Automatically starts the TCP relay on startup using the last saved settings.",
        "fr": "Démarre automatiquement le relais TCP au démarrage avec les derniers paramètres.",
        "de": "Startet die TCP-Weiterleitung beim Start automatisch mit den zuletzt gespeicherten Einstellungen.",
        "nl": "Start automatisch de TCP-doorstuur bij het opstarten met de laatste instellingen.",
    },
    "btn_start_relay": {
        "en": "Start TCP Relay",
        "fr": "Démarrer le relais TCP",
        "de": "TCP-Weiterleitung starten",
        "nl": "TCP-doorstuur starten",
    },
    "btn_stop_relay": {
        "en": "Stop TCP Relay",
        "fr": "Arrêter le relais TCP",
        "de": "TCP-Weiterleitung stoppen",
        "nl": "TCP-doorstuur stoppen",
    },
    "relay_inactive": {
        "en": "Relay inactive",
        "fr": "Relais inactif",
        "de": "Weiterleitung inaktiv",
        "nl": "Doorstuur inactief",
    },
    "relay_stopped": {
        "en": "Relay stopped",
        "fr": "Relais arrêté",
        "de": "Weiterleitung gestoppt",
        "nl": "Doorstuur gestopt",
    },
    "relay_clients": {
        "en": "Clients: {n}",
        "fr": "Clients : {n}",
        "de": "Clients: {n}",
        "nl": "Clients: {n}",
    },
    "relay_help": {
        "en": (
            "<div style='font-size: 10px; line-height: 1.4; text-align: center;'>"
            "Broadcasts corrected NMEA to other navigation apps.<br/>"
            "Connect OpenCPN, qtVlm, etc. to this port.<br/>"
            "Use <b>0.0.0.0</b> to listen on all network interfaces<br/>"
            "or <b>127.0.0.1</b> for local-only access.<br/><br/>"
            "<b>Corrections applied:</b><br/>"
            "• $SLCLI → $IIXDR (heel/roll, sign inverted)<br/>"
            "• $RIRSA → $IIRSA (rudder angle)<br/>"
            "• $WIMWV angle wrap (&gt;180° → signed)<br/>"
            "• Own-boat AIS sentences filtered out"
            "</div>"
        ),
        "fr": (
            "<div style='font-size: 10px; line-height: 1.4; text-align: center;'>"
            "Diffuse le NMEA corrigé vers d'autres applications de navigation.<br/>"
            "Connectez OpenCPN, qtVlm, etc. à ce port.<br/>"
            "Utilisez <b>0.0.0.0</b> pour toutes les interfaces réseau<br/>"
            "ou <b>127.0.0.1</b> pour un accès local uniquement.<br/><br/>"
            "<b>Corrections appliquées :</b><br/>"
            "• $SLCLI → $IIXDR (gîte/roulis, signe inversé)<br/>"
            "• $RIRSA → $IIRSA (angle de barre)<br/>"
            "• $WIMWV correction d'angle (&gt;180° → signé)<br/>"
            "• Phrases AIS du propre bateau filtrées"
            "</div>"
        ),
        "de": (
            "<div style='font-size: 10px; line-height: 1.4; text-align: center;'>"
            "Sendet korrigierte NMEA-Sätze an andere Navigations-Apps.<br/>"
            "OpenCPN, qtVlm usw. mit diesem Port verbinden.<br/>"
            "<b>0.0.0.0</b> für alle Netzwerkschnittstellen<br/>"
            "oder <b>127.0.0.1</b> nur für lokalen Zugriff.<br/><br/>"
            "<b>Angewandte Korrekturen:</b><br/>"
            "• $SLCLI → $IIXDR (Krängung/Rollen, Vorzeichen invertiert)<br/>"
            "• $RIRSA → $IIRSA (Ruderwinkel)<br/>"
            "• $WIMWV Winkelkorrektur (&gt;180° → vorzeichenbehaftet)<br/>"
            "• Eigene AIS-Sätze werden herausgefiltert"
            "</div>"
        ),
        "nl": (
            "<div style='font-size: 10px; line-height: 1.4; text-align: center;'>"
            "Stuurt gecorrigeerde NMEA door naar andere navigatie-apps.<br/>"
            "Verbind OpenCPN, qtVlm, enz. met deze poort.<br/>"
            "Gebruik <b>0.0.0.0</b> voor alle netwerkinterfaces<br/>"
            "of <b>127.0.0.1</b> voor alleen lokale toegang.<br/><br/>"
            "<b>Toegepaste correcties:</b><br/>"
            "• $SLCLI → $IIXDR (slagzij/rol, teken omgekeerd)<br/>"
            "• $RIRSA → $IIRSA (roerhoek)<br/>"
            "• $WIMWV hoekwrap (&gt;180° → getekend)<br/>"
            "• Eigen AIS-zinnen worden gefilterd"
            "</div>"
        ),
    },

    # ---- Tray menu ----
    "tray_hide": {
        "en": "Hide",
        "fr": "Masquer",
        "de": "Ausblenden",
        "nl": "Verbergen",
    },
    "tray_show": {
        "en": "Show",
        "fr": "Afficher",
        "de": "Anzeigen",
        "nl": "Tonen",
    },
    "tray_start_at_login": {
        "en": "Start at Login",
        "fr": "Lancer au démarrage",
        "de": "Bei Anmeldung starten",
        "nl": "Starten bij aanmelding",
    },
    "tray_quit": {
        "en": "Quit {app}",
        "fr": "Quitter {app}",
        "de": "{app} beenden",
        "nl": "{app} afsluiten",
    },
    "tray_only_mode": {
        "en": "Menu Bar / Tray Only",
        "fr": "Barre de menu / Zone de notif. uniquement",
        "de": "Nur Menüleiste / Infobereich",
        "nl": "Alleen menubalk / systeemvak",
    },
    "tray_help": {
        "en": "Help",
        "fr": "Aide",
        "de": "Hilfe",
        "nl": "Help",
    },
    "menu_file": {
        "en": "File",
        "fr": "Fichier",
        "de": "Datei",
        "nl": "Bestand",
    },
    "menu_quit": {
        "en": "Quit",
        "fr": "Quitter",
        "de": "Beenden",
        "nl": "Afsluiten",
    },
    "menu_help": {
        "en": "Help",
        "fr": "Aide",
        "de": "Hilfe",
        "nl": "Help",
    },
    "menu_help_manual": {
        "en": "Open Manual",
        "fr": "Ouvrir le manuel",
        "de": "Handbuch öffnen",
        "nl": "Handleiding openen",
    },
    "notif_running_title": {
        "en": "SA3 NMEA Relay",
        "fr": "SA3 NMEA Relay",
        "de": "SA3 NMEA Relay",
        "nl": "SA3 NMEA Relay",
    },
    "notif_running_msg": {
        "en": "Running in the menu bar.",
        "fr": "Actif dans la barre de menu.",
        "de": "Läuft in der Menüleiste.",
        "nl": "Actief in de menubalk.",
    },
    "notif_connected_title": {
        "en": "Connected",
        "fr": "Connecté",
        "de": "Verbunden",
        "nl": "Verbonden",
    },
    "notif_connected_msg": {
        "en": "Connected to Sailaway at {host}:{port}",
        "fr": "Connecté à Sailaway sur {host}:{port}",
        "de": "Mit Sailaway verbunden: {host}:{port}",
        "nl": "Verbonden met Sailaway op {host}:{port}",
    },
}

# Active language code
_lang: str = "en"

# Language display names shown in the selector
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "fr": "Français",
    "de": "Deutsch",
    "nl": "Nederlands",
}


def set_language(lang: str) -> None:
    global _lang
    if lang in LANGUAGE_NAMES:
        _lang = lang


def get_language() -> str:
    return _lang


def tr(key: str, **kwargs) -> str:
    """Return the translated string for *key* in the current language.

    Keyword arguments are substituted using str.format().
    Falls back to English if the key or language is missing.
    """
    entry = _STRINGS.get(key, {})
    text = entry.get(_lang) or entry.get("en") or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text
