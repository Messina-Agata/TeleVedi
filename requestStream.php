<?php

    $flusso = $argv[1];

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

    echo $flusso;
?>
