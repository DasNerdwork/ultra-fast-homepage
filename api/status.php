<?php
header('Content-Type: application/json');
loadEnv(__DIR__.'/../.env');

// Domain und Token aus .env
$DOMAIN = $_ENV['DOMAIN'];
$HA_TOKEN = $_ENV['HA_TOKEN'];

// Services definieren (nur Port und/oder URL)
$services = [
    'teamspeak'     => ['port'=>10011,'url'=>null],
    'satisfactory'  => ['port'=>15777,'url'=>null],
    'gmod'          => ['port'=>27015,'url'=>null],
    'mc-vanilla'    => ['port'=>25565,'url'=>null],
    'mc-modpack'    => ['port'=>25566,'url'=>null],
    'musikbot'      => ['port'=>8087,'url'=>"https://musik.$DOMAIN"],
    'clashscout'    => ['port'=>null,'url'=>"https://clashscout.com"],
    'voidwatch'     => ['port'=>8090,'url'=>"https://voidwatch.$DOMAIN"],
    'pb-smetti'     => ['port'=>25000,'url'=>"https://smetti.$DOMAIN"],
    'pb-junky'      => ['port'=>25001,'url'=>"https://junky.$DOMAIN"],
    'pb-orphi'      => ['port'=>25002,'url'=>"https://orphi.$DOMAIN"],
    'pb-snacky'     => ['port'=>25003,'url'=>"https://snacky.$DOMAIN"],
    'nextcloud'     => ['port'=>null,'url'=>"https://cloud.$DOMAIN"],
    'homeassistant' => ['port'=>8123,'url'=>"https://home.$DOMAIN/api/"],
    'unifi'         => ['port'=>8443,'url'=>"https://unifi.$DOMAIN"],
    'pihole'        => ['port'=>88,'url'=>"https://pi.$DOMAIN"],
];

$results = [];

// --- HTTP-Services parallel mit curl_multi ---
$multi = curl_multi_init();
$handles = [];
foreach ($services as $id => $svc) {
    if (!empty($svc['url'])) {
        $ch = curl_init();
        $opts = [
            CURLOPT_URL => $svc['url'],
            CURLOPT_TIMEOUT => 2,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_FORBID_REUSE => false,
            CURLOPT_FRESH_CONNECT => false,
        ];

        // Home Assistant: Authorization Header
        if ($id === 'homeassistant') {
            $opts[CURLOPT_HTTPHEADER] = [
                "Authorization: Bearer $HA_TOKEN",
                "Content-Type: application/json"
            ];
        } else {
            $opts[CURLOPT_NOBODY] = true;
        }

        curl_setopt_array($ch, $opts);
        curl_multi_add_handle($multi, $ch);
        $handles[$id] = $ch;
    }
}

$running = null;
do { curl_multi_exec($multi, $running); usleep(1000); } while ($running > 0);

foreach ($handles as $id => $ch) {
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $results[$id]['http'] = [
        'ok' => $httpCode >= 200 && $httpCode < 400,
        'httpStatus' => $httpCode
    ];
    curl_multi_remove_handle($multi, $ch);
    curl_close($ch);
}
curl_multi_close($multi);

// --- TCP-Services ---
foreach ($services as $id => $svc) {
    if (!empty($svc['port'])) {
        $start = microtime(true);
        $fp = @stream_socket_client($DOMAIN.':'.$svc['port'], $errno, $errstr, 2);

        $ms = null; // default N/A
        $ok = false;

        if ($fp) {
            $ok = true;
            $ms = max(1, round((microtime(true) - $start) * 1000)); // mindestens 1ms
            fclose($fp);
        }

        $results[$id]['tcp'] = [
            'ok' => $ok,
            'ms' => $ms
        ];
    }
}

// --- Ampel-Status kombinieren ---
foreach ($results as $id => &$res) {
    $httpOk = $res['http']['ok'] ?? null;
    $tcpOk  = $res['tcp']['ok'] ?? null;

    if (($httpOk===true || $httpOk===null) && ($tcpOk===true || $tcpOk===null)) $res['status']='green';
    elseif (($httpOk===true) || ($tcpOk===true)) $res['status']='yellow';
    else $res['status']='red';
}
unset($res);

// --- .env laden ---
function loadEnv($path) {
    if (!file_exists($path)) return;

    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue; // Kommentar
        [$name, $value] = explode('=', $line, 2);
        $name = trim($name);
        $value = trim($value);
        if (!isset($_ENV[$name])) $_ENV[$name] = $value;
    }
}

// --- Gruppieren ---
function groupServices($results, $prefix, $labelMap = []) {
    $group = [
        'instances' => [],
        'status' => 'green'
    ];
    foreach ($results as $id => $res) {
        if (strpos($id, $prefix) === 0) {
            $name = $labelMap[$id] ?? ucfirst(str_replace($prefix.'-', '', $id));
            $group['instances'][] = [
                'name' => $name,
                'status' => $res['status']
            ];
            if ($res['status'] === 'red' && $group['status'] !== 'red') {
                $group['status'] = 'yellow'; // mind. ein Fehler
            }
        }
    }
    // Wenn alle grün → green, wenn alle rot → red, sonst gelb
    $statuses = array_column($group['instances'], 'status');
    if (count(array_unique($statuses)) === 1) {
        $group['status'] = $statuses[0];
    } elseif (in_array('red', $statuses)) {
        $group['status'] = 'yellow';
    }
    return $group;
}

// Phantombot
$results['phantombot'] = groupServices($results, 'pb', [
    'pb-smetti' => 'Smetti',
    'pb-junky'  => 'Junky',
    'pb-orphi'  => 'Orphi',
    'pb-snacky' => 'Snacky'
]);

// --- Heizölpreise einfügen ---
function fetchHeizoelPreis($minDate, $maxDate) {
    $url = "https://www.heizoel24.de/api/chartapi/GetAveragePriceHistory?countryId=1&minDate={$minDate}&maxDate={$maxDate}";
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 5,
        CURLOPT_HTTPHEADER => [
            'Origin: https://www.heizoel24.de',
            'Referer: https://www.heizoel24.de/',
            'User-Agent: Mozilla/5.0'
        ]
    ]);
    $resp = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode >= 200 && $httpCode < 300 && $resp) {
        $data = json_decode($resp, true);
        return [
            'ok' => true,
            'httpStatus' => $httpCode,
            'currentPrice' => $data['CurrentPrice'] ?? null,
            'changePercent' => $data['ChangePercent'] ?? null,
            'values' => $data['Values'] ?? []
        ];
    }
    return [
        'ok' => false,
        'httpStatus' => $httpCode,
        'error' => 'API nicht erreichbar'
    ];
}

// --- Heizölpreise abfragen (z.B. letzte 30 Tage) ---
$minDate = date('m-d-Y', strtotime('-30 days'));
$maxDate = date('m-d-Y');
$results['heizoel'] = fetchHeizoelPreis($minDate, $maxDate);

echo json_encode($results);