#!/usr/bin/env bash
# Auth helper para Supabase — gera cookie SSR base64-encoded para chamar
# endpoints autenticados via curl.
#
# Uso:
#   source auth-helper.sh
#   supabase_login "admin@example.com" "password"
#   curl -H "Cookie: sb-${PROJECT_REF}-auth-token=${COOKIE}" ...
#
# Variáveis usadas/exportadas:
#   SUPABASE_URL, ANON_KEY, PROJECT_REF (definir antes de chamar)
#   ACC, REF, USERID, COOKIE (exportadas após login)

supabase_login() {
  local email="$1" pass="$2"
  : "${SUPABASE_URL:?Define SUPABASE_URL}"
  : "${ANON_KEY:?Define ANON_KEY}"
  : "${PROJECT_REF:?Define PROJECT_REF (ex: kvqaqkcnluwrorefqtcl)}"

  local token_json
  token_json=$(curl -s -X POST "${SUPABASE_URL}/auth/v1/token?grant_type=password" \
    -H "apikey: ${ANON_KEY}" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${email}\",\"password\":\"${pass}\"}")

  export ACC=$(python3 -c "import sys,json;print(json.loads(sys.stdin.read())['access_token'])" <<< "$token_json")
  export REF=$(python3 -c "import sys,json;print(json.loads(sys.stdin.read())['refresh_token'])" <<< "$token_json")
  export USERID=$(python3 -c "import sys,json;print(json.loads(sys.stdin.read())['user']['id'])" <<< "$token_json")

  export COOKIE=$(python3 -c "
import base64, json, os
b = base64.b64encode(json.dumps({
    'access_token': os.environ['ACC'],
    'refresh_token': os.environ['REF'],
    'expires_at': 9999999999,
    'expires_in': 3600,
    'token_type': 'bearer',
    'user': {'id': os.environ['USERID']},
}).encode()).decode()
print('base64-' + b)
")
  echo "Logged in: ${USERID}"
}

# Exemplo de uso para gerar PDF preview e renderizar capa
# pdf_preview <USER_ID> <TYPE> <OUTPUT_PDF>
pdf_preview() {
  local target="$1" type="$2" out="$3"
  : "${PROD_URL:?Define PROD_URL}"
  curl -s "${PROD_URL}/api/admin/users/${target}/preview-pdf/${type}" \
    -H "Cookie: sb-${PROJECT_REF}-auth-token=${COOKIE}" \
    -o "$out"
  echo "$type: $(stat -f%z "$out" 2>/dev/null) bytes"
}
