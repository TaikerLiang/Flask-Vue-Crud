let config;

console.log(process.env);

if (process.env.VUE_APP_ENV === "dev") {
  config = {
    $api_url: "http://localhost:5000",
    timeoutDuration: 30000,
  };
} else {
  config = {
    $api_url: "https://api.taiker.space",
    timeoutDuration: 1000,
  };
}

export { config }
