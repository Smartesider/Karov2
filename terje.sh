#!/bin/bash
set -euo pipefail

TXT_LOG="/var/log/skyserver_audit.txt"
JSON_LOG="/var/log/skyserver_audit.json"
TMP_JSON="/tmp/audit_tmp.json"

echo "📋 Starter sikkerhets- og endringsanalyse..." | tee "$TXT_LOG"
echo '{' > "$JSON_LOG"

# Del 1: PHP-relatert
echo "▶️ PHP-config-endringer:" | tee -a "$TXT_LOG"
find /etc/php/ -name php.ini -exec ls -lah {} \; >> "$TXT_LOG"
find /etc/php/ -name "*php.ini*" -exec sha256sum {} \; >> "$TXT_LOG"
echo '"php_ini_files": [' >> "$JSON_LOG"
find /etc/php/ -name php.ini -exec echo "\"{}\",\n" \; >> "$JSON_LOG"
echo '],' >> "$JSON_LOG"

# Del 2: Sjekk apache og nginx
echo "▶️ Webtjenester (Apache/Nginx):" | tee -a "$TXT_LOG"
systemctl is-active apache2 >/dev/null && echo "❌ Apache kjører!" | tee -a "$TXT_LOG"
systemctl is-active nginx >/dev/null && echo "✅ NGINX kjører som forventet." | tee -a "$TXT_LOG"
echo '"web_services": {' >> "$JSON_LOG"
echo "\"apache2\": \"$(systemctl is-active apache2 || echo not-found)\"," >> "$JSON_LOG"
echo "\"nginx\": \"$(systemctl is-active nginx || echo not-found)\"" >> "$JSON_LOG"
echo "}," >> "$JSON_LOG"

# Del 3: SSH og rootbeskyttelse
echo "▶️ SSH-konfig og rootbeskyttelse:" | tee -a "$TXT_LOG"
grep -Ei 'PermitRootLogin|PasswordAuthentication' /etc/ssh/sshd_config | tee -a "$TXT_LOG"
echo '"ssh_config": {' >> "$JSON_LOG"
echo "\"PermitRootLogin\": \"$(grep -Ei 'PermitRootLogin' /etc/ssh/sshd_config | awk '{print $2}')\"," >> "$JSON_LOG"
echo "\"PasswordAuthentication\": \"$(grep -Ei 'PasswordAuthentication' /etc/ssh/sshd_config | awk '{print $2}')\"" >> "$JSON_LOG"
echo "}," >> "$JSON_LOG"

# Del 4: Lyttende porter
echo "▶️ Aktive nettverkstjenester:" | tee -a "$TXT_LOG"
ss -tulpn | grep LISTEN | tee -a "$TXT_LOG"
echo '"open_ports": [' >> "$JSON_LOG"
ss -tulpn | grep LISTEN | awk '{print $5}' | sed 's/.*://g' | sort -u | sed 's/^/"/;s/$/",/' >> "$JSON_LOG"
echo '],' >> "$JSON_LOG"

# Del 5: Brukere med sudo-tilgang
echo "▶️ Brukere med sudo/root-rettigheter:" | tee -a "$TXT_LOG"
getent group sudo | cut -d: -f4 | tee -a "$TXT_LOG"
echo '"sudo_users": [' >> "$JSON_LOG"
getent group sudo | cut -d: -f4 | sed 's/,/","/g; s/^/"/; s/$/"/' >> "$JSON_LOG"
echo '],' >> "$JSON_LOG"

# Del 6: World-writable + setuid-filer (ekskluderer /proc /sys /dev)
echo "▶️ World-writable og setuid-filer (potensiell risiko):" | tee -a "$TXT_LOG"
find / \( -path /proc -o -path /sys -o -path /dev \) -prune -o -type f -perm -0002 -exec ls -lh {} \; 2>/dev/null | tee -a "$TXT_LOG"
find / \( -path /proc -o -path /sys -o -path /dev \) -prune -o -type f -perm -4000 -print 2>/dev/null | tee -a "$TXT_LOG"
echo '"dangerous_permissions": "summarized in txt log",' >> "$JSON_LOG"

# Del 7: Aktive tjenester og automatisk oppstart
echo "▶️ Aktive og aktiverte tjenester:" | tee -a "$TXT_LOG"
systemctl list-unit-files --state=enabled | grep service | tee -a "$TXT_LOG"
echo '"enabled_services_count": '$(systemctl list-unit-files --state=enabled | grep service | wc -l)',' >> "$JSON_LOG"

# Del 8: Andre ting skyserver har satt opp
echo "▶️ Overvåking og backup-verktøy:" | tee -a "$TXT_LOG"
for tool in monit logrotate etckeeper rclone netdata; do
  if command -v "$tool" >/dev/null; then
    echo "✅ $tool er installert." | tee -a "$TXT_LOG"
  else
    echo "❌ $tool mangler!" | tee -a "$TXT_LOG"
  fi
done
echo '"tools_installed": [' >> "$JSON_LOG"
for tool in monit logrotate etckeeper rclone netdata; do
  command -v "$tool" >/dev/null && echo "\"$tool\"," >> "$JSON_LOG"
done
echo '],' >> "$JSON_LOG"

# Sluttsignatur
echo '"audit_completed": "'$(date)'"' >> "$JSON_LOG"
echo '}' >> "$JSON_LOG"
echo "✅ Sikkerhetsanalyse fullført. Rapporter ligger i:"
echo " - $TXT_LOG"
echo " - $JSON_LOG"
