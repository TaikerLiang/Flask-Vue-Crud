let config;

console.log(process.env);

if (process.env.VUE_APP_ENV === "dev") {
  config = {
    $api_url: "http://localhost",
    timeoutDuration: 30000,
  };
} else {
  config = {
    $api_url: "http://54.248.53.18",
    timeoutDuration: 1000,
  };
}

export { config }
