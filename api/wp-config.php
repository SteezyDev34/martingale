<?php
/**
 * The base configuration for WordPress
 *
 * The wp-config.php creation script uses this file during the
 * installation. You don't have to use the web site, you can
 * copy this file to "wp-config.php" and fill in the values.
 *
 * This file contains the following configurations:
 *
 * * MySQL settings
 * * Secret keys
 * * Database table prefix
 * * ABSPATH
 *
 * @link https://codex.wordpress.org/Editing_wp-config.php
 *
 * @package WordPress
 */

// ** MySQL settings - You can get this info from your web host ** //
/** The name of the database for WordPress */
define('DB_NAME', 'pcomstd757');

/** MySQL database username */
define('DB_USER', 'pcomstd757');

/** MySQL database password */
define('DB_PASSWORD', 'RgzQzGkXvsMK');

/** MySQL hostname */
define('DB_HOST', 'pcomstd757.mysql.db:3306');

/** Database Charset to use in creating database tables. */
define('DB_CHARSET', 'utf8');

/** The Database Collate type. Don't change this if in doubt. */
define('DB_COLLATE', '');

/**#@+
 * Authentication Unique Keys and Salts.
 *
 * Change these to different unique phrases!
 * You can generate these using the {@link https://api.wordpress.org/secret-key/1.1/salt/ WordPress.org secret-key service}
 * You can change these at any point in time to invalidate all existing cookies. This will force all users to have to log in again.
 *
 * @since 2.6.0
 */
define('AUTH_KEY',         'PMuWcH8v/RCSmEt3lAg1RI0sCv0LsHHL5TleL03d9ZPx+ruUjIffxkxUZ2E9');
define('SECURE_AUTH_KEY',  'RTjJJMjJdAcoYH30KbFBbxCtCNu+r8Eg8vILlkgBybob/6VyFxpN4HHBwWMX');
define('LOGGED_IN_KEY',    '5CbwGHm8bOvweGFcTXdckdG5/ZC195EzNmbUhfUQ/GfuVQJdczK4acdCeye3');
define('NONCE_KEY',        'Hj9QVTOAFoaIkOLQfve2ba85eZgAV09t/ocp+UwNx6CGqYIz+v060NQzNwMl');
define('AUTH_SALT',        'NyHXfErjHLenHqQC+vfbLuJ7t8ZN5NBZ4fo6hs+rJp3x5LfxozTRoWb92XbH');
define('SECURE_AUTH_SALT', 'qWVDOnKp7YFUARG4ZgHwvaGo8h0AMqfCXABgQfWs3WNsmKawjCTQ3fVhYrCc');
define('LOGGED_IN_SALT',   'DKfvb+VRY22TnSNjcSopWbY0wTHWqriq+LMhOKf4PztwxJ0RO0y8gUnQUrK7');
define('NONCE_SALT',       'geAr8MDkHNq9AbphOfVxvYzbaoEXSTcXd+10+os5vBHIi5NUoqVLgrBcvIVv');

/**#@-*/

/**
 * WordPress Database Table prefix.
 *
 * You can have multiple installations in one database if you give each
 * a unique prefix. Only numbers, letters, and underscores please!
 */
$table_prefix  = 'mod168_';

/**
 * For developers: WordPress debugging mode.
 *
 * Change this to true to enable the display of notices during development.
 * It is strongly recommended that plugin and theme developers use WP_DEBUG
 * in their development environments.
 *
 * For information on other constants that can be used for debugging,
 * visit the Codex.
 *
 * @link https://codex.wordpress.org/Debugging_in_WordPress
 */
define('WP_DEBUG', false);

/* That's all, stop editing! Happy blogging. */

/** Absolute path to the WordPress directory. */
if ( !defined('ABSPATH') )
	define('ABSPATH', dirname(__FILE__) . '/');

/* Fixes "Add media button not working", see http://www.carnfieldwebdesign.co.uk/blog/wordpress-fix-add-media-button-not-working/ */
define('CONCATENATE_SCRIPTS', false );

/** Sets up WordPress vars and included files. */
require_once(ABSPATH . 'wp-settings.php');
