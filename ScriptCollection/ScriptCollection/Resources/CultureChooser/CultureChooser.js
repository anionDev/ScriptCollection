function getBrowserCulture() {
    let lang = navigator.language || navigator.userLanguage || "en";
    const match = lang.match(/^[a-zA-Z]{2}(?:-[a-zA-Z]{2})?/);
    return match ? match[0] : "en";
}
function redirectToCulture() {
    if (window.location.pathname !== "/") {
        return;
    }

    const supportedCultures = [/*__supportedCultures__*/];
    let culture = getBrowserCulture();

    if (supportedCultures.includes(culture)) {
        window.location.replace(`/${culture}/`);
        return;
    }

    const baseLang = culture.split("-")[0];
    if (supportedCultures.includes(baseLang)) {
        window.location.replace(`/${baseLang}/`);
        return;
    }

    window.location.replace("/en/");
}
redirectToCulture();