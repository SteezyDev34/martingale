const proxy = {
  host: "209.200.239.122",
  port: 51523,
  auth: {
    username: "auxobettingproxy",
    password: "Scorpion971"
  }
};

// Le domaine pour lequel appliquer le proxy
const targetDomain = "ultimatetennisstatistics.com";  // Remplacez par votre domaine cible

// Écouter les demandes d'authentification
chrome.webRequest.onAuthRequired.addListener(
  (details) => {
    if (details.challenger.host.includes(targetDomain)) {
      return {
        authCredentials: {
          username: proxy.auth.username,
          password: proxy.auth.password
        }
      };
    }
  },
  { urls: [`*://${targetDomain}/*`] },
  ["blocking"]
);

// Définir le proxy uniquement pour le domaine cible
chrome.proxy.settings.set(
  { value: { mode: "fixed_servers", rules: { singleProxy: { scheme: "http", host: proxy.host, port: proxy.port } } }, scope: "regular" },
  () => {
    console.log("Proxy configuré pour le domaine:", targetDomain);
  }
);
