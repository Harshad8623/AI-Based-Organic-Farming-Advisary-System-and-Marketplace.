(() => {
  const messages = {
    auth_choose_role: ['Choose Farmer or Buyer.', 'किसान या खरीदार चुनें।', 'शेतकरी किंवा खरेदीदार निवडा.'],
    auth_required: ['All fields are required.', 'सभी ज़रूरी जानकारी भरें।', 'सर्व आवश्यक माहिती भरा.'],
    auth_invalid_email: ['Please enter a valid email address.', 'सही ईमेल पता लिखें।', 'योग्य ईमेल पत्ता लिहा.'],
    auth_name_length: ['Name must be between 2 and 100 characters.', 'नाम में 2 से 100 अक्षर रखें।', 'नाव 2 ते 100 अक्षरांचे असावे.'],
    auth_password_length: ['Password must be between 8 and 128 characters.', 'पासवर्ड में 8 से 128 अक्षर रखें।', 'पासवर्ड 8 ते 128 अक्षरांचा असावा.'],
    auth_password_mismatch: ['Passwords do not match.', 'दोनों पासवर्ड एक जैसे नहीं हैं।', 'दोन्ही पासवर्ड जुळत नाहीत.'],
    auth_invalid_contact: ['Check your location and phone number.', 'अपनी जगह और फ़ोन नंबर जाँचें।', 'आपले ठिकाण आणि फोन क्रमांक तपासा.'],
    auth_email_registered: ['Email already registered. Please log in.', 'यह ईमेल पहले से दर्ज है। लॉग इन करें।', 'हा ईमेल आधीच नोंदवला आहे. लॉग इन करा.'],
    auth_registered: ['Registration successful! Please log in.', 'खाता बन गया! अब लॉग इन करें।', 'खाते तयार झाले! आता लॉग इन करा.'],
    auth_signed_in: ['You are signed in.', 'आप लॉग इन हैं।', 'तुम्ही लॉग इन केले आहे.'],
    auth_invalid_login: ['Invalid email or password.', 'ईमेल या पासवर्ड सही नहीं है।', 'ईमेल किंवा पासवर्ड चुकीचा आहे.'],
    auth_signed_out: ['You have been logged out.', 'आप लॉग आउट हो गए हैं।', 'तुम्ही लॉग आउट केले आहे.'],
    auth_denied: ['You do not have access to this action.', 'इस काम की अनुमति आपके खाते में नहीं है।', 'तुमच्या खात्याला या कृतीची परवानगी नाही.'],
    auth_login_required: ['Please log in to access this page.', 'यह पृष्ठ देखने के लिए लॉग इन करें।', 'हे पान पाहण्यासाठी लॉग इन करा.'],
    auth_session_expired: ['Your session expired. Reload this page and try again.', 'सत्र समाप्त हो गया है। पृष्ठ दोबारा खोलकर कोशिश करें।', 'सत्र संपले आहे. पान पुन्हा उघडून प्रयत्न करा.'],
    auth_check_input: ['Please check your input and try again.', 'जानकारी जाँचकर दोबारा कोशिश करें।', 'माहिती तपासून पुन्हा प्रयत्न करा.'],
    auth_not_found: ['This page or record could not be found.', 'यह पृष्ठ या नोंद नहीं मिली।', 'हे पान किंवा नोंद सापडली नाही.'],
    auth_file_large: ['This file is too large. Choose a file smaller than 16 MB.', 'फ़ाइल बहुत बड़ी है। 16 MB से छोटी फ़ाइल चुनें।', 'फाइल खूप मोठी आहे. 16 MB पेक्षा लहान फाइल निवडा.'],
    auth_server_error: ['Something went wrong. Please try again.', 'कुछ गड़बड़ हुई। दोबारा कोशिश करें।', 'काहीतरी चूक झाली. पुन्हा प्रयत्न करा.'],
    auth_soil_loamy: ['Loamy', 'दोमट', 'पोयट्याची'],
    auth_soil_clay: ['Clay', 'चिकनी', 'चिकणमाती'],
    auth_soil_sandy: ['Sandy', 'रेतीली', 'वालुकामय'],
    auth_soil_silt: ['Silt', 'गाद', 'गाळाची'],
    auth_soil_peat: ['Peat', 'पीट', 'पीट'],
    auth_soil_chalky: ['Chalky', 'चूने वाली', 'चुनखडीयुक्त']
  };
  ['en','hi','mr'].forEach((lang, index) => Object.entries(messages).forEach(([key, values]) => { TRANSLATIONS[lang][key] = values[index]; }));
  I18n.apply();
})();
