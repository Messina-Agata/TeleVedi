<?php

    $nome = $argv[1];
    $downloadPath = $argv[2];
    $sequenceNumber = $argv[3];
    $localPath = $argv[4];

    $downloadPath = str_replace("/", "\\", $downloadPath);

    $jsonArray = file_get_contents($localPath . "\program.json");
    $decoded_json = json_decode($jsonArray, true);
    foreach ($decoded_json as $key => $entry) {
        if ($entry["id"] == $sequenceNumber) {
            $flusso = $entry["flusso"];
            break;
        }
    }

    $flussoOrig = $flusso;

    function startFfmpegAndGetPid(string $input, string $output): ?int {
        $pid = 0;
        $command = "ffmpeg -i \"" . $input . "\" \"" . $output . "\"";
        $cmd = "start \"" . substr($input, 0, 72) . "\" cmd.exe @cmd /c " . $command; // con /c quando si ferma la registrazione si chiude anche la console; con /k invece si ferma la registrazione ma la console rimane aperta
        $handle = popen("start /B ". $cmd, "r");
        sleep(6);
        $psCommand = 'powershell -Command "& { $ffmpegPid = (Get-Process -Name ffmpeg | Sort-Object StartTime -Descending | Select-Object -First 1).Id; Write-Output \"PID:$ffmpegPid\" }"';
        exec($psCommand, $outputLines);
        pclose($handle);
        $pid = 0;
        foreach ($outputLines as $line) {
            if (preg_match('/PID:\s*(\d+)/', $line, $matches)) {
                $pid = $matches[1];
                break;
            }
        }
        return $pid;
    }

    $flusso = str_replace("%26", "&", $flusso);

    do {
        $curl = curl_init();
        curl_setopt($curl, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36');
        curl_setopt($curl, CURLOPT_URL, $flusso);
        curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($curl, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($curl, CURLOPT_SSL_VERIFYHOST, false);
        $response = curl_exec($curl);
        $curl_info = curl_getinfo($curl);
        curl_close($curl);
        if ($curl_info['http_code'] == 302) {
            $flusso = $curl_info['redirect_url'];
        }
    } while($curl_info['http_code'] == 302);

    if (!str_contains($flusso, ".m3u8") && !str_contains($flusso, ".mpd")) {
        exec("yt-dlp.exe --get-url \"" . $flusso . "\"", $nuovoFlusso);
        $flusso = $nuovoFlusso[0];
    }

    date_default_timezone_set('Europe/Rome');
    $date = date('Ymd_Gis', time());
    
    $pid = startFfmpegAndGetPid($flusso, $downloadPath . "\\" . $date . " " . $nome . ".mkv", $localPath);

    $newJson = array();

    $jsonArray = file_get_contents($localPath . "\program.json");
    $decoded_json = json_decode($jsonArray, true);
    foreach ($decoded_json as $key => $entry) {
        $newJson[$key] = $decoded_json[$key];
        if ($entry["id"] == $sequenceNumber) {
            $newJson[$key]["ffmpegPid"] = $pid;
        }
    }

    $newJsonString = json_encode($newJson);
    file_put_contents($localPath . "\program.json", $newJsonString);
?>
