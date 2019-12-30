let config;

console.log(process.env);

if (process.env.VUE_APP_ENV === "dev") {
  config = {
    $api_url: "http://localhost:5000",
    timeoutDuration: 3000,
  };
} else {
  config = {
    $api_url: "https://api.taiker.net",
    timeoutDuration: 1000,
  };
}

export { config }
