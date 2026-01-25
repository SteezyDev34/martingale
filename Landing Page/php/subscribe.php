<?php

	// Fill in these three values with your own information
	$api_key = '56dd49fc31e445e1ed25ff80e27f89ab-us9';
	$datacenter = 'us9';
	$list_id = '4da4e46a7d';

	$email = $_POST['email'];
	$status = 'subscribed';
	if(!empty($_POST['status'])){
	    $status = $_POST['status'];
	}
	$url = 'https://'.$datacenter.'.api.mailchimp.com/3.0/lists/'.$list_id.'/members/';

	$username = 'apikey';
	$password = $api_key;

	$data = array("email_address" => $email,"status" => $status);
	$data_string = json_encode($data);

	$ch = curl_init();
	curl_setopt($ch, CURLOPT_URL,$url);
	curl_setopt($ch, CURLOPT_POST, 1);
	curl_setopt($ch, CURLOPT_POSTFIELDS, $data_string);
	curl_setopt($ch, CURLOPT_RETURNTRANSFER,1);
	curl_setopt($ch, CURLOPT_HTTPAUTH, CURLAUTH_BASIC);
	curl_setopt($ch, CURLOPT_USERPWD, "$username:$api_key");
	curl_setopt($ch, CURLOPT_HTTPHEADER, array(
	    'Content-Type: application/json',
	    'Content-Length: ' . strlen($data_string))
	);

	$result=curl_exec ($ch);
	curl_close ($ch);
	
	echo $result;
?>