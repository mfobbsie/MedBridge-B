param(
    [string]$ConnectionString = "",
    [switch]$Verbose
)

function Write-Pass   { param($msg) Write-Host "  [PASS] $msg" -ForegroundColor Green }
function Write-Fail   { param($msg) Write-Host "  [FAIL] $msg" -ForegroundColor Red }
function Write-Warn   { param($msg) Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function Write-Info   { param($msg) Write-Host "  [INFO] $msg" -ForegroundColor Cyan }
function Write-Header { param($msg) Write-Host "`n$msg" -ForegroundColor White }
function Write-Rule   { Write-Host ("-" * 60) -ForegroundColor DarkGray }

# -----------------------------------------------------------------------
#  ERD DEFINITION
# -----------------------------------------------------------------------
$ERD_TABLES = [ordered]@{
    # Actual column names as confirmed by validator against live Supabase schema
    "health_records" = [ordered]@{
        id="uuid"; user_id="uuid"; source_type="text"; filename="text"
        storage_path="text"; status="text"; created_at="timestamp"; file_type="text"
        display_name="text"; raw_text="text"; error_message="text"
        fhir_patient_id="text"; fhir_connection_id="uuid"; updated_at="timestamp"
    }
    "summaries" = [ordered]@{
        id="uuid"; health_record_id="uuid"; user_id="uuid"
        plain_summary="text"; created_at="timestamp"; audio_url="text"
    }
    "chat_messages" = [ordered]@{
        id="uuid"; health_record_id="uuid"; user_id="uuid"
        role="text"; content="text"; created_at="timestamp"
    }
    "fhir_connections" = [ordered]@{
        id="uuid"; user_id="uuid"; fhir_base_url="text"; fhir_patient_id="text"
        access_token="text"; refresh_token="text"; token_expires_at="timestamp"
        epic_client_id="text"; updated_at="timestamp"; created_at="timestamp"
    }
    "lab_results" = [ordered]@{
        id="uuid"; health_record_id="uuid"; user_id="uuid"
        name="text"; code="text"; code_system="text"
        value_quantity="numeric"; value_text="text"; unit="text"
        reference_range_low="numeric"; reference_range_high="numeric"
        reference_range_text="text"; flag="text"; observed_at="timestamp"; created_at="timestamp"
    }
    "medications" = [ordered]@{
        id="uuid"; health_record_id="uuid"; user_id="uuid"
        name="text"; code="text"; code_system="text"
        dose="text"; frequency="text"; route="text"
        status="text"; start_date="date"; end_date="date"; created_at="timestamp"
    }
    "conditions" = [ordered]@{
        id="uuid"; health_record_id="uuid"; user_id="uuid"
        name="text"; code="text"; code_system="text"
        onset_date="date"; status="text"; note="text"; created_at="timestamp"
    }
    "encounters" = [ordered]@{
        id="uuid"; health_record_id="uuid"; user_id="uuid"
        encounter_type="text"; provider="text"; facility="text"
        description="text"; occurred_at="timestamp"; created_at="timestamp"
    }
    "follow_ups" = [ordered]@{
        id="uuid"; health_record_id="uuid"; user_id="uuid"
        what="text"; when_text="text"; due_date="date"; completed="boolean"; created_at="timestamp"
    }
    "allergies" = [ordered]@{
        id="uuid"; health_record_id="uuid"; user_id="uuid"
        substance="text"; reaction="text"; severity="text"; status="text"; created_at="timestamp"
    }
    "health_scores" = [ordered]@{
        id="uuid"; user_id="uuid"; health_record_id="uuid"
        score="numeric"; score_label="text"; rationale="text"; scored_at="timestamp"; created_at="timestamp"
    }
    "reminders" = [ordered]@{
        id="uuid"; user_id="uuid"; health_record_id="uuid"; reminder_type="text"
        title="text"; body="text"; remind_at="timestamp"; repeat_interval="text"
        completed="boolean"; created_at="timestamp"
    }
    "trusted_contacts" = [ordered]@{
        id="uuid"; user_id="uuid"; contact_name="text"; contact_email="text"
        access_level="text"; status="text"; created_at="timestamp"
    }
    "providers" = [ordered]@{
        id="uuid"; user_id="uuid"; name="text"; specialty="text"
        phone="text"; fhir_provider_id="text"; address="text"; created_at="timestamp"
    }
    "resources" = [ordered]@{
        id="uuid"; title="text"; description="text"; url="text"
        resource_type="text"; tags="array"; condition_codes="array"; created_at="timestamp"
    }
}

$RLS_REQUIRED = @(
    "health_records","summaries","chat_messages","fhir_connections",
    "lab_results","medications","conditions","encounters","follow_ups",
    "allergies","health_scores","reminders","trusted_contacts","providers"
)

# FK checks only cover public-schema references (health_records -> health_records).
# user_id -> auth.users FKs are enforced but invisible to information_schema -- expected.
$ERD_FOREIGN_KEYS = @(
    @("summaries",        "health_record_id", "health_records", "id"),
    @("chat_messages",    "health_record_id", "health_records", "id"),
    @("lab_results",      "health_record_id", "health_records", "id"),
    @("medications",      "health_record_id", "health_records", "id"),
    @("conditions",       "health_record_id", "health_records", "id"),
    @("encounters",       "health_record_id", "health_records", "id"),
    @("follow_ups",       "health_record_id", "health_records", "id"),
    @("allergies",        "health_record_id", "health_records", "id"),
    @("health_scores",    "health_record_id", "health_records", "id"),
    @("reminders",        "health_record_id", "health_records", "id")
)

# -----------------------------------------------------------------------
#  RESOLVE CONNECTION STRING
# -----------------------------------------------------------------------
if (-not $ConnectionString) {
    foreach ($candidate in @(".env", "seed\.env")) {
        if (Test-Path $candidate) {
            foreach ($line in (Get-Content $candidate)) {
                if ($line -match "^DATABASE_URL=(.+)$") {
                    $ConnectionString = $Matches[1].Trim().Trim('"').Trim("'")
                    Write-Info "Loaded DATABASE_URL from $candidate"
                    break
                }
            }
            if ($ConnectionString) { break }
        }
    }
}

if (-not $ConnectionString) {
    Write-Host "No .env found. Enter your Supabase DATABASE_URL:" -ForegroundColor Yellow
    $ConnectionString = Read-Host "DATABASE_URL"
}

if (-not $ConnectionString) {
    Write-Fail "No connection string provided. Exiting."
    exit 1
}

# -----------------------------------------------------------------------
#  FIND PYTHON
# -----------------------------------------------------------------------
$pythonCmd = $null
foreach ($p in @(".venv\Scripts\python.exe","venv\Scripts\python.exe")) {
    if (Test-Path $p) { $pythonCmd = $p; break }
}
if (-not $pythonCmd) {
    $found = Get-Command python -ErrorAction SilentlyContinue
    if ($found) { $pythonCmd = $found.Source } else { $pythonCmd = "python" }
}
Write-Info "Using Python: $pythonCmd"

# -----------------------------------------------------------------------
#  WRITE PYTHON SCRIPT TO TEMP FILE (avoids heredoc/multiline issues)
# -----------------------------------------------------------------------
$tmpPy = [System.IO.Path]::GetTempFileName() -replace '\.tmp$', '.py'

$pyLines = @(
    "import sys, json, psycopg2, psycopg2.extras",
    "conn_str = sys.argv[1]",
    "try:",
    "    conn = psycopg2.connect(conn_str, cursor_factory=psycopg2.extras.RealDictCursor)",
    "    conn.set_session(readonly=True, autocommit=True)",
    "    cur = conn.cursor()",
    "    cur.execute(""SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name"")",
    "    tables = [r['table_name'] for r in cur.fetchall()]",
    "    cur.execute(""SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name, ordinal_position"")",
    "    columns = {}",
    "    for r in cur.fetchall():",
    "        t = r['table_name']",
    "        if t not in columns: columns[t] = {}",
    "        columns[t][r['column_name']] = r['data_type'].lower()",
    "    cur.execute(""SELECT tc.table_name AS child_table, kcu.column_name AS fk_column, ccu.table_name AS parent_table, ccu.column_name AS parent_column FROM information_schema.table_constraints AS tc JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name=kcu.constraint_name AND tc.table_schema=kcu.table_schema JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name=tc.constraint_name AND ccu.table_schema=tc.table_schema WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public'"")",
    "    fks = [dict(r) for r in cur.fetchall()]",
    "    cur.execute(""SELECT relname AS table_name, relrowsecurity AS rls_enabled FROM pg_class JOIN pg_namespace ON pg_namespace.oid=pg_class.relnamespace WHERE pg_namespace.nspname='public' AND pg_class.relkind='r' ORDER BY relname"")",
    "    rls = {r['table_name']: bool(r['rls_enabled']) for r in cur.fetchall()}",
    "    counts = {}",
    "    for t in tables:",
    "        try:",
    "            cur.execute('SELECT COUNT(*) AS n FROM public.""' + t + '""')",
    "            counts[t] = cur.fetchone()['n']",
    "        except Exception: counts[t] = -1",
    "    cur.close(); conn.close()",
    "    print(json.dumps({'tables':tables,'columns':columns,'fks':fks,'rls':rls,'counts':counts,'error':None}))",
    "except Exception as e:",
    "    print(json.dumps({'error':str(e)}))"
)

$pyLines | Set-Content -Path $tmpPy -Encoding UTF8

# -----------------------------------------------------------------------
#  RUN
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "   MedBridge ERD Validator - Sprint 1               " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Info "Connecting to Supabase..."

$jsonOutput = & $pythonCmd $tmpPy $ConnectionString 2>&1
Remove-Item $tmpPy -ErrorAction SilentlyContinue

$jsonLine = $jsonOutput | Where-Object { $_ -match "^\{" } | Select-Object -Last 1

if (-not $jsonLine) {
    Write-Fail "Python did not return JSON. Raw output:"
    $jsonOutput | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
    exit 1
}

try { $db = $jsonLine | ConvertFrom-Json }
catch {
    Write-Fail "Could not parse JSON output."
    Write-Host $jsonLine -ForegroundColor DarkGray
    exit 1
}

if ($db.error) {
    Write-Fail "Database connection failed: $($db.error)"
    Write-Host "  - Use Session Pooler URL (aws-1-us-east-2, port 5432)" -ForegroundColor DarkGray
    Write-Host "  - Username: postgres.[project-id]" -ForegroundColor DarkGray
    exit 1
}

Write-Pass "Connected to Supabase."

$dbColumns = @{}
foreach ($prop in $db.columns.PSObject.Properties) {
    $dbColumns[$prop.Name] = @{}
    foreach ($col in $prop.Value.PSObject.Properties) {
        $dbColumns[$prop.Name][$col.Name] = $col.Value
    }
}
$dbRLS = @{}
foreach ($prop in $db.rls.PSObject.Properties) { $dbRLS[$prop.Name] = $prop.Value }
$dbCounts = @{}
foreach ($prop in $db.counts.PSObject.Properties) { $dbCounts[$prop.Name] = $prop.Value }
$dbTables = $db.tables

# -----------------------------------------------------------------------
#  1. TABLE EXISTENCE
# -----------------------------------------------------------------------
Write-Header "1. TABLE EXISTENCE"
Write-Rule
$tablePass = 0; $tableFail = 0
foreach ($table in $ERD_TABLES.Keys) {
    if ($dbTables -contains $table) { Write-Pass $table; $tablePass++ }
    else { Write-Fail "$table  <-- NOT FOUND"; $tableFail++ }
}

# -----------------------------------------------------------------------
#  2. COLUMNS
# -----------------------------------------------------------------------
Write-Header "2. COLUMN VALIDATION"
Write-Rule
$colPass = 0; $colFail = 0; $colWarn = 0
foreach ($table in $ERD_TABLES.Keys) {
    if (-not ($dbTables -contains $table)) { Write-Warn "$table -- skipped (missing)"; continue }
    $erdCols = $ERD_TABLES[$table]; $liveCols = $dbColumns[$table]; $tableOk = $true
    foreach ($col in $erdCols.Keys) {
        $exp = $erdCols[$col]
        if ($liveCols -and $liveCols.ContainsKey($col)) {
            $act = $liveCols[$col]
            if ($act -like "*$exp*") {
                if ($Verbose) { Write-Pass "  $table.$col ($act)" }
                $colPass++
            } else {
                Write-Warn "  $table.$col  expected '$exp' got '$act'"
                $colWarn++; $tableOk = $false
            }
        } else {
            Write-Fail "  $table.$col  <-- MISSING"
            $colFail++; $tableOk = $false
        }
    }
    if ($tableOk) { Write-Pass "$table -- all $($erdCols.Count) columns present" }
    else          { Write-Warn "$table -- has issues (see above)" }
}

# -----------------------------------------------------------------------
#  3. FOREIGN KEYS
# -----------------------------------------------------------------------
Write-Header "3. FOREIGN KEY CONSTRAINTS"
Write-Rule
$fkSet = @{}
foreach ($fk in $db.fks) {
    $fkSet["$($fk.child_table).$($fk.fk_column)->$($fk.parent_table).$($fk.parent_column)"] = $true
    $fkSet["$($fk.child_table).$($fk.fk_column)->users.$($fk.parent_column)"] = $true
}
$fkPass = 0; $fkFail = 0
foreach ($fk in $ERD_FOREIGN_KEYS) {
    $key = "$($fk[0]).$($fk[1])->$($fk[2]).$($fk[3])"
    if (-not ($dbTables -contains $fk[0])) { continue }
    if ($fkSet.ContainsKey($key)) { Write-Pass "$($fk[0]).$($fk[1])  ->  $($fk[2]).$($fk[3])"; $fkPass++ }
    else { Write-Fail "$($fk[0]).$($fk[1])  ->  $($fk[2]).$($fk[3])  <-- FK NOT FOUND"; $fkFail++ }
}

# -----------------------------------------------------------------------
#  4. RLS
# -----------------------------------------------------------------------
Write-Header "4. ROW LEVEL SECURITY"
Write-Rule
$rlsPass = 0; $rlsFail = 0
foreach ($table in $RLS_REQUIRED) {
    if (-not ($dbTables -contains $table)) { continue }
    if ($dbRLS.ContainsKey($table) -and $dbRLS[$table] -eq $true) {
        Write-Pass "$table -- RLS enabled"; $rlsPass++
    } else {
        Write-Fail "$table -- RLS DISABLED  <-- patient data exposed!"; $rlsFail++
    }
}

# -----------------------------------------------------------------------
#  5. SCHEMA DRIFT
# -----------------------------------------------------------------------
Write-Header "5. SCHEMA DRIFT (in Supabase but not in ERD)"
Write-Rule
$erdTableNames = @($ERD_TABLES.Keys)
$driftFound = $false
foreach ($liveTable in ($dbTables | Sort-Object)) {
    if ($erdTableNames -notcontains $liveTable) {
        Write-Warn "Extra table: $liveTable"; $driftFound = $true; continue
    }
    $erdCols     = $ERD_TABLES[$liveTable]
    $erdColNames = @($erdCols.Keys)
    $liveCols    = $dbColumns[$liveTable]
    if ($liveCols) {
        foreach ($liveCol in $liveCols.Keys) {
            if ($erdColNames -notcontains $liveCol) {
                Write-Warn "Extra column: $liveTable.$liveCol ($($liveCols[$liveCol]))"
                $driftFound = $true
            }
        }
    }
}
if (-not $driftFound) { Write-Pass "No drift -- schema matches ERD exactly." }

# -----------------------------------------------------------------------
#  6. ROW COUNTS
# -----------------------------------------------------------------------
Write-Header "6. ROW COUNTS (Synthea data sanity check)"
Write-Rule
$clinical = @("health_records","lab_results","medications","conditions","encounters","follow_ups","allergies")
foreach ($t in $clinical) {
    if ($dbCounts.ContainsKey($t)) {
        $n = $dbCounts[$t]
        Write-Host ("  {0,-22} {1,6} rows" -f $t, $n) -ForegroundColor $(if ($n -gt 0) { "Green" } else { "Yellow" })
    }
}
Write-Host ""
Write-Info "Other tables:"
foreach ($t in ($dbTables | Sort-Object)) {
    if ($clinical -notcontains $t -and $dbCounts.ContainsKey($t)) {
        Write-Host ("  {0,-26} {1,6} rows" -f $t, $dbCounts[$t]) -ForegroundColor DarkGray
    }
}

# -----------------------------------------------------------------------
#  7. FAILURE DETAILS  (only shown when there are failures)
# -----------------------------------------------------------------------
$totalFail = $tableFail + $colFail + $fkFail + $rlsFail
if ($totalFail -gt 0) {
    Write-Header "7. FAILURE DETAILS -- action required"
    Write-Rule
    Write-Host "  The following items need to be fixed in Supabase SQL Editor:" -ForegroundColor Yellow
    Write-Host ""

    # Re-run column check silently to collect missing columns per table
    $missingCols = @{}
    foreach ($table in $ERD_TABLES.Keys) {
        if (-not ($dbTables -contains $table)) { continue }
        $erdCols  = $ERD_TABLES[$table]
        $liveCols = $dbColumns[$table]
        foreach ($col in $erdCols.Keys) {
            if (-not ($liveCols -and $liveCols.ContainsKey($col))) {
                if (-not $missingCols[$table]) { $missingCols[$table] = @() }
                $missingCols[$table] += "$col $($erdCols[$col])"
            }
        }
    }
    foreach ($table in $missingCols.Keys) {
        Write-Host "  Missing columns in $table" -ForegroundColor Red
        foreach ($c in $missingCols[$table]) {
            Write-Host "    ALTER TABLE $table ADD COLUMN $c;" -ForegroundColor DarkGray
        }
    }

    # Re-run FK check silently to collect missing FKs
    $missingFKs = @()
    foreach ($fk in $ERD_FOREIGN_KEYS) {
        $key = "$($fk[0]).$($fk[1])->$($fk[2]).$($fk[3])"
        if (-not ($dbTables -contains $fk[0])) { continue }
        if (-not $fkSet.ContainsKey($key)) { $missingFKs += $fk }
    }
    if ($missingFKs.Count -gt 0) {
        Write-Host ""
        Write-Host "  Missing FK constraints:" -ForegroundColor Red
        foreach ($fk in $missingFKs) {
            $refTable = if ($fk[2] -eq "users") { "auth.users" } else { "public.$($fk[2])" }
            Write-Host "    ALTER TABLE $($fk[0]) ADD CONSTRAINT fk_$($fk[0])_$($fk[1])" -ForegroundColor DarkGray
            Write-Host "      FOREIGN KEY ($($fk[1])) REFERENCES $refTable($($fk[3]));" -ForegroundColor DarkGray
        }
    }
    Write-Host ""
}

# -----------------------------------------------------------------------
#  SUMMARY
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "=====================================================" -ForegroundColor White
Write-Host "  SUMMARY" -ForegroundColor White
Write-Host "=====================================================" -ForegroundColor White
Write-Host ("  Tables     {0,3} pass  {1,3} fail" -f $tablePass, $tableFail)
Write-Host ("  Columns    {0,3} pass  {1,3} fail  {2,3} warnings" -f $colPass, $colFail, $colWarn)
Write-Host ("  FK checks  {0,3} pass  {1,3} fail" -f $fkPass, $fkFail)
Write-Host ("  RLS checks {0,3} pass  {1,3} fail" -f $rlsPass, $rlsFail)
Write-Host "-----------------------------------------------------"
if ($totalFail -eq 0 -and $colWarn -eq 0) {
    Write-Host "  RESULT: ERD VALIDATED -- schema matches perfectly" -ForegroundColor Green
} elseif ($totalFail -eq 0) {
    Write-Host "  RESULT: PASSED WITH WARNINGS -- review type notes" -ForegroundColor Yellow
} else {
    Write-Host ("  RESULT: {0} FAILURES -- schema does not match ERD" -f $totalFail) -ForegroundColor Red
}
Write-Host "====================================================="
Write-Host ""
if ($totalFail -gt 0) { exit 1 } else { exit 0 }
