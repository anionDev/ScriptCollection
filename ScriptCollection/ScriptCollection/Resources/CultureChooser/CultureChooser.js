function getBrowserCulture() {
    //returns a culture in the format en or en-US
    let lang = navigator.language || navigator.userLanguage || "en";
    const match = lang.match(/^[a-zA-Z]{2}(?:-[a-zA-Z]{2})?/);
    return match ? match[0] : "en";
}

function redirectToCulture() {
    const supportedCultures = [/*__supportedCultures__*/];
    let culture = getBrowserCulture();
    if (supportedCultures.includes(culture)) {
        window.location.replace(`/${culture}/index.html`);
    } else {
        throw new Error(`Unsupported culture: "${culture}"`);
    }
}

redirectToCulture();