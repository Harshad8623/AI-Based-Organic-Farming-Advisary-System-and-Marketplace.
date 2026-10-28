"""Stable message keys let validation feedback use the same offline language UI."""

MESSAGE_KEYS = {
    'Choose Farmer or Buyer.': 'auth_choose_role',
    'All fields are required.': 'auth_required',
    'Please enter a valid email address.': 'auth_invalid_email',
    'Name must be between 2 and 100 characters.': 'auth_name_length',
    'Password must be between 8 and 128 characters.': 'auth_password_length',
    'Passwords do not match.': 'auth_password_mismatch',
    'Check your location and phone number.': 'auth_invalid_contact',
    'Email already registered. Please log in.': 'auth_email_registered',
    'Registration successful! Please log in.': 'auth_registered',
    'You are signed in.': 'auth_signed_in',
    'Invalid email or password.': 'auth_invalid_login',
    'You have been logged out.': 'auth_signed_out',
    'Access denied.': 'auth_denied',
    'Please log in to access this page.': 'auth_login_required',
    'Your session expired. Reload this page and try again.': 'auth_session_expired',
    'Please check your input and try again.': 'auth_check_input',
    'You do not have access to this action.': 'auth_denied',
    'This page or record could not be found.': 'auth_not_found',
    'This file is too large. Choose a file smaller than 16 MB.': 'auth_file_large',
    'Something went wrong. Please try again.': 'auth_server_error',
}
