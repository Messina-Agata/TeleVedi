<?php

    $flusso = $argv[1];
    $nome = $argv[2];
    $downloadPath = $argv[3];
    $localPath = $argv[4];
    $sequenceNumber = $argv[5];

    $downloadPath = str_replace("/", "\\", $downloadPath);
    $localPath = str_replace("/", "\\", $localPath);

    function startFfmpegAndGetPid(string $input, string $output, $localPath): ?int {
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
        file_put_contents($localPath . "\\record.txt", $pid);
        return $pid;
    }

    if (!str_contains($flusso, ".m3u8") && !str_contains($flusso, ".mpd")) {
        exec("yt-dlp.exe --get-url \"" . $flusso . "\"", $nuovoFlusso);
        $flusso = $nuovoFlusso[0];
    }

    date_default_timezone_set('Europe/Rome');
    $date = date('Ymd_Gis', time());

    $pid = startFfmpegAndGetPid($flusso, $downloadPath . "\\" . $date . " " . $nome . ".mkv", $localPath);
        
    $newJson = array();

    $jsonArray = file_get_contents($localPath . "\\record.json");
    $decoded_json = json_decode($jsonArray, true);
    foreach ($decoded_json as $key => $entry) {
        $newJson[$key] = $decoded_json[$key];
        if ($entry["id"] == $sequenceNumber) {
            $newJson[$key]["ffmpegPid"] = $pid;
        }
    }

    $newJsonString = json_encode($newJson);
    file_put_contents($localPath . "\\record.json", $newJsonString);

?>
