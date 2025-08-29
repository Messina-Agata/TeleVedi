<?php
    $sequenceNumber = $argv[1];
    $localPath = $argv[2];
    $ffmpeg = 0;
    $discard = 0;

    $programPath = $localPath . DIRECTORY_SEPARATOR . "program.json";
    $jsonArray = file_get_contents($programPath);
    $decoded_json = json_decode($jsonArray, true);
    foreach ($decoded_json as $key => $entry) {
        if ($entry["id"] == $sequenceNumber) {
            $pid = $entry["ffmpegPid"];
            $discard = $key;
            break;
        }
    }
    array_splice($decoded_json, $discard, 1);
    $newJsonString = json_encode($decoded_json);
    file_put_contents($programPath, $newJsonString);

    if ($pid !== null && is_numeric($pid) && $pid > 0) {
        if (strtoupper(substr(PHP_OS, 0, 3)) === 'WIN') {
            exec("taskkill /PID $pid /F");
        } else {
            exec("kill $pid");
        }
    }
?>
