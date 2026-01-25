<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
	$nom = isset($_POST['nom']) ? trim($_POST['nom']) : '';
	$email = isset($_POST['email']) ? trim($_POST['email']) : '';
	$telephone = isset($_POST['telephone']) ? trim($_POST['telephone']) : '';
	$type_demande = isset($_POST['type_demande']) ? trim($_POST['type_demande']) : '';
	$message = isset($_POST['message']) ? trim($_POST['message']) : '';

	// Sujet automatique selon le type de demande
	$subject = ($type_demande == 'investissement') ? 'Demande d’investissement' : 'Demande d’information';

	// Sender Email and Name 
	$from = stripslashes($nom) . "<" . stripslashes($email) . ">";

	// Recipient Email Address 
	// Change the email address with yours
	$to = 'auxobetting@gmail.com';


	// Email Header 
	$headers = "From: $from\r\n" .
		"MIME-Version: 1.0\r\n";

	// Message Body 
	$body = "Demande reçue via le formulaire investisseur :\n";
	$body .= "Nom : $nom\n";
	$body .= "Email : $email\n";
	$body .= "Téléphone : $telephone\n";
	$body .= "Type de demande : $type_demande\n";
	$body .= "Message :\n$message\n";

	// Vérification des champs obligatoires
	if (empty($nom) || empty($email) || empty($type_demande) || empty($message) || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
		echo 'Veuillez remplir tous les champs obligatoires et vérifier votre email.';
		exit;
	}

	// Envoi du mail
	if (mail($to, $subject, $body, $headers)) {
		echo 'Merci ! Votre demande a bien été envoyée. Nous vous recontacterons rapidement.';
	} else {
		echo 'Erreur lors de l’envoi. Veuillez réessayer ou nous contacter directement.';
	}
}
