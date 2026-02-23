function getBrowserCulture() {
    //returns a culture in the format "en", "fr" and "fr-FR".
    let lang = navigator.language || navigator.userLanguage || "en";
    const match = lang.match(/^[a-zA-Z]{2}(?:-[a-zA-Z]{2})?/);
    return match ? match[0] : "en";
}

function getCultureToRedirect() {
    const supportedCultures = [/*__supportedCultures__*/];//contains values like "en", "fr" and "fr-FR".
    let culture = getBrowserCulture();
    if (supportedCultures.includes(culture)) {
        window.location.replace(`/${culture}/index.html`);
    } else {
        if (0 < culture.indexOf('-')) {
            languageOnly = culture.split('-')[0];
            if (supportedCultures.includes(languageOnly)) {
                return languageOnly;
            }
        }
    }
    return "en";
}

function redirectToCulture() {
    const culture = getCultureToRedirect();
    window.location.replace(`/${culture}/index.html`);
}

redirectToCulture();